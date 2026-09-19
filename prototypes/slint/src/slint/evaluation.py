"""Run a compiled artifact against chunks.

Order of work, cheapest first:

1. static rules run their native detector on every routed chunk;
2. feature rules read the semantic IR, extracted once per chunk and cached;
3. judge rules are batched so each chunk costs one model call carrying every judge routed to it;
4. unsupported rules are surfaced once, at their source, for a human.

Routing keeps the pair matrix sparse: a heading rule never sees a paragraph and a Python rule never
sees Markdown prose.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from slint.chunks import Chunk
from slint.detectors import DETECTORS_BY_NAME, run_detector
from slint.extraction import chunk_state, extract_features
from slint.features import ALL_FEATURES, ChunkFeatures, FeatureValue
from slint.jev import Jev, Noul, NoulAnswer
from slint.rules import (
    Artifact,
    Condition,
    FeatureEvaluator,
    JudgeEvaluator,
    Requirement,
    Severity,
    StaticEvaluator,
    UnsupportedEvaluator,
)

logger = logging.getLogger(__name__)

NOUL_TRUE_FLOOR = 0.6
NOUL_FALSE_CEILING = 0.4
SEVERITY_RANK: Mapping[Severity, int] = {"error": 0, "warning": 1, "info": 2}


@dataclass(frozen=True, kw_only=True)
class Finding:
    rule_id: str
    severity: Severity
    statement: str
    message: str
    file: str
    line: int
    end_line: int
    snippet: str
    source: str
    evaluator: str
    confidence: float


@dataclass(frozen=True, kw_only=True)
class CheckStats:
    chunks: int
    rules: int
    possible_pairs: int
    routed_pairs: int
    static_checks: int
    feature_checks: int
    chunks_extracted: int
    chunks_from_cache: int
    judge_calls: int
    judge_questions: int
    judge_rules_skipped: int
    model: str


@dataclass(frozen=True, kw_only=True)
class CheckResult:
    findings: tuple[Finding, ...]
    stats: CheckStats

    @property
    def worst_severity(self) -> Severity | None:
        if not self.findings:
            return None
        return min((f.severity for f in self.findings), key=lambda s: SEVERITY_RANK[s])


def routes_to(rule: Requirement, chunk: Chunk) -> bool:
    if rule.domain != "any" and rule.domain != chunk.domain:
        return False
    if rule.language != "any" and rule.language != chunk.language:
        return False
    match rule.scope:
        case "heading":
            return chunk.kind == "heading"
        case "opening":
            return chunk.position == "opening" and chunk.kind != "heading"
        case "closing":
            return chunk.position == "closing" and chunk.kind != "heading"
        case "list":
            return chunk.kind == "list"
        case "body":
            return chunk.kind in ("paragraph", "list") and chunk.position == "body"
        case "code":
            return chunk.domain == "code"
        case "any":
            semantic = isinstance(rule.evaluator, FeatureEvaluator | JudgeEvaluator)
            return not (semantic and chunk.kind == "heading")


def _source_anchor(rule: Requirement) -> str:
    return rule.sources[0].anchor if rule.sources else "?"


def _finding(
    rule: Requirement,
    chunk: Chunk,
    *,
    message: str,
    line: int,
    snippet: str,
    evaluator: str,
    confidence: float,
    severity: Severity | None = None,
) -> Finding:
    return Finding(
        rule_id=rule.id,
        severity=severity or rule.severity,
        statement=rule.statement,
        message=message,
        file=chunk.file,
        line=line,
        end_line=chunk.end_line if line == chunk.start_line else line,
        snippet=snippet,
        source=_source_anchor(rule),
        evaluator=evaluator,
        confidence=confidence,
    )


def evaluate_static(rule: Requirement, evaluator: StaticEvaluator, chunk: Chunk) -> list[Finding]:
    spec = DETECTORS_BY_NAME.get(evaluator.detector)
    if spec is None or not spec.applies_to(chunk):
        return []
    return [
        _finding(
            rule,
            chunk,
            message=evidence.message,
            line=evidence.line,
            snippet=evidence.snippet,
            evaluator="static",
            confidence=1.0,
        )
        for evidence in run_detector(spec, chunk, evaluator.params)
    ]


def condition_holds(condition: Condition, value: FeatureValue) -> bool:
    match condition.op, value.value:
        case "is", float() as probability:
            return probability >= NOUL_TRUE_FLOOR if condition.value else probability <= NOUL_FALSE_CEILING
        case "is_not", float() as probability:
            return probability <= NOUL_FALSE_CEILING if condition.value else probability >= NOUL_TRUE_FLOOR
        case "<", float() as number:
            return number < float(condition.value)
        case "<=", float() as number:
            return number <= float(condition.value)
        case ">", float() as number:
            return number > float(condition.value)
        case ">=", float() as number:
            return number >= float(condition.value)
        case "==", actual:
            return actual == condition.value
        case "!=", actual:
            return actual != condition.value
    return False


def describe_condition(condition: Condition, value: FeatureValue) -> str:
    spec = ALL_FEATURES.get(condition.feature)
    match value.value:
        case float() as number if spec is not None and spec.kind == "score":
            level = spec.levels[min(round(number), len(spec.levels) - 1)].split(":")[0].lower()
            return f"{condition.feature}={number:.1f} ({level})"
        case float() as number:
            return f"{condition.feature}={number:.2f}"
        case str() as option:
            return f"{condition.feature}={option}"
    return condition.feature


def evaluate_feature(
    rule: Requirement, evaluator: FeatureEvaluator, chunk: Chunk, features: ChunkFeatures
) -> list[Finding]:
    values = [features.get(condition.feature) for condition in evaluator.violated_when]
    if any(value is None for value in values):
        return []
    pairs = list(zip(evaluator.violated_when, values, strict=True))
    if not all(condition_holds(condition, value) for condition, value in pairs if value is not None):
        return []
    confidence = min(value.confidence for value in values if value is not None)
    heuristic = features.extractor == "heuristic"
    evidence = ", ".join(describe_condition(c, v) for c, v in pairs if v is not None)
    severity: Severity | None = "warning" if heuristic and rule.severity == "error" else None
    return [
        _finding(
            rule,
            chunk,
            message=evidence,
            line=chunk.start_line,
            snippet=chunk.text.splitlines()[0][:120],
            evaluator="feature/heuristic" if heuristic else "feature",
            confidence=confidence,
            severity=severity,
        )
    ]


def judge_rules(rules: Sequence[Requirement], chunk: Chunk, jev: Jev) -> list[Finding]:
    questions = {
        rule.id: Noul(
            instructions=rule.evaluator.question,
            criteria={
                "true": "The rule is violated somewhere in this unit",
                "false": "The unit complies or the rule does not apply",
            },
        )
        for rule in rules
        if isinstance(rule.evaluator, JudgeEvaluator)
    }
    answers = jev.ask(chunk_state(chunk), questions).answers
    findings: list[Finding] = []
    for rule in rules:
        answer = answers.get(rule.id)
        if not isinstance(rule.evaluator, JudgeEvaluator) or not isinstance(answer, NoulAnswer):
            continue
        if answer.noul >= rule.evaluator.threshold:
            findings.append(
                _finding(
                    rule,
                    chunk,
                    message=f"model judged a violation (p={answer.noul:.2f})",
                    line=chunk.start_line,
                    snippet=chunk.text.splitlines()[0][:120],
                    evaluator="judge",
                    confidence=answer.noul,
                )
            )
    return findings


def _unsupported_finding(rule: Requirement, reason: str, severity: Severity = "info") -> Finding:
    source = rule.sources[0]
    return Finding(
        rule_id=rule.id,
        severity=severity,
        statement=rule.statement,
        message=reason,
        file=source.file,
        line=source.line_start,
        end_line=source.line_end,
        snippet=source.text[:120],
        source=source.anchor,
        evaluator="unsupported",
        confidence=0.0,
    )


def check(
    artifact: Artifact, chunks: Sequence[Chunk], *, jev: Jev | None, cache_dir: Path | None
) -> CheckResult:
    findings: list[Finding] = []
    routed_pairs = 0
    static_checks = 0
    feature_checks = 0
    judge_calls = 0
    judge_questions = 0
    feature_chunks: dict[str, Chunk] = {}
    feature_work: list[tuple[Requirement, FeatureEvaluator, Chunk]] = []
    judge_work: dict[str, list[Requirement]] = {}

    for rule in artifact.rules:
        match rule.evaluator:
            case UnsupportedEvaluator(reason=reason):
                findings.append(_unsupported_finding(rule, f"needs human review: {reason}"))
                continue
            case _:
                pass
        for chunk in chunks:
            if not routes_to(rule, chunk):
                continue
            routed_pairs += 1
            match rule.evaluator:
                case StaticEvaluator() as evaluator:
                    static_checks += 1
                    findings.extend(evaluate_static(rule, evaluator, chunk))
                case FeatureEvaluator() as evaluator:
                    feature_chunks[chunk.id] = chunk
                    feature_work.append((rule, evaluator, chunk))
                case JudgeEvaluator():
                    judge_work.setdefault(chunk.id, []).append(rule)

    extraction = extract_features(feature_chunks.values(), jev, cache_dir)
    for rule, evaluator, chunk in feature_work:
        feature_checks += 1
        findings.extend(evaluate_feature(rule, evaluator, chunk, extraction.features[chunk.id]))

    chunks_by_id = {chunk.id: chunk for chunk in chunks}
    judge_rules_skipped = 0
    if jev is None:
        judge_rules_skipped = len({rule.id for rules in judge_work.values() for rule in rules})
    else:
        for chunk_id, rules in judge_work.items():
            judge_calls += 1
            judge_questions += len(rules)
            findings.extend(judge_rules(rules, chunks_by_id[chunk_id], jev))

    ordered = sorted(findings, key=lambda f: (f.file, f.line, SEVERITY_RANK[f.severity], f.rule_id))
    stats = CheckStats(
        chunks=len(chunks),
        rules=len(artifact.rules),
        possible_pairs=len(chunks) * len(artifact.rules),
        routed_pairs=routed_pairs,
        static_checks=static_checks,
        feature_checks=feature_checks,
        chunks_extracted=extraction.extracted,
        chunks_from_cache=extraction.cached,
        judge_calls=judge_calls,
        judge_questions=judge_questions,
        judge_rules_skipped=judge_rules_skipped,
        model=jev.model if jev is not None else "offline",
    )
    return CheckResult(findings=tuple(ordered), stats=stats)
