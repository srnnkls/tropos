"""Compile human-written guides into requirements.

Two passes. A deterministic pass finds candidate sentences with normative force (MUST, NEVER, DO,
prefer, avoid ...) and records where they came from. A classification pass then decides, for each
candidate, how the runtime will evaluate it: a native detector, a predicate over the semantic IR,
a direct judgment, or nothing. With Jev the classification is one fan-out call per candidate; the
keyword fallback lets `slint compile --offline` produce a usable artifact without a model.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from slint import __version__
from slint.chunks import Chunk, chunk_markdown
from slint.detectors import DETECTORS_BY_NAME, DetectorSpec, detectors_for
from slint.features import ALL_FEATURES, FeatureSpec, features_for
from slint.jev import Choice, ChoiceAnswer, Jev, Noul, NoulAnswer, Question
from slint.rules import (
    SEVERITY_FOR_MODALITY,
    Artifact,
    Condition,
    Evaluator,
    FeatureEvaluator,
    JudgeEvaluator,
    Modality,
    Provenance,
    Requirement,
    RuleDomain,
    Scope,
    StaticEvaluator,
    build_manifest,
    digest_sources,
)

logger = logging.getLogger(__name__)

COMPILER_VERSION = __version__
CLASSIFICATION_CONFIDENCE_FLOOR = 0.4
REQUIREMENT_PROBABILITY_FLOOR = 0.5

SKIPPED_SECTIONS = frozenset(
    {"references", "related", "supporting documentation", "quick reference", "resources", "table of contents"}
)
MUST_NOT = re.compile(
    r"\b(NEVER|MUST NOT|MUST NEVER|DON'?T|DO NOT|FORBIDDEN|NOT ALLOWED|IS ALWAYS WRONG)\b", re.I
)
MUST = re.compile(r"\b(MUST|ALWAYS|REQUIRED|ONLY|SHALL)\b")
DO = re.compile(r"^(DO|USE)\b")
SHOULD_NOT = re.compile(r"\b(should not|shouldn'?t|avoid|discouraged|rarely|don'?t)\b", re.I)
SHOULD = re.compile(
    r"\b(should|prefer|preferred|recommended|ideally|use|keep|write|put|make|spend|start|"
    r"create|define|document|name|organi[sz]e|catch|propagate|split|include|set|add|enable|"
    r"ensure|limit|lead|answer|state|cite|expand|explain|treat|check|validate|model|accept|"
    r"parse|group|extract|configure|separate|structure|return|raise|flag|trust|test)\b",
    re.I,
)
IMPERATIVE_START = re.compile(
    r"^(Use|Keep|Write|Prefer|Avoid|Put|Make|Validate|Organi[sz]e|Catch|Propagate|Split|Include|Spend|Start|"
    r"Create|Define|Document|Name|Return|Raise|Group|Set|Add|Enable|Ensure|Limit|Lead|Answer|State|Cite|Expand|"
    r"Explain|Treat|Check|Model|Accept|Parse|Extract|Configure|Separate|Structure|Flag|Trust|Test|Give|Say|"
    r"Stop|Open|Close|Bold|Reference|Let|Handle|Log|Wrap|Never|Always|Do|Don't|Only)\b"
)
LIST_MARKER = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
CODE_SPAN = re.compile(r"`[^`]*`")
LEAD_IN = re.compile(r":\s*$")
EMPHASIS = re.compile(r"(\*\*|__|(?<!\w)\*(?!\s)|(?<!\s)\*(?!\w)|(?<!\w)_(?!\s)|(?<!\s)_(?!\w))")
CHECK_MARKS = re.compile("^[\u2713\u2714\u2718\u2717\u00d7]\\s*(CORRECT|WRONG)?[:\\-]?\\s*", re.I)
PATHS_FRONT_MATTER = re.compile(r"^paths:\s*\"?([^\"\n]+)\"?", re.M)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'`(])")
KNOWN_LANGUAGES = frozenset(
    {"python", "go", "rust", "zig", "elisp", "bash", "shell", "markdown", "typescript", "javascript"}
)
LANGUAGE_FOR_GLOB: Mapping[str, str] = {
    "py": "python",
    "go": "go",
    "rs": "rust",
    "zig": "zig",
    "el": "elisp",
    "sh": "shell",
    "bash": "shell",
    "md": "markdown",
    "ts": "typescript",
    "js": "javascript",
}


@dataclass(frozen=True, kw_only=True)
class Candidate:
    statement: str
    modality: Modality
    domain: RuleDomain
    language: str
    provenance: Provenance


def guide_language(file: str, text: str) -> str:
    """Read the `paths:` front matter (as loqui uses it) into a language, else the parent directory name."""
    match = PATHS_FRONT_MATTER.search(text[:400]) if text.startswith("---") else None
    if match is not None:
        for glob in match.group(1).split(","):
            extension = glob.strip().rsplit(".", maxsplit=1)[-1]
            if extension in LANGUAGE_FOR_GLOB:
                return LANGUAGE_FOR_GLOB[extension]
    parent = Path(file).parent.name.lower()
    return parent if parent in KNOWN_LANGUAGES else "any"


def domain_for_language(language: str) -> RuleDomain:
    if language == "any":
        return "any"
    return "prose" if language == "markdown" else "code"


def normalise(sentence: str) -> str:
    text = LIST_MARKER.sub("", sentence.strip())
    spans = CODE_SPAN.findall(text)
    text = CODE_SPAN.sub("\x00", text)
    text = EMPHASIS.sub("", text)
    for span in spans:
        text = text.replace("\x00", span, 1)
    text = CHECK_MARKS.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def modality_of(sentence: str) -> Modality | None:
    starts_forbidden = LIST_MARKER.sub("", sentence.strip()).startswith(("\u2718", "\u2717", "\u00d7"))
    text = normalise(sentence)
    if not text or text.startswith(("|", "```", "!")):
        return None
    if starts_forbidden or MUST_NOT.search(text):
        return "MUST_NOT"
    if MUST.search(text) or DO.match(text):
        return "MUST"
    if SHOULD_NOT.search(text):
        return "SHOULD_NOT"
    if SHOULD.search(text) and IMPERATIVE_START.match(text):
        return "SHOULD"
    return None


def _in_skipped_section(chunk: Chunk) -> bool:
    return any(title.lower().strip() in SKIPPED_SECTIONS for title in chunk.heading_path)


def _items(chunk: Chunk) -> list[tuple[int, str]]:
    """Split a chunk into (relative_line, sentence) units: list items, or sentences of a paragraph."""
    if chunk.kind == "list":
        items: list[tuple[int, str]] = []
        for index, line in enumerate(chunk.text.splitlines()):
            if LIST_MARKER.match(line) or not items:
                items.append((index, line))
            else:
                items[-1] = (items[-1][0], items[-1][1] + " " + line.strip())
        return items
    if chunk.kind == "paragraph":
        return [(0, sentence) for sentence in SENTENCE_END.split(" ".join(chunk.text.splitlines()))]
    return []


def extract_candidates(file: str, text: str) -> list[Candidate]:
    language = guide_language(file, text)
    domain = domain_for_language(language)
    candidates: list[Candidate] = []
    for chunk in chunk_markdown(file, text):
        if _in_skipped_section(chunk):
            continue
        for relative_line, sentence in _items(chunk):
            modality = modality_of(sentence)
            statement = normalise(sentence)
            if modality is None or len(statement.split()) < 3 or LEAD_IN.search(statement):
                continue
            candidates.append(
                Candidate(
                    statement=statement,
                    modality=modality,
                    domain=domain,
                    language=language,
                    provenance=Provenance(
                        file=file,
                        heading_path=chunk.heading_path,
                        line_start=chunk.start_line + relative_line,
                        line_end=chunk.start_line + relative_line,
                        text=sentence.strip(),
                    ),
                )
            )
    return candidates


def _detector_params(spec: DetectorSpec, statement: str) -> dict[str, int | str]:
    if spec.param_pattern is None:
        return {}
    match = re.search(spec.param_pattern, statement, re.I)
    if match is None:
        return {}
    key = next(iter(spec.default_params), "value")
    return {key: int(match.group(1))}


def _domain_word(domain: RuleDomain) -> str:
    return {"code": "code", "prose": "text", "any": "code or text"}[domain]


def judge_question(candidate: Candidate) -> str:
    modality = candidate.modality.replace("_", " ")
    return (
        f"Does this {_domain_word(candidate.domain)} violate the following rule? "
        f"Rule ({modality}): {candidate.statement}"
    )


def compile_questions(candidate: Candidate) -> dict[str, Question]:
    """Every question the compiler might need about one candidate, asked in a single fan-out call."""
    domain_word = _domain_word(candidate.domain)
    questions: dict[str, Question] = {
        "is_requirement": Noul(
            instructions=(
                f"Is this sentence a concrete rule that a reviewer could check a piece of {domain_word} "
                "against, as opposed to an explanation, an example or a heading?"
            )
        ),
    }
    detector_domains = ("prose", "code") if candidate.domain == "any" else (candidate.domain,)
    detectors = [d for dom in detector_domains for d in detectors_for(dom, candidate.language or "any")]
    if candidate.language == "any":
        detectors = [
            d
            for dom in detector_domains
            for d in detectors_for(dom, "python" if dom == "code" else "markdown")
        ]
    if detectors:
        questions["detector"] = Choice(
            instructions="Which built-in check, if any, decides this rule exactly and deterministically?",
            criteria={
                **{d.name: d.description for d in detectors},
                "none": "No built-in check decides this rule",
            },
        )
    features = [f for dom in detector_domains for f in features_for(dom)]
    questions["feature"] = Choice(
        instructions=f"Which semantic property of a {domain_word} unit does this rule constrain, if any?",
        criteria={**{f.name: f.description for f in features}, "none": "None of these properties"},
    )
    for feature in features:
        if feature.kind == "choice":
            questions[f"option:{feature.name}"] = Choice(
                instructions=f"If this rule is about {feature.description}, which value does it single out?",
                criteria={**dict(feature.options or {}), "none": "The rule is not about this property"},
            )
    exemptions = [f for f in features if f.kind == "noul"]
    questions["exemption"] = Choice(
        instructions="Which property, when present, exempts a unit from this rule?",
        criteria={**{f.name: f.description for f in exemptions}, "none": "Nothing exempts a unit"},
    )
    if candidate.domain != "code":
        questions["scope"] = Choice(
            instructions="Which part of a document does this rule apply to?",
            criteria={
                "any": "Every passage",
                "heading": "Headings only",
                "opening": "The opening passage that should answer or state the point first",
                "closing": "The closing or concluding passage",
                "list": "Bulleted or numbered lists",
            },
        )
    if candidate.domain == "any":
        questions["domain"] = Choice(
            instructions="Does this rule apply to source code, to written text, or to both?",
            criteria={"code": "Source code", "prose": "Written text", "any": "Both"},
        )
    return questions


def _choice(answers: Mapping[str, object], key: str) -> ChoiceAnswer | None:
    answer = answers.get(key)
    return answer if isinstance(answer, ChoiceAnswer) else None


def classify_with_jev(candidate: Candidate, jev: Jev) -> Requirement | None:
    state = {
        "guide": candidate.provenance.file,
        "section": list(candidate.provenance.heading_path),
        "modality": candidate.modality,
        "rule": candidate.statement,
    }
    answers = jev.ask(state, compile_questions(candidate)).answers
    is_requirement = answers.get("is_requirement")
    if isinstance(is_requirement, NoulAnswer) and is_requirement.noul < REQUIREMENT_PROBABILITY_FLOOR:
        logger.debug("dropped non-requirement (p=%.2f): %s", is_requirement.noul, candidate.statement)
        return None

    domain = candidate.domain
    if (domain_answer := _choice(answers, "domain")) and domain_answer.choice in ("code", "prose", "any"):
        domain = domain_answer.choice  # type: ignore[assignment]
    scope: Scope = "any"
    if (
        scope_answer := _choice(answers, "scope")
    ) and scope_answer.confidence >= CLASSIFICATION_CONFIDENCE_FLOOR:
        scope = scope_answer.choice  # type: ignore[assignment]

    evaluator: Evaluator
    confidence: float
    detector_answer = _choice(answers, "detector")
    feature_answer = _choice(answers, "feature")
    if (
        detector_answer is not None
        and detector_answer.choice != "none"
        and detector_answer.confidence >= CLASSIFICATION_CONFIDENCE_FLOOR
        and detector_answer.choice
        in {d.name for d in detectors_for("code", "python") + detectors_for("prose", "markdown")}
    ):
        spec = DETECTORS_BY_NAME[detector_answer.choice]
        evaluator = StaticEvaluator(detector=spec.name, params=_detector_params(spec, candidate.statement))
        confidence = detector_answer.confidence
        if domain == "any":
            domain = spec.domain
    elif (
        feature_answer is not None
        and feature_answer.choice != "none"
        and feature_answer.confidence >= CLASSIFICATION_CONFIDENCE_FLOOR
        and _feature_named(feature_answer.choice) is not None
    ):
        spec = _feature_named(feature_answer.choice)
        assert spec is not None
        option_answer = _choice(answers, f"option:{spec.name}")
        option = option_answer.choice if option_answer and option_answer.choice != "none" else None
        forbids = candidate.modality in ("MUST_NOT", "SHOULD_NOT")
        conditions = spec.violation_conditions(option=option, forbids_option=forbids)
        if conditions is None:
            evaluator = JudgeEvaluator(question=judge_question(candidate))
            confidence = 0.5
        else:
            exemption = _choice(answers, "exemption")
            if (
                exemption
                and exemption.choice != "none"
                and exemption.confidence >= CLASSIFICATION_CONFIDENCE_FLOOR
            ):
                conditions = (*conditions, Condition(feature=exemption.choice, op="is", value=False))
            evaluator = FeatureEvaluator(violated_when=conditions)
            confidence = feature_answer.confidence
        if domain == "any":
            domain = spec.domain
    else:
        evaluator = JudgeEvaluator(question=judge_question(candidate))
        confidence = 0.5

    return _requirement(candidate, evaluator=evaluator, domain=domain, scope=scope, confidence=confidence)


def _feature_named(name: str) -> FeatureSpec | None:
    return ALL_FEATURES.get(name)


def _keyword_hit(keywords: Iterable[str], statement: str) -> bool:
    return _longest_keyword_hit(keywords, statement) > 0


def _longest_keyword_hit(keywords: Iterable[str], statement: str) -> int:
    """Length of the longest keyword found at a word start: `hedg` finds `hedging`, `names` not `namespacing`.

    The longest match wins between competing features, so `answer first` routes to directness rather than
    to the purpose feature's bare `answer`."""
    lowered = statement.lower()
    hits = [len(k) for k in keywords if re.search(rf"(?<![\w.]){re.escape(k.lower())}", lowered)]
    return max(hits, default=0)


