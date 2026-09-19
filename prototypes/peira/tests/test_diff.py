from __future__ import annotations

import subprocess
from pathlib import Path

from peira.chunks import chunk_text
from peira.diff import changed_lines, filter_to_changed, git_root, parse_unified_diff

DIFF = """diff --git a/src/a.py b/src/a.py
--- a/src/a.py
+++ b/src/a.py
@@ -10,0 +11,2 @@ def f():
+    x = 1
+    y = 2
@@ -40 +42 @@ def g():
-    old
+    new
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1 @@
-# old
+# new
"""


def test_parse_unified_diff_collects_added_line_numbers_per_file():
    changed = parse_unified_diff(DIFF)

    assert changed == {"src/a.py": {11, 12, 42}, "README.md": {1}}


def test_filter_keeps_only_chunks_overlapping_changed_lines(tmp_path: Path):
    source = "def f():\n    return 1\n\n\ndef g():\n    return 2\n"
    file = tmp_path / "m.py"
    file.write_text(source)
    chunks = chunk_text(str(file), source)

    kept = filter_to_changed(chunks, {"m.py": {6}}, tmp_path)

    assert [chunk.name for chunk in kept] == ["g"]


def test_git_root_and_changed_lines_use_the_repository_root(tmp_path: Path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    nested = tmp_path / "pkg"
    nested.mkdir()
    file = nested / "m.py"
    file.write_text("def f():\n    return 1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "init"], check=True)
    file.write_text("def f():\n    return 1\n\n\ndef g():\n    return 2\n")

    root = git_root(nested)
    changed = changed_lines("HEAD", nested, [Path("m.py")])
    kept = filter_to_changed(chunk_text(str(file), file.read_text()), changed, root)

    assert root == tmp_path.resolve()
    assert changed == {"pkg/m.py": {3, 4, 5, 6}}
    assert [chunk.name for chunk in kept] == ["g"]
