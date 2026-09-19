"""Restrict a check to the lines a git revision changed, so `slint check --diff` scales with the diff."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path

from slint.chunks import Chunk
from slint.errors import SlintError

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
NEW_FILE = re.compile(r"^\+\+\+ b/(.*)$")


def parse_unified_diff(diff: str) -> dict[str, set[int]]:
    changed: dict[str, set[int]] = {}
    current = ""
    for line in diff.splitlines():
        if file_match := NEW_FILE.match(line):
            current = file_match.group(1)
            changed.setdefault(current, set())
        elif current and (hunk := HUNK.match(line)):
            start = int(hunk.group(1))
            count = int(hunk.group(2)) if hunk.group(2) is not None else 1
            changed[current].update(range(start, start + max(count, 1)))
    return changed


def _git(cwd: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, timeout=60
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as error:
        detail = getattr(error, "stderr", "") or str(error)
        raise SlintError(f"git {args[0]} failed: {detail.strip()}") from error
    return completed.stdout


def git_root(cwd: Path) -> Path:
    """Diff headers are repository-root relative, so chunk paths must be compared against the same root."""
    return Path(_git(cwd, "rev-parse", "--show-toplevel").strip())


def changed_lines(revision: str, cwd: Path, paths: Iterable[Path]) -> dict[str, set[int]]:
    return parse_unified_diff(_git(cwd, "diff", "-U0", "--no-color", revision, "--", *map(str, paths)))


def overlaps(chunk: Chunk, changed: Mapping[str, set[int]], repo: Path) -> bool:
    lines = changed.get(_relative(chunk.file, repo))
    if not lines:
        return False
    return any(chunk.start_line <= line <= chunk.end_line for line in lines)


def _relative(file: str, repo: Path) -> str:
    try:
        return str(Path(file).resolve().relative_to(repo.resolve()))
    except ValueError:
        return file


def filter_to_changed(chunks: Iterable[Chunk], changed: Mapping[str, set[int]], repo: Path) -> list[Chunk]:
    return [chunk for chunk in chunks if overlaps(chunk, changed, repo)]
