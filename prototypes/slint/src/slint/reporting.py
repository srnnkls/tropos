"""Render check results as terminal text, JSON, or SARIF 2.1.0 for code-scanning integrations."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict

from slint import __version__
from slint.evaluation import CheckResult, Finding
from slint.rules import Artifact, Requirement

SARIF_LEVEL = {"error": "error", "warning": "warning", "info": "note"}


def render_text(result: CheckResult, *, show_stats: bool = True) -> str:
    lines: list[str] = []
    for finding in result.findings:
        header = f"{finding.file}:{finding.line}: {finding.severity} {finding.rule_id} [{finding.evaluator}]"
        lines.append(f"{header} {finding.statement}")
        if finding.message and finding.message != finding.statement:
            lines.append(f"    {finding.message}")
        if finding.snippet:
            lines.append(f"    > {finding.snippet}")
        lines.append(f"    source: {finding.source}")
    lines.append(_summary(result))
    if show_stats:
        lines.append(_stats(result))
    return "\n".join(lines)


def _summary(result: CheckResult) -> str:
    counts = {"error": 0, "warning": 0, "info": 0}
    for finding in result.findings:
        counts[finding.severity] += 1
    total = len(result.findings)
    noun = "finding" if total == 1 else "findings"
    return f"{total} {noun}: {counts['error']} errors, {counts['warning']} warnings, {counts['info']} info"


def _stats(result: CheckResult) -> str:
    s = result.stats
    density = f"{s.routed_pairs}/{s.possible_pairs}" if s.possible_pairs else "0/0"
    line = (
        f"chunks {s.chunks} · rules {s.rules} · routed pairs {density} · static {s.static_checks} · "
        f"feature {s.feature_checks} (extracted {s.chunks_extracted}, cached {s.chunks_from_cache}) · "
        f"judge calls {s.judge_calls} carrying {s.judge_questions} questions · model {s.model}"
    )
    if s.judge_rules_skipped:
        line += (
            f"\n{s.judge_rules_skipped} judge rules skipped offline; set TYPESAFE_API_KEY to evaluate them"
        )
    return line


def render_json(result: CheckResult) -> str:
    return json.dumps(
        {"findings": [asdict(f) for f in result.findings], "stats": asdict(result.stats)}, indent=2
    )


def render_sarif(result: CheckResult, artifact: Artifact) -> str:
    rules_by_id = {rule.id: rule for rule in artifact.rules}
    referenced = sorted({finding.rule_id for finding in result.findings})
    rule_index = {rule_id: index for index, rule_id in enumerate(referenced)}
    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "slint",
                        "version": __version__,
                        "informationUri": "https://github.com/srnnkls/tropos",
                        "rules": [
                            _sarif_rule(rules_by_id[rule_id])
                            for rule_id in referenced
                            if rule_id in rules_by_id
                        ],
                    }
                },
                "results": [_sarif_result(finding, rule_index) for finding in result.findings],
            }
        ],
    }
    return json.dumps(sarif, indent=2)


def _sarif_rule(rule: Requirement) -> dict[str, object]:
    return {
        "id": rule.id,
        "shortDescription": {"text": rule.statement[:200]},
        "fullDescription": {"text": rule.statement},
        "help": {"text": "\n".join(f"{s.anchor}: {s.text}" for s in rule.sources)},
        "properties": {"modality": rule.modality, "evaluator": rule.evaluator.kind, "scope": rule.scope},
    }


def _sarif_result(finding: Finding, rule_index: dict[str, int]) -> dict[str, object]:
    return {
        "ruleId": finding.rule_id,
        "ruleIndex": rule_index.get(finding.rule_id, -1),
        "level": SARIF_LEVEL[finding.severity],
        "message": {
            "text": f"{finding.statement} — {finding.message}" if finding.message else finding.statement
        },
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.file},
                    "region": {"startLine": finding.line, "endLine": max(finding.end_line, finding.line)},
                }
            }
        ],
        "properties": {
            "evaluator": finding.evaluator,
            "confidence": finding.confidence,
            "source": finding.source,
        },
    }


def render_rules(rules: Sequence[Requirement]) -> str:
    lines: list[str] = []
    for rule in rules:
        evaluator = rule.evaluator
        match evaluator.kind:
            case "static":
                how = f"static:{evaluator.detector}"  # type: ignore[union-attr]
                if evaluator.params:  # type: ignore[union-attr]
                    how += f" {dict(evaluator.params)}"  # type: ignore[union-attr]
            case "feature":
                how = "feature: " + " and ".join(
                    f"{c.feature} {c.op} {c.value}"
                    for c in evaluator.violated_when  # type: ignore[union-attr]
                )
            case "judge":
                how = "judge"
            case _:
                how = f"unsupported: {evaluator.reason}"  # type: ignore[union-attr]
        scope = "" if rule.scope == "any" else f" scope={rule.scope}"
        lines.append(f"{rule.id} {rule.modality} [{rule.domain}/{rule.language}{scope}] {rule.statement}")
        lines.append(f"    {how} (confidence {rule.compiler_confidence:.2f})")
        for source in rule.sources:
            lines.append(f"    source: {source.anchor}")
    return "\n".join(lines)