SCOPE_KEYWORDS: tuple[tuple[Scope, tuple[str, ...]], ...] = (
    ("heading", ("heading", "headings", "title")),
    ("opening", ("opening", "first paragraph", "answer first", "lead with", "up front", "begin")),
    ("closing", ("conclusion", "closing", "end with", "last paragraph", "wrap up")),
    ("list", ("bullet", "list item", "lists")),
)
EXEMPTION = re.compile(r"\b(unless|except when|except if|except where)\b", re.I)


def _split_exemption(statement: str) -> tuple[str, str]:
    parts = EXEMPTION.split(statement, maxsplit=1)
    if len(parts) < 3:
        return statement, ""
    return parts[0].strip(), parts[2].strip()


def _exemption_condition(clause: str, domain: str) -> Condition | None:
    """`... unless the claim is genuinely uncertain` becomes `contains_uncertain_claim is False`."""
    if not clause:
        return None
    for spec in features_for(domain):  # type: ignore[arg-type]
        if spec.kind == "noul" and _keyword_hit(spec.keywords, clause):
            return Condition(feature=spec.name, op="is", value=False)
    return None


def classify_heuristically(candidate: Candidate) -> Requirement:
    """Keyword routing for offline compiles. Coarser than Jev, but deterministic and free."""
    domain = candidate.domain
    statement, exemption_clause = _split_exemption(candidate.statement)
    forbids = candidate.modality in ("MUST_NOT", "SHOULD_NOT")
    scope: Scope = "any"
    if domain != "code":
        for candidate_scope, keywords in SCOPE_KEYWORDS:
            if _keyword_hit(keywords, statement):
                scope = candidate_scope
                break

    domains: tuple[str, ...] = ("prose", "code") if domain == "any" else (domain,)
    detector_hits: list[tuple[int, DetectorSpec]] = []
    for dom in domains:
        language = (
            candidate.language if candidate.language != "any" else ("python" if dom == "code" else "markdown")
        )
        for spec in detectors_for(dom, language):  # type: ignore[arg-type]
            if score := _longest_keyword_hit(spec.keywords, statement):
                detector_hits.append((score, spec))
    if detector_hits:
        _, spec = max(detector_hits, key=lambda hit: hit[0])
        evaluator = StaticEvaluator(detector=spec.name, params=_detector_params(spec, statement))
        return _requirement(candidate, evaluator=evaluator, domain=spec.domain, scope=scope, confidence=0.5)

    feature_hits: list[tuple[int, FeatureSpec]] = []
    for dom in domains:
        for spec in features_for(dom):  # type: ignore[arg-type]
            if score := _longest_keyword_hit(spec.keywords, statement):
                feature_hits.append((score, spec))
    for _, spec in sorted(feature_hits, key=lambda hit: -hit[0]):
        option = None
        if spec.kind == "choice":
            option = next((o for o in (spec.options or {}) if o in statement.lower()), None)
        conditions = spec.violation_conditions(option=option, forbids_option=forbids)
        if conditions is None:
            continue
        exemption = _exemption_condition(exemption_clause, spec.domain)
        if exemption is not None:
            conditions = (*conditions, exemption)
        evaluator = FeatureEvaluator(violated_when=conditions)
        return _requirement(candidate, evaluator=evaluator, domain=spec.domain, scope=scope, confidence=0.4)
    return _requirement(
        candidate,
        evaluator=JudgeEvaluator(question=judge_question(candidate)),
        domain=domain,
        scope=scope,
        confidence=0.3,
    )


