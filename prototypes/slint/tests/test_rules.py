from __future__ import annotations

import json
from pathlib import Path

import pytest

from slint.compiler import compile_guides
from slint.errors import ArtifactError
from slint.rules import load_artifact, save_artifact


def test_artifact_round_trips_through_disk(tmp_path: Path, writing_guide: Path, networking_spec: Path):
    artifact = compile_guides([writing_guide, networking_spec], jev=None, prefix="EX")

    save_artifact(artifact, tmp_path)
    loaded = load_artifact(tmp_path)

    assert loaded == artifact


def test_missing_artifact_is_a_clear_error(tmp_path: Path):
    with pytest.raises(ArtifactError, match="run `slint compile` first"):
        load_artifact(tmp_path)


def test_feature_schema_mismatch_demands_recompile(tmp_path: Path, writing_guide: Path):
    save_artifact(compile_guides([writing_guide], jev=None), tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    manifest["feature_schema_version"] = "0"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))

    with pytest.raises(ArtifactError, match="Recompile"):
        load_artifact(tmp_path)


def test_corrupt_rules_file_is_a_clear_error(tmp_path: Path, writing_guide: Path):
    save_artifact(compile_guides([writing_guide], jev=None), tmp_path)
    (tmp_path / "rules.json").write_text('[{"id": "X"}]')

    with pytest.raises(ArtifactError, match="corrupt artifact"):
        load_artifact(tmp_path)
