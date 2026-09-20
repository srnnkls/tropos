#!/usr/bin/env python3
"""Build immutable harness packages, pin the local sources, and deploy with Phora."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tomllib


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        ["python3", str(root / "scripts/build-harnesses.py")], cwd=root, check=True
    )
    path = root / "phora.local.toml"
    start_marker = "# BEGIN TROPOS DEPENDENCY EXPORT\n"
    end_marker = "# END TROPOS DEPENDENCY EXPORT\n"
    text = path.read_text() if path.exists() else "version = 1\n"
    if start_marker in text:
        start = text.index(start_marker)
        end = text.index(end_marker, start) + len(end_marker)
        text = text[:start] + text[end:]
    if "tropos-dependencies" in tomllib.loads(text).get("sources", {}):
        raise ValueError(
            "phora.local.toml already defines tropos-dependencies outside the generated block"
        )
    block = (
        start_marker
        + "[sources.tropos-dependencies]\n"
        + "git = "
        + json.dumps(str(root / ".henia/packages/dependencies"))
        + "\n"
        + end_marker
    )
    block = block.removesuffix(end_marker)
    packages = {
        f"{name}-build": root / ".henia/build" / name
        for name in ("claude", "codex", "pi", "omp")
    }
    packages["tropos-dependencies"] = root / ".henia/packages/dependencies"
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=packages.pop("tropos-dependencies"), text=True
    ).strip()
    block += "rev = " + json.dumps(revision) + "\n"
    for name, directory in packages.items():
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=directory, text=True
        ).strip()
        block += (
            f"\n[sources.{name}]\npath = "
            + json.dumps(str(directory))
            + "\nrev = "
            + json.dumps(revision)
            + "\n"
        )
    path.write_text(text.rstrip() + "\n\n" + block + end_marker)
    subprocess.run(
        ["phora", "sync", "--fast-forward", "--prune", *sys.argv[1:]],
        cwd=root,
        check=True,
    )


if __name__ == "__main__":
    main()