def _requirement(
    candidate: Candidate, *, evaluator: Evaluator, domain: RuleDomain, scope: Scope, confidence: float
) -> Requirement:
    return Requirement(
        id="",
        statement=candidate.statement,
        modality=candidate.modality,
        severity=SEVERITY_FOR_MODALITY[candidate.modality],
        scope=scope,
        domain=domain,
        language=candidate.language,
        evaluator=evaluator,
        sources=(candidate.provenance,),
        compiler_confidence=confidence,
    )


def merge_duplicates(rules: Iterable[Requirement]) -> list[Requirement]:
    """Rules that compile to the same check are one rule with several sources."""
    merged: dict[str, Requirement] = {}
    for rule in rules:
        key = rule.evaluator_key
        if key in merged and not isinstance(rule.evaluator, JudgeEvaluator):
            existing = merged[key]
            merged[key] = Requirement(
                id=existing.id,
                statement=existing.statement,
                modality=existing.modality,
                severity=existing.severity,
                scope=existing.scope,
                domain=existing.domain,
                language=existing.language if existing.language == rule.language else "any",
                evaluator=existing.evaluator,
                sources=(*existing.sources, *rule.sources),
                compiler_confidence=max(existing.compiler_confidence, rule.compiler_confidence),
            )
        else:
            merged.setdefault(
                key + rule.statement if isinstance(rule.evaluator, JudgeEvaluator) else key, rule
            )
    return list(merged.values())


