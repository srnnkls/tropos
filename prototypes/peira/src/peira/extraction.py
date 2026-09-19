"""Build the semantic IR: one feature vector per chunk, cached by content.

With Jev, extraction is one call per chunk carrying the whole feature vocabulary for the chunk's
domain (speculative fan-out). Offline, a keyword heuristic produces a rougher vector so the rest
of the pipeline still runs; findings derived from it are labelled as heuristic.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

from peira.chunks import Chunk
from peira.features import (
    FEATURE_SCHEMA_VERSION,
    ChunkFeatures,
    FeatureSpec,
    FeatureValue,
    features_for,
)
from peira.jev import ChoiceAnswer, Jev, JsonValue, NoulAnswer, ScoreAnswer

logger = logging.getLogger(__name__)

HEURISTIC_MODEL = "heuristic"


def cache_key(chunk: Chunk, model: str) -> str:
    material = f"{FEATURE_SCHEMA_VERSION}\n{model}\n{chunk.domain}\n{chunk.kind}\n{chunk.text}"
    return hashlib.sha256(material.encode()).hexdigest()


def read_cached(cache_dir: Path | None, key: str) -> ChunkFeatures | None:
    if cache_dir is None:
        return None
    path = cache_dir / f"{key}.json"
    if not path.exists():
        return None
    try:
        return parse_chunk_features(json.loads(path.read_text()))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.warning("discarding unreadable feature cache entry %s", path.name)
        return None


def write_cached(cache_dir: Path | None, key: str, features: ChunkFeatures) -> None:
    if cache_dir is None:
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / f"{key}.json").write_text(json.dumps(asdict(features)))


def parse_chunk_features(raw: Mapping[str, object]) -> ChunkFeatures:
    values_raw = raw["values"]
    if not isinstance(values_raw, Mapping):
        raise ValueError("values must be an object")
    values: dict[str, FeatureValue] = {}
    for name, item in values_raw.items():
        if not isinstance(item, Mapping):
            raise ValueError(f"feature {name} must be an object")
        probabilities = item.get("probabilities") or {}
        if not isinstance(probabilities, Mapping):
            raise ValueError(f"feature {name} has malformed probabilities")
        value = item["value"]
        if not isinstance(value, str | int | float):
            raise ValueError(f"feature {name} has malformed value")
        values[str(name)] = FeatureValue(
            value=value if isinstance(value, str) else float(value),
            confidence=float(item.get("confidence", 0.0)),  # type: ignore[arg-type]
            probabilities={str(k): float(v) for k, v in probabilities.items()},  # type: ignore[arg-type]
        )
    extractor = raw["extractor"]
    domain = raw["domain"]
    if extractor not in ("jev", "heuristic") or domain not in ("prose", "code"):
        raise ValueError("unknown extractor or domain")
    return ChunkFeatures(
        chunk_id=str(raw["chunk_id"]),
        domain=domain,
        extractor=extractor,
        model=str(raw.get("model", "")),
        schema_version=str(raw.get("schema_version", "0")),
        values=values,
    )


def chunk_state(chunk: Chunk) -> dict[str, JsonValue]:
    """What Jev sees: the chunk plus just enough context to judge it as part of a document."""
    return {
        "kind": chunk.kind,
        "language": chunk.language,
        "position_in_document": chunk.position,
        "section": list(chunk.heading_path),
        "text": chunk.text,
    }


def extract_with_jev(chunk: Chunk, jev: Jev) -> ChunkFeatures:
    specs = features_for(chunk.domain)
    response = jev.ask(chunk_state(chunk), {spec.name: spec.question() for spec in specs})
    values: dict[str, FeatureValue] = {}
    for spec in specs:
        answer = response.answers.get(spec.name)
        match answer:
            case NoulAnswer(noul=noul):
                values[spec.name] = FeatureValue(value=noul, confidence=abs(noul - 0.5) * 2, probabilities={})
            case ChoiceAnswer(choice=choice, confidence=confidence, probabilities=probabilities):
                values[spec.name] = FeatureValue(
                    value=choice, confidence=confidence, probabilities=probabilities
                )
            case ScoreAnswer(score=score, confidence=confidence, probabilities=probabilities):
                values[spec.name] = FeatureValue(
                    value=score, confidence=confidence, probabilities=probabilities
                )
            case None:
                logger.warning("Jev returned no answer for feature %s", spec.name)
    return ChunkFeatures(
        chunk_id=chunk.id, domain=chunk.domain, extractor="jev", model=response.model, values=values
    )


HEDGES = re.compile(
    r"\b(maybe|perhaps|possibly|arguably|somewhat|it seems|seems to|might|may|could|likely|probably|"
    r"in some cases|to some extent|generally|typically|often|sort of|kind of|i think|we believe)\b",
    re.IGNORECASE,
)
FILLER = re.compile(
    r"\b(in order to|it is important to note|it should be noted|basically|actually|really|very|quite|"
    r"as a matter of fact|at the end of the day|needless to say|in other words|that being said)\b",
    re.IGNORECASE,
)
PASSIVE = re.compile(r"\b(is|are|was|were|be|been|being)\s+(\w+ed|\w+en)\b", re.IGNORECASE)
ACRONYM = re.compile(r"\b[A-Z]{3,}\b")
UNCERTAIN_MARKERS = re.compile(
    r"\b(unknown|unclear|uncertain|not yet|debated|contested|depends|estimate)", re.IGNORECASE
)
NETWORK = re.compile(r"\b(requests|httpx|urlopen|socket|aiohttp|grpc)\b")
TIMEOUT = re.compile(r"\btimeout\s*=")
SWALLOW = re.compile(r"except[^\n]*:\s*\n\s*pass\b")
GLOBAL_MUTATION = re.compile(r"^\s*global\s+\w+", re.MULTILINE)
SECRET_LOG = re.compile(r"(print|log\w*\.\w+)\([^)]*(password|secret|token|api_key|apikey)", re.IGNORECASE)


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _score(level: float, spec: FeatureSpec) -> FeatureValue:
    clamped = max(0.0, min(float(len(spec.levels) - 1), level))
    return FeatureValue(value=clamped, confidence=0.4, probabilities={})


def _noul(probability: float) -> FeatureValue:
    return FeatureValue(value=probability, confidence=0.4, probabilities={})


def _choice(option: str, spec: FeatureSpec) -> FeatureValue:
    options = list(spec.options or {})
    return FeatureValue(
        value=option, confidence=0.3, probabilities=dict.fromkeys(options, 1.0 / max(len(options), 1))
    )


def extract_heuristically(chunk: Chunk) -> ChunkFeatures:
    """A deliberately rough approximation of the IR that needs no model. Treat its output as a hint."""
    specs = {spec.name: spec for spec in features_for(chunk.domain)}
    values: dict[str, FeatureValue] = {}
    text = chunk.text
    words = max(len(re.findall(r"\w+", text)), 1)
    if chunk.domain == "prose":
        sentences = _sentences(text)
        hedge_density = len(HEDGES.findall(text)) / words * 100
        filler_density = len(FILLER.findall(text)) / words * 100
        average_sentence = words / max(len(sentences), 1)
        passive_share = len(PASSIVE.findall(text)) / max(len(sentences), 1)
        distinct = {re.sub(r"\W+", " ", s.lower()).strip() for s in sentences}
        values["hedging"] = _score(hedge_density / 2.5, specs["hedging"])
        values["verbosity"] = _score(
            filler_density / 1.5 + max(average_sentence - 20, 0) / 15, specs["verbosity"]
        )
        values["directness"] = _score(
            3 - min(len(sentences) - 1, 3) * 0.5 if chunk.position == "opening" else 2, specs["directness"]
        )
        values["passive_voice_heavy"] = _noul(min(passive_share, 1.0))
        values["uses_jargon"] = _noul(min(len(set(ACRONYM.findall(text))) / 3, 1.0))
        values["contains_repetition"] = _noul(0.8 if len(distinct) < len(sentences) else 0.1)
        values["contains_uncertain_claim"] = _noul(0.7 if UNCERTAIN_MARKERS.search(text) else 0.2)
        values["contains_unsupported_claim"] = _noul(0.5)
        values["tone"] = _choice("promotional" if text.count("!") >= 2 else "neutral", specs["tone"])
        values["purpose"] = _choice(
            {"opening": "answer", "closing": "summary"}.get(chunk.position, "context"), specs["purpose"]
        )
        values["audience_level"] = _choice("practitioner", specs["audience_level"])
    else:
        network = bool(NETWORK.search(text))
        values["makes_network_call"] = _noul(0.9 if network else 0.1)
        values["sets_explicit_timeout"] = _noul(0.9 if TIMEOUT.search(text) else 0.1)
        values["swallows_errors"] = _noul(0.9 if SWALLOW.search(text) else 0.1)
        values["mutates_global_state"] = _noul(0.9 if GLOBAL_MUTATION.search(text) else 0.1)
        values["logs_sensitive_data"] = _noul(0.9 if SECRET_LOG.search(text) else 0.1)
        values["code_purpose"] = _choice("network" if network else "other", specs["code_purpose"])
        for name in (
            "rewraps_without_context",
            "comments_restate_code",
            "class_is_namespace",
            "untyped_data_in_core",
            "duplicates_dependency_validation",
        ):
            values[name] = _noul(0.5)
        values["names_are_descriptive"] = _noul(0.5)
    return ChunkFeatures(
        chunk_id=chunk.id, domain=chunk.domain, extractor="heuristic", model=HEURISTIC_MODEL, values=values
    )


@dataclass(frozen=True, kw_only=True)
class Extraction:
    features: Mapping[str, ChunkFeatures]
    extracted: int
    cached: int


def extract_features(chunks: Iterable[Chunk], jev: Jev | None, cache_dir: Path | None = None) -> Extraction:
    """Return the IR for every chunk, extracting only what the cache does not already hold."""
    model = jev.model if jev is not None else HEURISTIC_MODEL
    features: dict[str, ChunkFeatures] = {}
    extracted = 0
    cached_count = 0
    for chunk in chunks:
        key = cache_key(chunk, model)
        cached = read_cached(cache_dir, key)
        if cached is not None and cached.schema_version == FEATURE_SCHEMA_VERSION:
            features[chunk.id] = cached
            cached_count += 1
            continue
        fresh = extract_with_jev(chunk, jev) if jev is not None else extract_heuristically(chunk)
        write_cached(cache_dir, key, fresh)
        features[chunk.id] = fresh
        extracted += 1
    return Extraction(features=features, extracted=extracted, cached=cached_count)
