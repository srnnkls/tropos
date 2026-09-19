from __future__ import annotations

from dataclasses import dataclass

import pytest

from peira.chunks import chunk_markdown, chunk_python, chunk_text

MARKDOWN = """---
paths: "**/*.py"
---

# Title

Opening paragraph that answers.

## Details

- first item
- second item
  continued

```python
def f():
    return 1
```

Closing paragraph.
"""


def test_markdown_front_matter_is_not_a_chunk():
    chunks = chunk_markdown("guide.md", MARKDOWN)

    assert all("paths:" not in chunk.text for chunk in chunks)


def test_markdown_splits_into_heading_paragraph_list_and_code():
    chunks = chunk_markdown("guide.md", MARKDOWN)

    assert [chunk.kind for chunk in chunks] == [
        "heading",
        "paragraph",
        "heading",
        "list",
        "code_block",
        "paragraph",
    ]


def test_markdown_code_block_is_code_domain_with_fence_language():
    chunks = chunk_markdown("guide.md", MARKDOWN)

    code = next(chunk for chunk in chunks if chunk.kind == "code_block")

    assert code.domain == "code"
    assert code.language == "python"
    assert code.start_line == 16


def test_markdown_marks_first_and_last_prose_chunks():
    chunks = chunk_markdown("guide.md", MARKDOWN)

    prose = [chunk for chunk in chunks if chunk.kind in ("paragraph", "list")]

    assert prose[0].position == "opening"
    assert prose[-1].position == "closing"
    assert prose[1].position == "body"


def test_markdown_heading_path_tracks_nesting():
    chunks = chunk_markdown("guide.md", MARKDOWN)

    closing = chunks[-1]

    assert closing.heading_path == ("Title", "Details")


PYTHON = '''"""Module docstring."""
import os

CONSTANT = 1


@decorator
def first():
    return os.name


class Thing:
    def method(self):
        return CONSTANT
'''


def test_python_yields_one_chunk_per_top_level_definition_plus_preamble():
    chunks = chunk_python("mod.py", PYTHON)

    assert [(chunk.kind, chunk.name) for chunk in chunks] == [
        ("module", "<module>"),
        ("function", "first"),
        ("class", "Thing"),
    ]


def test_python_function_chunk_starts_at_its_decorator():
    chunks = chunk_python("mod.py", PYTHON)

    function = next(chunk for chunk in chunks if chunk.name == "first")

    assert function.start_line == 7
    assert function.text.startswith("@decorator")


def test_unparseable_python_falls_back_to_one_file_chunk():
    chunks = chunk_python("broken.py", "def broken(:\n  pass\n")

    assert len(chunks) == 1
    assert chunks[0].kind == "file"


@dataclass(frozen=True)
class LanguageCase:
    file: str
    language: str
    domain: str
    description: str


LANGUAGE_CASES = [
    LanguageCase(file="README.md", language="markdown", domain="prose", description="markdown"),
    LanguageCase(file="main.go", language="go", domain="code", description="go"),
    LanguageCase(file="notes.txt", language="text", domain="prose", description="plain text"),
    LanguageCase(file="Makefile", language="text", domain="prose", description="unknown suffix"),
]


@pytest.mark.parametrize("case", LANGUAGE_CASES, ids=lambda c: c.description)
def test_unknown_languages_become_single_chunks(case: LanguageCase):
    chunks = chunk_text(case.file, "content\n")

    assert chunks[0].language == case.language
    assert chunks[0].domain == case.domain
