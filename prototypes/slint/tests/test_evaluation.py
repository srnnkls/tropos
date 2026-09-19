from __future__ import annotations

from pathlib import Path

from slint.chunks import chunk_text
from slint.compiler import compile_guides
from slint.evaluation import check, condition_holds, routes_to
from slint.features import FeatureValue
from slint.jev import RecordingJev, ScriptedJev
from slint.rules import (
    Artifact,
    Condition,
    Evaluator,
    JudgeEvaluator,
    Manifest,
    Provenance,
    Requirement,
    RuleDomain,
    Scope,
    Severity,
    StaticEvaluator,
    UnsupportedEvaluator,
)


def _rule(
    rule_id: str,
    evaluator: Evaluator,
    *,
    scope: Scope = "any",
    domain: RuleDomain = "prose",
    language: str = "any",
    severity: Severity = "error",
) -> Requirement:
    return Requirement(
        id=rule_id,
        statement=f"rule {rule_id}",
        modality="MUST",
        severity=severity,
        scope=scope,
        domain=domain,
        language=language,
        evaluator=evaluator,
        compiler_confidence=1.0,
        sources=(Provenance(file="g.md", heading_path=(), line_start=1, line_end=1, text="rule"),),
    )


def _artifact(*rules: Requirement) -> Artifact:
    manifest = Manifest(
        compiler_version="t",
        model="t",
        created_at="now",
        sources=(),
        rule_count=len(rules),
        evaluator_counts={},
    )
    return Artifact(manifest=manifest, rules=tuple(rules))


DOC = "# Title\n\nOpening words here.\n\nMiddle words here.\n\n- a list\n\nClosing words here.\n"


def test_routing_is_sparse_by_scope_domain_and_language():
    chunks = chunk_text("d.md", DOC)
    heading_rule = _rule("H", StaticEvaluator(detector="heading_not_sentence_case"), scope="heading")
    opening_rule = _rule("O", JudgeEvaluator(question="?"), scope="opening")
    python_rule = _rule("P", StaticEvaluator(detector="staticmethod"), domain="code", language="python")
    judge_rule = _rule("J", JudgeEvaluator(question="?"))

    routed = {
        rule.id: [c.kind for c in chunks if routes_to(rule, c)]
        for rule in (heading_rule, opening_rule, python_rule, judge_rule)
    }

    assert routed == {
        "H": ["heading"],
        "O": ["paragraph"],
        "P": [],
        "J": ["paragraph", "paragraph", "list", "paragraph"],
    }


def test_judge_rules_are_batched_into_one_call_per_chunk():
    chunks = chunk_text("d.md", DOC)
    rules = [_rule(f"J{i}", JudgeEvaluator(question=f"q{i}")) for i in range(5)]
    jev = RecordingJev(inner=ScriptedJev(script={"J2": {"type": "noul", "noul": 0.9}}))

    result = check(_artifact(*rules), chunks, jev=jev, cache_dir=None)

    prose_chunks = [c for c in chunks if c.kind != "heading"]
    assert jev.calls == len(prose_chunks)
    assert jev.questions_asked == 5 * len(prose_chunks)
    assert result.stats.possible_pairs == 5 * len(chunks)
    assert {f.rule_id for f in result.findings} == {"J2"}
    assert all(f.evaluator == "judge" for f in result.findings)


def test_judge_rules_are_skipped_offline_and_counted():
    chunks = chunk_text("d.md", DOC)

    result = check(_artifact(_rule("J", JudgeEvaluator(question="?"))), chunks, jev=None, cache_dir=None)

    assert result.findings == ()
    assert result.stats.judge_rules_skipped == 1


def test_unsupported_rules_surface_once_at_their_source():
    result = check(
        _artifact(_rule("U", UnsupportedEvaluator(reason="too vague"))),
        chunk_text("d.md", DOC),
        jev=None,
        cache_dir=None,
    )

    assert len(result.findings) == 1
    assert result.findings[0].file == "g.md"
    assert result.findings[0].severity == "info"


def test_noul_conditions_ignore_uncertain_values():
    condition = Condition(feature="uses_jargon", op="is", value=True)

    assert condition_holds(condition, FeatureValue(value=0.9, confidence=0.8, probabilities={}))
    assert not condition_holds(condition, FeatureValue(value=0.5, confidence=0.0, probabilities={}))
    assert not condition_holds(condition, FeatureValue(value=0.1, confidence=0.8, probabilities={}))


def test_heuristic_feature_findings_are_downgraded_to_warnings(writing_guide: Path, status_update: Path):
    artifact = compile_guides([writing_guide], jev=None, prefix="EX")

    result = check(
        artifact, chunk_text(str(status_update), status_update.read_text()), jev=None, cache_dir=None
    )

    heuristic = [f for f in result.findings if f.evaluator == "feature/heuristic"]
    assert heuristic
    assert all(f.severity == "warning" for f in heuristic)


def test_static_findings_carry_evidence_and_provenance(networking_spec: Path, client_source: Path):
    artifact = compile_guides([networking_spec], jev=None, prefix="NET")

    result = check(
        artifact, chunk_text(str(client_source), client_source.read_text()), jev=None, cache_dir=None
    )

    timeout = next(f for f in result.findings if "timeout" in f.message)
    assert timeout.line == 28
    assert timeout.snippet.startswith("response = requests.get(")
    assert (
        timeout.source.startswith("examples/guides/networking-spec.md:11")
        or "networking-spec.md:11" in timeout.source
    )
    assert timeout.evaluator == "static"
