from __future__ import annotations

import json
from pathlib import Path

from slint.chunks import chunk_text
from slint.compiler import compile_guides
from slint.evaluation import check
from slint.reporting import render_json, render_sarif, render_text


def _result(guide: Path, source: Path):
    artifact = compile_guides([guide], jev=None, prefix="EX")
    return artifact, check(artifact, chunk_text(str(source), source.read_text()), jev=None, cache_dir=None)


def test_text_report_names_file_line_rule_and_source(networking_spec: Path, client_source: Path):
    _, result = _result(networking_spec, client_source)

    text = render_text(result)

    assert "client.py:28: error EX-001 [static]" in text
    assert "source: examples/guides/networking-spec.md:11" in text or "networking-spec.md:11" in text
    assert "findings:" in text


def test_sarif_report_is_well_formed(networking_spec: Path, client_source: Path):
    artifact, result = _result(networking_spec, client_source)

    sarif = json.loads(render_sarif(result, artifact))

    run = sarif["runs"][0]
    assert sarif["version"] == "2.1.0"
    assert run["tool"]["driver"]["name"] == "slint"
    assert {rule["id"] for rule in run["tool"]["driver"]["rules"]} == {f.rule_id for f in result.findings}
    first = run["results"][0]
    assert first["level"] in ("error", "warning", "note")
    assert first["locations"][0]["physicalLocation"]["region"]["startLine"] == result.findings[0].line


def test_json_report_carries_stats(networking_spec: Path, client_source: Path):
    _, result = _result(networking_spec, client_source)

    payload = json.loads(render_json(result))

    assert payload["stats"]["routed_pairs"] <= payload["stats"]["possible_pairs"]
    assert len(payload["findings"]) == len(result.findings)
