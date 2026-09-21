#!/usr/bin/env python3
"""Build Tropos and exercise its optional repository-local smoke deployment."""

from pathlib import Path
import shutil
import subprocess
import sys


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, str(root / "scripts/build-harnesses.py")], cwd=root, check=True
    )
    project = root / ".henia/probe"
    project.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / "phora/prototype.toml", project / "phora.toml")
    subprocess.run(
        ["phora", "update", "tropos", "--fast-forward"],
        cwd=project,
        check=True,
    )


if __name__ == "__main__":
    main()
