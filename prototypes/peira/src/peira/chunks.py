"""Partition source artifacts into chunks that rules can be routed to.

Markdown becomes headings, paragraphs, lists and fenced code blocks; Python becomes top-level
functions and classes plus a module preamble; anything else is one chunk. Each chunk carries the
metadata the router needs: kind, domain, language, document position and heading path.
"""

from __future__ import annotations

import ast
import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

type Domain = Literal["prose", "code"]
type Position = Literal["opening", "body", "closing"]
type ChunkKind = Literal["heading", "paragraph", "list", "code_block", "module", "function", "class", "file"]

PROSE_SUFFIXES = frozenset({".md", ".markdown", ".txt", ".rst", ".adoc"})
CODE_LANGUAGES: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".sh": "shell",
    ".bash": "shell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".json": "json",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".zig": "zig",
    ".el": "elisp",
}


@dataclass(frozen=True, kw_only=True)
class Chunk:
    id: str
    file: str
    kind: ChunkKind
    domain: Domain
    language: str
    text: str
    start_line: int
    end_line: int
    heading_path: tuple[str, ...] = ()
    position: Position = "body"
    name: str | None = None

    @property
    def location(self) -> str:
        return f"{self.file}:{self.start_line}"

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1


def chunk_id(file: str, start_line: int, end_line: int, text: str) -> str:
    digest = hashlib.sha256(f"{file}:{start_line}-{end_line}\n{text}".encode()).hexdigest()
    return digest[:16]


def language_for(path: str) -> tuple[str, Domain]:
    suffix = Path(path).suffix.lower()
    if suffix in (".md", ".markdown"):
        return "markdown", "prose"
    if suffix in PROSE_SUFFIXES:
        return "text", "prose"
    if suffix in CODE_LANGUAGES:
        return CODE_LANGUAGES[suffix], "code"
    return "text", "prose"


def chunk_file(path: Path) -> list[Chunk]:
    return chunk_text(str(path), path.read_text(encoding="utf-8", errors="replace"))


def chunk_text(file: str, text: str) -> list[Chunk]:
    language, domain = language_for(file)
    match language:
        case "markdown":
            return chunk_markdown(file, text)
        case "python":
            return chunk_python(file, text)
        case _:
            return [_whole_file_chunk(file, text, kind="file", domain=domain, language=language)]


def _whole_file_chunk(file: str, text: str, *, kind: ChunkKind, domain: Domain, language: str) -> Chunk:
    end_line = max(len(text.splitlines()), 1)
    return Chunk(
        id=chunk_id(file, 1, end_line, text),
        file=file,
        kind=kind,
        domain=domain,
        language=language,
        text=text,
        start_line=1,
        end_line=end_line,
        position="opening",
    )


HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^(```|~~~)\s*([\w+-]*)")
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
FRONT_MATTER_DELIMITER = "---"


def chunk_markdown(file: str, text: str) -> list[Chunk]:
    lines = text.splitlines()
    chunks: list[Chunk] = []
    heading_path: tuple[str, ...] = ()
    index = _skip_front_matter(lines)
    total = len(lines)

    while index < total:
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if fence := FENCE.match(line):
            chunk, index = _read_fenced_block(
                file, lines, index, fence.group(1), fence.group(2), heading_path
            )
            if chunk is not None:
                chunks.append(chunk)
            continue
        if heading := HEADING.match(line):
            level = len(heading.group(1))
            title = heading.group(2).strip()
            heading_path = (*heading_path[: level - 1], title)
            chunks.append(_markdown_chunk(file, "heading", index + 1, index + 1, title, heading_path))
            index += 1
            continue
        if LIST_ITEM.match(line):
            end = _scan_while(lines, index, _continues_list)
            chunks.append(
                _markdown_chunk(file, "list", index + 1, end, "\n".join(lines[index:end]), heading_path)
            )
            index = end
            continue
        end = _scan_while(lines, index, _continues_paragraph)
        chunks.append(
            _markdown_chunk(file, "paragraph", index + 1, end, "\n".join(lines[index:end]), heading_path)
        )
        index = end

    return _mark_positions([chunk for chunk in chunks if chunk.text.strip()])


def _skip_front_matter(lines: list[str]) -> int:
    if not lines or lines[0].strip() != FRONT_MATTER_DELIMITER:
        return 0
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONT_MATTER_DELIMITER:
            return index + 1
    return 0


def _continues_list(line: str) -> bool:
    return bool(line.strip()) and (LIST_ITEM.match(line) is not None or line.startswith((" ", "\t")))


def _continues_paragraph(line: str) -> bool:
    return (
        bool(line.strip()) and not HEADING.match(line) and not FENCE.match(line) and not LIST_ITEM.match(line)
    )


def _scan_while(lines: list[str], start: int, predicate: Callable[[str], bool]) -> int:
    index = start
    while index < len(lines) and predicate(lines[index]):
        index += 1
    return index


def _read_fenced_block(
    file: str, lines: list[str], start: int, marker: str, language: str, heading_path: tuple[str, ...]
) -> tuple[Chunk | None, int]:
    end = start + 1
    while end < len(lines) and not lines[end].startswith(marker):
        end += 1
    body = "\n".join(lines[start + 1 : end])
    if not body.strip():
        return None, end + 1
    chunk = Chunk(
        id=chunk_id(file, start + 2, end, body),
        file=file,
        kind="code_block",
        domain="code",
        language=language or "text",
        text=body,
        start_line=start + 2,
        end_line=end,
        heading_path=heading_path,
    )
    return chunk, end + 1


def _markdown_chunk(
    file: str, kind: ChunkKind, start_line: int, end_line: int, text: str, heading_path: tuple[str, ...]
) -> Chunk:
    return Chunk(
        id=chunk_id(file, start_line, end_line, text),
        file=file,
        kind=kind,
        domain="prose",
        language="markdown",
        text=text,
        start_line=start_line,
        end_line=end_line,
        heading_path=heading_path,
    )


def _mark_positions(chunks: list[Chunk]) -> list[Chunk]:
    """Flag the first and last prose chunks so answer-first and conclusion rules can route to them."""
    prose_indexes = [index for index, chunk in enumerate(chunks) if chunk.kind in ("paragraph", "list")]
    if not prose_indexes:
        return chunks
    marked = list(chunks)
    marked[prose_indexes[0]] = replace(marked[prose_indexes[0]], position="opening")
    if len(prose_indexes) > 1:
        marked[prose_indexes[-1]] = replace(marked[prose_indexes[-1]], position="closing")
    return marked


def chunk_python(file: str, text: str) -> list[Chunk]:
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [_whole_file_chunk(file, text, kind="file", domain="code", language="python")]

    chunks: list[Chunk] = []
    covered: set[int] = set()
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue
        start = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
        end = node.end_lineno or node.lineno
        body = "\n".join(lines[start - 1 : end])
        chunks.append(
            Chunk(
                id=chunk_id(file, start, end, body),
                file=file,
                kind="class" if isinstance(node, ast.ClassDef) else "function",
                domain="code",
                language="python",
                text=body,
                start_line=start,
                end_line=end,
                name=node.name,
            )
        )
        covered.update(range(start, end + 1))

    preamble = [
        (number, line) for number, line in enumerate(lines, start=1) if number not in covered and line.strip()
    ]
    if preamble:
        body = "\n".join(line for _, line in preamble)
        chunks.append(
            Chunk(
                id=chunk_id(file, preamble[0][0], preamble[-1][0], body),
                file=file,
                kind="module",
                domain="code",
                language="python",
                text=body,
                start_line=preamble[0][0],
                end_line=preamble[-1][0],
                name="<module>",
            )
        )
    chunks.sort(key=lambda chunk: chunk.start_line)
    if not chunks:
        return []
    chunks[0] = replace(chunks[0], position="opening")
    if len(chunks) > 1:
        chunks[-1] = replace(chunks[-1], position="closing")
    return chunks
