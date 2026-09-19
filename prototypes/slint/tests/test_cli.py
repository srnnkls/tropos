from __future__ import annotations

import json
from pathlib import Path

import pytest

from slint.cli import main


@pytest.fixture
def compiled(tmp_path: Path, examples_dir: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    artifact = tmp_path / "artifact"
    code = main(["compile", str(examples_dir / "guides"), "--offline", "--prefix", "EX", "-o", str(artifact)])
    assert code == 0
    capsys.readouterr()
    return artifact


def test_compile_writes_rules_and_manifest(compiled: Path):
    assert (compiled / "rules.json").exists()
    manifest = json.loads((compiled / "manifest.json").read_text())
    assert manifest["rule_count"] > 10
    assert manifest["model"] == "heuristic"


def test_check_exits_one_on_errors_and_prints_findings(
    compiled: Path, examples_dir: Path, capsys: pytest.CaptureFixture[str]
):
    code = main(["check", str(examples_dir / "sources"), "-a", str(compiled), "--offline", "--no-cache"])

    out = capsys.readouterr().out
    assert code == 1
    assert "client.py:28: error EX-001" in out
    assert "status-update.md:1: error" in out


def test_check_fail_on_warning_and_json_format(
    compiled: Path, examples_dir: Path, capsys: pytest.CaptureFixture[str]
):
    code = main(
        [
            "check",
            str(examples_dir / "sources" / "status-update.md"),
            "-a",
            str(compiled),
            "--offline",
            "--no-cache",
            "--format",
            "json",
            "--fail-on",
            "warning",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert code == 1
    assert payload["stats"]["judge_calls"] == 0


def test_check_passes_on_clean_input(compiled: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    clean = tmp_path / "clean.py"
    clean.write_text(
        "from __future__ import annotations\n\nimport requests\n\n\n"
        "def fetch(url: str) -> str:\n    return requests.get(url, timeout=5).text\n"
    )

    code = main(["check", str(clean), "-a", str(compiled), "--offline", "--no-cache", "--no-stats"])

    assert code == 0
    assert capsys.readouterr().out.strip() == "0 findings: 0 errors, 0 warnings, 0 info"


def test_missing_artifact_is_a_usage_error(
    tmp_path: Path, examples_dir: Path, capsys: pytest.CaptureFixture[str]
):
    code = main(["check", str(examples_dir / "sources"), "-a", str(tmp_path / "nope"), "--offline"])

    assert code == 2
    assert "run `slint compile` first" in capsys.readouterr().err


def test_rules_command_lists_evaluators(compiled: Path, capsys: pytest.CaptureFixture[str]):
    code = main(["rules", "-a", str(compiled)])

    out = capsys.readouterr().out
    assert code == 0
    assert "static:network_call_without_timeout" in out
    assert "feature: hedging > 1.5" in out


def test_features_command_dumps_the_ir(
    compiled: Path, examples_dir: Path, capsys: pytest.CaptureFixture[str]
):
    code = main(["features", str(examples_dir / "sources" / "status-update.md"), "--offline", "--no-cache"])

    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert code == 0
    assert all(line["extractor"] == "heuristic" for line in lines)
    assert "hedging" in lines[0]
