"""Native detectors: rules that are statically decidable never reach the model.

Each detector is described in plain language so the compiler (Jev or the keyword fallback) can
map a guide sentence onto it. Python detectors work on the `ast` of a chunk and fall back to
regexes when a chunk is not parseable on its own.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from slint.chunks import Chunk, Domain

type Params = Mapping[str, int | str]


@dataclass(frozen=True, kw_only=True)
class Evidence:
    line: int
    snippet: str
    message: str


type DetectorFn = Callable[[Chunk, Params], list[Evidence]]


@dataclass(frozen=True, kw_only=True)
class DetectorSpec:
    name: str
    domain: Domain
    languages: tuple[str, ...]
    description: str
    keywords: tuple[str, ...]
    run: DetectorFn
    default_params: Mapping[str, int | str] = field(default_factory=dict)
    param_pattern: str | None = None  # regex with one int group, read from the rule text

    def applies_to(self, chunk: Chunk) -> bool:
        return chunk.domain == self.domain and ("any" in self.languages or chunk.language in self.languages)


def run_detector(spec: DetectorSpec, chunk: Chunk, params: Params) -> list[Evidence]:
    merged = {**spec.default_params, **params}
    return spec.run(chunk, merged)


def _snippet(chunk: Chunk, relative_line: int) -> str:
    lines = chunk.text.splitlines()
    if 0 <= relative_line < len(lines):
        return lines[relative_line].strip()[:120]
    return chunk.text.splitlines()[0].strip()[:120] if lines else ""


def _evidence(chunk: Chunk, relative_line: int, message: str) -> Evidence:
    return Evidence(
        line=chunk.start_line + relative_line, snippet=_snippet(chunk, relative_line), message=message
    )


def _parse(chunk: Chunk) -> ast.Module | None:
    try:
        return ast.parse(chunk.text)
    except SyntaxError:
        return None


def _walk(tree: ast.AST) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    stack = [tree]
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack.extend(ast.iter_child_nodes(node))
    return nodes


def _dotted(node: ast.AST) -> str:
    parts: list[str] = []
    current: ast.AST = node
    while True:
        match current:
            case ast.Attribute(value=value, attr=attr):
                parts.append(attr)
                current = value
            case ast.Name(id=name):
                parts.append(name)
                break
            case ast.Call(func=func):
                current = func
            case _:
                break
    return ".".join(reversed(parts))


def _regex_lines(chunk: Chunk, pattern: re.Pattern[str], message: str) -> list[Evidence]:
    return [
        _evidence(chunk, index, message)
        for index, line in enumerate(chunk.text.splitlines())
        if pattern.search(line)
    ]


ALLOWED_BASES = frozenset(
    {
        "Protocol",
        "Generic",
        "TypedDict",
        "NamedTuple",
        "Enum",
        "StrEnum",
        "IntEnum",
        "Flag",
        "IntFlag",
        "ABC",
        "BaseModel",
        "object",
        "Exception",
        "BaseException",
    }
)


def _is_exception_like(base: str) -> bool:
    tail = base.rsplit(".", maxsplit=1)[-1]
    return tail in ALLOWED_BASES or tail.endswith(("Error", "Exception", "Warning", "Protocol", "Mixin"))


def detect_staticmethod(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(
        chunk, re.compile(r"^\s*@staticmethod\b"), "@staticmethod: use a module-level function"
    )


def detect_behavioral_inheritance(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [_dotted(base) for base in node.bases]
        offending = [base for base in bases if base and not _is_exception_like(base)]
        if offending:
            found.append(
                _evidence(
                    chunk,
                    node.lineno - 1,
                    f"class {node.name} inherits behaviour from {', '.join(offending)}",
                )
            )
    return found


MUTABLE_CONSTRUCTORS = frozenset({"list", "dict", "set"})


def detect_mutable_default_argument(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        defaults = [*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]]
        for default in defaults:
            is_literal = isinstance(default, ast.List | ast.Dict | ast.Set)
            is_ctor = isinstance(default, ast.Call) and _dotted(default.func) in MUTABLE_CONSTRUCTORS
            if is_literal or is_ctor:
                found.append(
                    _evidence(chunk, default.lineno - 1, f"mutable default argument in {node.name}()")
                )
    return found


def detect_star_import(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(
        chunk, re.compile(r"^\s*from\s+\S+\s+import\s+\*"), "star import hides what was imported"
    )


def detect_section_divider_comment(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(
        chunk,
        re.compile(r"^\s*#\s*([=\-*#~]{4,}|[=\-*~]{2,}\s*\w.*[=\-*~]{2,})\s*$"),
        "section divider comment",
    )


BUILTIN_MATCH_CLASSES = frozenset({"str", "int", "float", "bool", "bytes", "list", "dict", "tuple", "set"})


def detect_positional_class_pattern(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        if (
            isinstance(node, ast.MatchClass)
            and node.patterns
            and _dotted(node.cls) not in BUILTIN_MATCH_CLASSES
        ):
            found.append(_evidence(chunk, node.lineno - 1, f"positional pattern on {_dotted(node.cls)}"))
    return found


def detect_root_logger_configured(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(chunk, re.compile(r"\blogging\.(basicConfig|root\.)"), "configures the root logger")


def detect_missing_future_annotations(chunk: Chunk, _: Params) -> list[Evidence]:
    if chunk.kind != "module":
        return []
    has_import = re.search(r"^\s*(import|from)\s+\w", chunk.text, re.MULTILINE)
    has_future = "from __future__ import annotations" in chunk.text
    if has_import and not has_future:
        return [_evidence(chunk, 0, "module does not enable `from __future__ import annotations`")]
    return []


DICT_ANY = re.compile(r"\b[Dd]ict\[\s*str\s*,\s*Any\s*\]")


def detect_dict_any_parameter(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name.startswith(("parse_", "from_", "load")) or node.name in ("from_dict", "from_json"):
            continue  # boundary parsers are where dict[str, Any] belongs
        for arg in [*node.args.args, *node.args.kwonlyargs]:
            if arg.annotation is not None and DICT_ANY.search(ast.unparse(arg.annotation)):
                found.append(
                    _evidence(
                        chunk,
                        node.lineno - 1,
                        f"{node.name}() takes dict[str, Any] `{arg.arg}` into core logic",
                    )
                )
    return found


def detect_test_class(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(
        chunk, re.compile(r"^\s*class\s+Test\w*\b"), "test class: use module-level test functions"
    )


NETWORK_CALLS = frozenset(
    {
        "requests.get",
        "requests.post",
        "requests.put",
        "requests.patch",
        "requests.delete",
        "requests.head",
        "requests.request",
        "httpx.get",
        "httpx.post",
        "httpx.put",
        "httpx.patch",
        "httpx.delete",
        "httpx.request",
        "httpx.Client",
        "httpx.AsyncClient",
        "urllib.request.urlopen",
        "urlopen",
    }
)


def detect_network_call_without_timeout(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        if not isinstance(node, ast.Call) or _dotted(node.func) not in NETWORK_CALLS:
            continue
        if not any(keyword.arg == "timeout" for keyword in node.keywords):
            found.append(
                _evidence(chunk, node.lineno - 1, f"{_dotted(node.func)}() without an explicit timeout")
            )
    return found


BLOCKING_CALLS = frozenset(
    {"requests.get", "requests.post", "requests.put", "requests.delete", "time.sleep", "open"}
)


def detect_blocking_io_in_async(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        for inner in _walk(node):
            if isinstance(inner, ast.Call) and _dotted(inner.func) in BLOCKING_CALLS:
                found.append(
                    _evidence(
                        chunk,
                        inner.lineno - 1,
                        f"blocking {_dotted(inner.func)}() inside async {node.name}()",
                    )
                )
    return found


def detect_swallowed_exception(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        if isinstance(node, ast.ExceptHandler) and all(isinstance(stmt, ast.Pass) for stmt in node.body):
            found.append(_evidence(chunk, node.lineno - 1, "exception caught and discarded"))
    return found


def detect_gather_without_error_handling(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        if not isinstance(node, ast.Call) or _dotted(node.func) != "asyncio.gather":
            continue
        if not any(keyword.arg == "return_exceptions" for keyword in node.keywords):
            found.append(
                _evidence(chunk, node.lineno - 1, "asyncio.gather without error handling; prefer TaskGroup")
            )
    return found


def detect_list_reassignment_instead_of_clear(chunk: Chunk, _: Params) -> list[Evidence]:
    tree = _parse(chunk)
    if tree is None:
        return []
    found: list[Evidence] = []
    for node in _walk(tree):
        match node:
            case ast.Assign(targets=[ast.Attribute() as target], value=ast.List(elts=[]) | ast.Dict(keys=[])):
                found.append(
                    _evidence(chunk, node.lineno - 1, f"{ast.unparse(target)} reassigned; use .clear()")
                )
    return found


def detect_typealias_import(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(
        chunk, re.compile(r"\bTypeAlias\b"), "TypeAlias: use a plain assignment or `type X = ...`"
    )


GRAB_BAG_MODULES = frozenset({"utils", "util", "common", "helpers", "misc"})


def detect_grab_bag_module(chunk: Chunk, _: Params) -> list[Evidence]:
    if chunk.kind != "module":
        return []
    stem = Path(chunk.file).stem
    if stem in GRAB_BAG_MODULES:
        return [_evidence(chunk, 0, f"module named {stem}.py: name it after what it contains")]
    return []


SMALL_WORDS = frozenset(
    {"a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "vs", "at", "by"}
)


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'-]*", text)]


def detect_heading_not_sentence_case(chunk: Chunk, _: Params) -> list[Evidence]:
    if chunk.kind != "heading":
        return []
    words = _words(chunk.text)
    capitalised_tail = [
        w for w in words[1:] if w[0].isupper() and w.lower() not in SMALL_WORDS and not w.isupper()
    ]
    if len(capitalised_tail) >= 2:
        return [_evidence(chunk, 0, "heading is not in sentence case")]
    return []


def detect_heading_not_title_case(chunk: Chunk, _: Params) -> list[Evidence]:
    if chunk.kind != "heading":
        return []
    words = _words(chunk.text)
    lowercase_major = [w for w in words[1:] if w[0].islower() and w.lower() not in SMALL_WORDS]
    if lowercase_major:
        return [_evidence(chunk, 0, "heading is not in title case")]
    return []


def detect_exclamation(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(chunk, re.compile(r"!(?!\[)"), "exclamation mark")


def detect_em_dash(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(chunk, re.compile(r"—|(?<=\w) -- (?=\w)"), "em dash")


def detect_parenthetical(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(chunk, re.compile(r"(?<!\])\([^()]{3,}\)"), "parenthetical aside")


def detect_semicolon(chunk: Chunk, _: Params) -> list[Evidence]:
    return _regex_lines(chunk, re.compile(r"(?<=\w);\s"), "semicolon joining clauses")


SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def detect_long_sentence(chunk: Chunk, params: Params) -> list[Evidence]:
    if chunk.kind not in ("paragraph", "list"):
        return []
    limit = int(params.get("max_words", 30))
    found: list[Evidence] = []
    for index, line in enumerate(chunk.text.splitlines()):
        for sentence in SENTENCE_END.split(line):
            count = len(_words(sentence))
            if count > limit:
                found.append(_evidence(chunk, index, f"sentence has {count} words (limit {limit})"))
                break
    return found


def detect_first_person_plural(chunk: Chunk, _: Params) -> list[Evidence]:
    if chunk.kind not in ("paragraph", "list"):
        return []
    return _regex_lines(chunk, re.compile(r"\b[Ww]e('re|'ve|'ll)?\b|\b[Oo]ur\b"), "first person plural")


def detect_second_person(chunk: Chunk, _: Params) -> list[Evidence]:
    if chunk.kind not in ("paragraph", "list"):
        return []
    return _regex_lines(
        chunk, re.compile(r"\b[Yy]ou('re|'ve|'ll)?\b|\b[Yy]our\b"), "addresses the reader as you"
    )


PYTHON = ("python",)
MARKDOWN = ("markdown", "text")

DETECTORS: tuple[DetectorSpec, ...] = (
    DetectorSpec(
        name="staticmethod",
        domain="code",
        languages=PYTHON,
        description="a method is decorated with @staticmethod",
        keywords=("staticmethod", "static method"),
        run=detect_staticmethod,
    ),
    DetectorSpec(
        name="behavioral_inheritance",
        domain="code",
        languages=PYTHON,
        description=(
            "a class inherits from a base that is not an exception, protocol, enum or typing construct"
        ),
        keywords=("inheritance", "inherit", "subclass", "base class", "mixin"),
        run=detect_behavioral_inheritance,
    ),
    DetectorSpec(
        name="mutable_default_argument",
        domain="code",
        languages=PYTHON,
        description="a function parameter defaults to a mutable list, dict or set",
        keywords=("mutable default",),
        run=detect_mutable_default_argument,
    ),
    DetectorSpec(
        name="star_import",
        domain="code",
        languages=PYTHON,
        description="a module uses `from x import *`",
        keywords=("star import", "import *"),
        run=detect_star_import,
    ),
    DetectorSpec(
        name="section_divider_comment",
        domain="code",
        languages=PYTHON,
        description="a comment line is a section divider such as `# ==== Models ====`",
        keywords=("section divider", "divider", "ascii art"),
        run=detect_section_divider_comment,
    ),
    DetectorSpec(
        name="positional_class_pattern",
        domain="code",
        languages=PYTHON,
        description="a match/case class pattern uses positional sub-patterns instead of keyword patterns",
        keywords=("positional pattern", "keyword pattern", "positional patterns"),
        run=detect_positional_class_pattern,
    ),
    DetectorSpec(
        name="root_logger_configured",
        domain="code",
        languages=PYTHON,
        description="code calls logging.basicConfig or otherwise configures the root logger",
        keywords=("root logger", "basicconfig", "logger"),
        run=detect_root_logger_configured,
    ),
    DetectorSpec(
        name="missing_future_annotations",
        domain="code",
        languages=PYTHON,
        description="a module with imports does not start with `from __future__ import annotations`",
        keywords=("__future__", "future annotations", "future import"),
        run=detect_missing_future_annotations,
    ),
    DetectorSpec(
        name="dict_any_parameter",
        domain="code",
        languages=PYTHON,
        description="a non-parsing function accepts dict[str, Any] as a parameter",
        keywords=("dict[str, any]", "dict[str,any]"),
        run=detect_dict_any_parameter,
    ),
    DetectorSpec(
        name="test_class",
        domain="code",
        languages=PYTHON,
        description="a test file groups tests in a class named Test*",
        keywords=("test class", "test classes"),
        run=detect_test_class,
    ),
    DetectorSpec(
        name="network_call_without_timeout",
        domain="code",
        languages=PYTHON,
        description="an HTTP or network client call is made without a timeout argument",
        keywords=("timeout",),
        run=detect_network_call_without_timeout,
    ),
    DetectorSpec(
        name="blocking_io_in_async",
        domain="code",
        languages=PYTHON,
        description="an async function calls blocking I/O such as requests.get, time.sleep or open",
        keywords=("blocking", "event loop", "block"),
        run=detect_blocking_io_in_async,
    ),
    DetectorSpec(
        name="swallowed_exception",
        domain="code",
        languages=PYTHON,
        description="an except handler does nothing but pass",
        keywords=("swallow", "silently", "except: pass", "bare except"),
        run=detect_swallowed_exception,
    ),
    DetectorSpec(
        name="gather_without_error_handling",
        domain="code",
        languages=PYTHON,
        description="asyncio.gather is called without return_exceptions",
        keywords=("gather", "taskgroup", "structured concurrency"),
        run=detect_gather_without_error_handling,
    ),
    DetectorSpec(
        name="list_reassignment_instead_of_clear",
        domain="code",
        languages=PYTHON,
        description=(
            "an attribute holding a collection is reset by assigning a new empty literal instead of .clear()"
        ),
        keywords=(".clear()", "clear()", "= []"),
        run=detect_list_reassignment_instead_of_clear,
    ),
    DetectorSpec(
        name="typealias_import",
        domain="code",
        languages=PYTHON,
        description="typing.TypeAlias is used instead of a plain alias assignment",
        keywords=("typealias", "type alias"),
        run=detect_typealias_import,
    ),
    DetectorSpec(
        name="grab_bag_module",
        domain="code",
        languages=PYTHON,
        description="a module is named utils, common, helpers or misc",
        keywords=("utils", "common module", "helpers", "grab bag"),
        run=detect_grab_bag_module,
    ),
    DetectorSpec(
        name="heading_not_sentence_case",
        domain="prose",
        languages=MARKDOWN,
        description="a heading capitalises words beyond the first, i.e. is not in sentence case",
        keywords=("sentence case",),
        run=detect_heading_not_sentence_case,
    ),
    DetectorSpec(
        name="heading_not_title_case",
        domain="prose",
        languages=MARKDOWN,
        description="a heading leaves major words lowercase, i.e. is not in title case",
        keywords=("title case",),
        run=detect_heading_not_title_case,
    ),
    DetectorSpec(
        name="exclamation",
        domain="prose",
        languages=MARKDOWN,
        description="the text contains an exclamation mark",
        keywords=("exclamation",),
        run=detect_exclamation,
    ),
    DetectorSpec(
        name="em_dash",
        domain="prose",
        languages=MARKDOWN,
        description="the text contains an em dash",
        keywords=("em dash", "em-dash", "dash"),
        run=detect_em_dash,
    ),
    DetectorSpec(
        name="parenthetical",
        domain="prose",
        languages=MARKDOWN,
        description="the text contains a parenthetical aside",
        keywords=("parenthetical", "parenthes"),
        run=detect_parenthetical,
    ),
    DetectorSpec(
        name="semicolon",
        domain="prose",
        languages=MARKDOWN,
        description="a semicolon joins two clauses",
        keywords=("semicolon",),
        run=detect_semicolon,
    ),
    DetectorSpec(
        name="long_sentence",
        domain="prose",
        languages=MARKDOWN,
        description="a sentence exceeds a word limit",
        keywords=("words", "sentence length", "long sentence", "sentences under", "sentences short"),
        run=detect_long_sentence,
        default_params={"max_words": 30},
        param_pattern=r"(\d{1,3})\s*words",
    ),
    DetectorSpec(
        name="first_person_plural",
        domain="prose",
        languages=MARKDOWN,
        description="the text uses first person plural (we, our)",
        keywords=("first person", "we/our", '"we"'),
        run=detect_first_person_plural,
    ),
    DetectorSpec(
        name="second_person",
        domain="prose",
        languages=MARKDOWN,
        description="the text addresses the reader as you",
        keywords=("second person", '"you"', "address the reader"),
        run=detect_second_person,
    ),
)

DETECTORS_BY_NAME: Mapping[str, DetectorSpec] = {spec.name: spec for spec in DETECTORS}


def detectors_for(domain: Domain, language: str) -> tuple[DetectorSpec, ...]:
    return tuple(
        spec
        for spec in DETECTORS
        if spec.domain == domain and ("any" in spec.languages or language in spec.languages)
    )
