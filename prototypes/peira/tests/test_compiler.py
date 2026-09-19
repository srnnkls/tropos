from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from peira.compiler import (
    Candidate,
    classify_heuristically,
    classify_with_jev,
    compile_guides,
    extract_candidates,
    guide_language,
    merge_duplicates,
    modality_of,
    normalise,
)
from peira.jev import RecordingJev, ScriptedJev
from peira.rules import FeatureEvaluator, JudgeEvaluator, Provenance, StaticEvaluator


@dataclass(frozen=True)
class ModalityCase:
    sentence: str
    expected: str | None
    description: str


MODALITY_CASES = [
    ModalityCase("Outbound requests MUST configure a timeout.", "MUST", "must"),
    ModalityCase("- **NEVER** use `@staticmethod`", "MUST_NOT", "never bullet"),
    ModalityCase("- ✘ Behavioral inheritance (except exceptions)", "MUST_NOT", "cross mark"),
    ModalityCase("Prefer the active voice.", "SHOULD", "prefer"),
    ModalityCase("Avoid exclamation marks.", "SHOULD_NOT", "avoid"),
    ModalityCase("The root gives us eloquence and soliloquy.", None, "descriptive sentence"),
    ModalityCase("| Tool | Purpose |", None, "table row"),
]


@pytest.mark.parametrize("case", MODALITY_CASES, ids=lambda c: c.description)
def test_modality_detection(case: ModalityCase):
    assert modality_of(case.sentence) == case.expected


def test_normalise_strips_emphasis_but_keeps_code_spans():
    assert normalise("- **DO** use `__all__` in `__init__.py`") == "DO use `__all__` in `__init__.py`"


def test_guide_language_reads_loqui_front_matter():
    assert guide_language("x.md", '---\npaths: "**/*.py, **/pyproject.toml"\n---\n# T\n') == "python"


def test_guide_language_falls_back_to_parent_directory_name():
    assert guide_language("languages/python/README.md", "# Python\n") == "python"
    assert guide_language("docs/README.md", "# Docs\n") == "any"


GUIDE = """# Guide

Just an introduction, nothing normative.

## Rules

- Headings MUST be in sentence case.
- Use pattern matching when:
- NEVER use em dashes.

```python
# ✘ WRONG: this MUST NOT be picked up
```

## References

- You MUST ignore this section.
"""


def test_extract_candidates_keeps_normative_sentences_with_provenance(tmp_path: Path):
    candidates = extract_candidates("guide.md", GUIDE)

    assert [c.statement for c in candidates] == ["Headings MUST be in sentence case.", "NEVER use em dashes."]
    assert candidates[0].provenance.line_start == 7
    assert candidates[0].provenance.heading_path == ("Guide", "Rules")


def _candidate(statement: str, modality: str = "MUST", language: str = "any") -> Candidate:
    domain = "any" if language == "any" else ("code" if language == "python" else "prose")
    return Candidate(
        statement=statement,
        modality=modality,  # type: ignore[arg-type]
        domain=domain,  # type: ignore[arg-type]
        language=language,
        provenance=Provenance(file="g.md", heading_path=("G",), line_start=1, line_end=1, text=statement),
    )


def test_heuristic_routes_timeout_rule_to_static_detector():
    rule = classify_heuristically(
        _candidate("Outbound HTTP requests MUST configure an explicit timeout.", "MUST", "python")
    )

    assert rule.evaluator == StaticEvaluator(detector="network_call_without_timeout")
    assert rule.severity == "error"


def test_heuristic_reads_numeric_parameter_from_rule_text():
    rule = classify_heuristically(_candidate("Keep sentences under 25 words.", "SHOULD"))

    assert rule.evaluator == StaticEvaluator(detector="long_sentence", params={"max_words": 25})


def test_heuristic_hedging_rule_with_exemption_becomes_compound_predicate():
    rule = classify_heuristically(
        _candidate("Do not hedge. State things plainly unless the claim is genuinely uncertain.", "MUST_NOT")
    )

    assert isinstance(rule.evaluator, FeatureEvaluator)
    assert [(c.feature, c.op, c.value) for c in rule.evaluator.violated_when] == [
        ("hedging", ">", 1.5),
        ("contains_uncertain_claim", "is", False),
    ]