def assign_ids(rules: Iterable[Requirement], prefix: str) -> tuple[Requirement, ...]:
    ordered = sorted(rules, key=lambda r: (r.sources[0].file, r.sources[0].line_start))
    return tuple(
        Requirement(
            id=f"{prefix}-{index:03d}",
            statement=rule.statement,
            modality=rule.modality,
            severity=rule.severity,
            scope=rule.scope,
            domain=rule.domain,
            language=rule.language,
            evaluator=rule.evaluator,
            sources=rule.sources,
            compiler_confidence=rule.compiler_confidence,
        )
        for index, rule in enumerate(ordered, start=1)
    )


def compile_guides(paths: Iterable[Path], *, jev: Jev | None, prefix: str = "RULE") -> Artifact:
    files = [path for path in paths if path.is_file()]
    candidates = [
        c for path in files for c in extract_candidates(str(path), path.read_text(encoding="utf-8"))
    ]
    classified: list[Requirement] = []
    for candidate in candidates:
        rule = classify_with_jev(candidate, jev) if jev is not None else classify_heuristically(candidate)
        if rule is not None:
            classified.append(rule)
    rules = assign_ids(merge_duplicates(classified), prefix)
    manifest = build_manifest(
        compiler_version=COMPILER_VERSION,
        model=jev.model if jev is not None else "heuristic",
        sources=digest_sources(files),
        rules=rules,
    )
    return Artifact(manifest=manifest, rules=rules)
