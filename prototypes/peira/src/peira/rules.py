"""The compiled artifact: normative requirements with provenance, routing metadata and an evaluator.

A requirement is evaluated by exactly one of four strategies, cheapest first:

    static      a native detector decides it deterministically
    feature     a predicate over the semantic IR decides it, no model call at check time
    judge       Jev is asked directly, once per routed chunk, batched with the chunk's other judges
    unsupported the rule is recorded and surfaced for human review
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from peira.errors import ArtifactError

ARTIFACT_FORMAT_VERSION = "1"
FEATURE_SCHEMA_VERSION = "1"
RULES_FILE = "rules.json"
MANIFEST_FILE = "manifest.json"

type Modality = Literal["MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT"]
type Severity = Literal["error", "warning", "info"]
type Scope = Literal["any", "heading", "opening", "closing", "body", "list", "code"]
type RuleDomain = Literal["prose", "code", "any"]
type Comparison = Literal["<", "<=", ">", ">=", "==", "!=", "is", "is_not"]

SEVERITY_FOR_MODALITY: Mapping[Modality, Severity] = {
    "MUST": "error",
    "MUST_NOT": "error",
    "SHOULD": "warning",
    "SHOULD_NOT": "warning",
}


@dataclass(frozen=True, kw_only=True)
class Provenance:
    file: str
    heading_path: tuple[str, ...]
    line_start: int
    line_end: int
    text: str

    @property
    def anchor(self) -> str:
        section = f" §{' > '.join(self.heading_path)}" if self.heading_path else ""
        return f"{self.file}:{self.line_start}{section}"


@dataclass(frozen=True, kw_only=True)
class StaticEvaluator:
    kind: Literal["static"] = "static"
    detector: str
    params: Mapping[str, int | str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class Condition:
    """A violation condition over one feature; `value` is compared with the extracted feature value."""

    feature: str
    op: Comparison
    value: float | str | bool


@dataclass(frozen=True, kw_only=True)
class FeatureEvaluator:
    kind: Literal["feature"] = "feature"
    violated_when: tuple[Condition, ...]


@dataclass(frozen=True, kw_only=True)
class JudgeEvaluator:
    kind: Literal["judge"] = "judge"
    question: str
    threshold: float = 0.6


@dataclass(frozen=True, kw_only=True)
class UnsupportedEvaluator:
    kind: Literal["unsupported"] = "unsupported"
    reason: str


type Evaluator = StaticEvaluator | FeatureEvaluator | JudgeEvaluator | UnsupportedEvaluator


@dataclass(frozen=True, kw_only=True)
class Requirement:
    id: str
    statement: str
    modality: Modality
    severity: Severity
    scope: Scope
    domain: RuleDomain
    language: str
    evaluator: Evaluator
    sources: tuple[Provenance, ...]
    compiler_confidence: float

    @property
    def evaluator_key(self) -> str:
        """Rules with the same key are the same check and are merged at compile time."""
        return json.dumps({"e": asdict(self.evaluator), "d": self.domain, "s": self.scope}, sort_keys=True)


@dataclass(frozen=True, kw_only=True)
class SourceDigest:
    path: str
    sha256: str


@dataclass(frozen=True, kw_only=True)
class Manifest:
    format_version: str = ARTIFACT_FORMAT_VERSION
    compiler_version: str
    feature_schema_version: str = FEATURE_SCHEMA_VERSION
    model: str
    created_at: str
    sources: tuple[SourceDigest, ...]
    rule_count: int
    evaluator_counts: Mapping[str, int]


@dataclass(frozen=True, kw_only=True)
class Artifact:
    manifest: Manifest
    rules: tuple[Requirement, ...]


def digest_sources(paths: Iterable[Path]) -> tuple[SourceDigest, ...]:
    return tuple(
        SourceDigest(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        for path in sorted(paths)
    )


def build_manifest(
    *, compiler_version: str, model: str, sources: tuple[SourceDigest, ...], rules: tuple[Requirement, ...]
) -> Manifest:
    counts: dict[str, int] = {}
    for rule in rules:
        counts[rule.evaluator.kind] = counts.get(rule.evaluator.kind, 0) + 1
    return Manifest(
        compiler_version=compiler_version,
        model=model,
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        sources=sources,
        rule_count=len(rules),
        evaluator_counts=counts,
    )


def save_artifact(artifact: Artifact, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / RULES_FILE).write_text(
        json.dumps([asdict(rule) for rule in artifact.rules], indent=2, ensure_ascii=False) + "\n"
    )
    (directory / MANIFEST_FILE).write_text(json.dumps(asdict(artifact.manifest), indent=2) + "\n")


def load_artifact(directory: Path) -> Artifact:
    rules_path = directory / RULES_FILE
    manifest_path = directory / MANIFEST_FILE
    if not rules_path.exists() or not manifest_path.exists():
        raise ArtifactError(f"no compiled artifact in {directory} (run `peira compile` first)")
    try:
        manifest = parse_manifest(json.loads(manifest_path.read_text()))
        rules = tuple(parse_requirement(raw) for raw in json.loads(rules_path.read_text()))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        raise ArtifactError(f"corrupt artifact in {directory}: {error}") from error
    if manifest.format_version != ARTIFACT_FORMAT_VERSION:
        raise ArtifactError(
            f"artifact format {manifest.format_version} is not supported by this runtime "
            f"({ARTIFACT_FORMAT_VERSION})"
        )
    if manifest.feature_schema_version != FEATURE_SCHEMA_VERSION:
        raise ArtifactError(
            f"artifact was compiled against feature schema {manifest.feature_schema_version}; "
            f"this runtime speaks {FEATURE_SCHEMA_VERSION}. Recompile."
        )
    return Artifact(manifest=manifest, rules=rules)


def parse_manifest(raw: Mapping[str, Any]) -> Manifest:
    return Manifest(
        format_version=str(raw.get("format_version", "0")),
        compiler_version=str(raw["compiler_version"]),
        feature_schema_version=str(raw.get("feature_schema_version", "0")),
        model=str(raw["model"]),
        created_at=str(raw["created_at"]),
        sources=tuple(SourceDigest(path=s["path"], sha256=s["sha256"]) for s in raw.get("sources", [])),
        rule_count=int(raw["rule_count"]),
        evaluator_counts={str(k): int(v) for k, v in raw.get("evaluator_counts", {}).items()},
    )


def parse_requirement(raw: Mapping[str, Any]) -> Requirement:
    return Requirement(
        id=str(raw["id"]),
        statement=str(raw["statement"]),
        modality=_literal(raw["modality"], ("MUST", "MUST_NOT", "SHOULD", "SHOULD_NOT")),
        severity=_literal(raw["severity"], ("error", "warning", "info")),
        scope=_literal(raw["scope"], ("any", "heading", "opening", "closing", "body", "list", "code")),
        domain=_literal(raw["domain"], ("prose", "code", "any")),
        language=str(raw["language"]),
        evaluator=parse_evaluator(raw["evaluator"]),
        sources=tuple(
            Provenance(
                file=s["file"],
                heading_path=tuple(s.get("heading_path", ())),
                line_start=int(s["line_start"]),
                line_end=int(s["line_end"]),
                text=s["text"],
            )
            for s in raw["sources"]
        ),
        compiler_confidence=float(raw.get("compiler_confidence", 1.0)),
    )


def parse_evaluator(raw: Mapping[str, Any]) -> Evaluator:
    match raw:
        case {"kind": "static", "detector": str() as detector}:
            return StaticEvaluator(detector=detector, params=dict(raw.get("params") or {}))
        case {"kind": "feature", "violated_when": list() as conditions}:
            return FeatureEvaluator(
                violated_when=tuple(
                    Condition(
                        feature=str(c["feature"]),
                        op=_literal(c["op"], ("<", "<=", ">", ">=", "==", "!=", "is", "is_not")),
                        value=c["value"],
                    )
                    for c in conditions
                )
            )
        case {"kind": "judge", "question": str() as question}:
            return JudgeEvaluator(question=question, threshold=float(raw.get("threshold", 0.6)))
        case {"kind": "unsupported", "reason": str() as reason}:
            return UnsupportedEvaluator(reason=reason)
    raise ValueError(f"unknown evaluator: {raw}")


def _literal[T: str](value: object, allowed: tuple[T, ...]) -> T:
    for candidate in allowed:
        if value == candidate:
            return candidate
    raise ValueError(f"{value!r} is not one of {allowed}")