def test_heuristic_polarity_ignores_modality_for_good_and_bad_features():
    be_direct = classify_heuristically(_candidate("Be direct and answer first.", "MUST"))
    no_hedging = classify_heuristically(_candidate("Do not hedge.", "MUST_NOT"))

    assert isinstance(be_direct.evaluator, FeatureEvaluator)
    assert be_direct.evaluator.violated_when[0].op == "<"
    assert isinstance(no_hedging.evaluator, FeatureEvaluator)
    assert no_hedging.evaluator.violated_when[0].op == ">"


def test_heuristic_choice_feature_uses_modality_for_the_option():
    rule = classify_heuristically(_candidate("The tone MUST NOT be promotional.", "MUST_NOT"))

    assert isinstance(rule.evaluator, FeatureEvaluator)
    assert rule.evaluator.violated_when[0].op == "=="
    assert rule.evaluator.violated_when[0].value == "promotional"


def test_heuristic_falls_back_to_judge():
    rule = classify_heuristically(
        _candidate("Dependencies MUST flow toward the domain core.", "MUST", "python")
    )

    assert isinstance(rule.evaluator, JudgeEvaluator)
    assert "Rule (MUST)" in rule.evaluator.question


def test_jev_classification_asks_one_fan_out_call_per_candidate():
    jev = RecordingJev(
        inner=ScriptedJev(
            script={
                "is_requirement": {"type": "noul", "noul": 0.9},
                "detector": {"type": "choice", "choice": "none", "confidence": 0.9, "probabilities": {}},
                "feature": {"type": "choice", "choice": "hedging", "confidence": 0.8, "probabilities": {}},
                "exemption": {
                    "type": "choice",
                    "choice": "contains_uncertain_claim",
                    "confidence": 0.7,
                    "probabilities": {},
                },
                "scope": {"type": "choice", "choice": "any", "confidence": 0.9, "probabilities": {}},
                "domain": {"type": "choice", "choice": "prose", "confidence": 0.9, "probabilities": {}},
            }
        )
    )

    rule = classify_with_jev(_candidate("Do not hedge unless genuinely uncertain."), jev)

    assert jev.calls == 1
    assert rule is not None
    assert rule.domain == "prose"
    assert isinstance(rule.evaluator, FeatureEvaluator)
    assert {c.feature for c in rule.evaluator.violated_when} == {"hedging", "contains_uncertain_claim"}
    assert rule.compiler_confidence == 0.8


def test_jev_classification_drops_non_requirements():
    jev = ScriptedJev(script={"is_requirement": {"type": "noul", "noul": 0.1}})

    assert classify_with_jev(_candidate("Python has namespaces: modules."), jev) is None


def test_jev_classification_prefers_static_detector_over_feature():
    jev = ScriptedJev(
        script={
            "is_requirement": {"type": "noul", "noul": 0.95},
            "detector": {"type": "choice", "choice": "staticmethod", "confidence": 0.95, "probabilities": {}},
            "feature": {
                "type": "choice",
                "choice": "class_is_namespace",
                "confidence": 0.9,
                "probabilities": {},
            },
        }
    )

    rule = classify_with_jev(_candidate("NEVER use @staticmethod.", "MUST_NOT", "python"), jev)

    assert rule is not None
    assert rule.evaluator == StaticEvaluator(detector="staticmethod")


def test_merge_duplicates_unions_sources_and_widens_language():
    readme = classify_heuristically(_candidate("NEVER use @staticmethod.", "MUST_NOT", "any"))
    topic = classify_heuristically(_candidate("@staticmethod is ALWAYS wrong.", "MUST_NOT", "python"))

    merged = merge_duplicates([readme, topic])

    assert len(merged) == 1
    assert len(merged[0].sources) == 2
    assert merged[0].language == "any"


def test_compile_guides_offline_produces_ids_and_manifest(writing_guide: Path, networking_spec: Path):
    artifact = compile_guides([writing_guide, networking_spec], jev=None, prefix="EX")

    assert artifact.rules[0].id == "EX-001"
    assert artifact.manifest.model == "heuristic"
    assert {s.path for s in artifact.manifest.sources} == {str(writing_guide), str(networking_spec)}
    assert artifact.manifest.evaluator_counts["static"] >= 8
