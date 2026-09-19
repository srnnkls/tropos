"""Command line surface: compile guides, check sources, inspect rules and the IR.

Exit codes: 0 clean (or only findings below --fail-on), 1 findings at or above --fail-on,
2 usage or configuration error.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Iterable, Sequence
from dataclasses import asdict
from pathlib import Path

from slint import __version__
from slint.chunks import CODE_LANGUAGES, PROSE_SUFFIXES, Chunk, chunk_file
from slint.compiler import compile_guides
from slint.diff import changed_lines, filter_to_changed, git_root
from slint.errors import SlintError
from slint.evaluation import SEVERITY_RANK, check
from slint.extraction import extract_features
from slint.jev import Jev, RecordingJev, jev_from_env
from slint.reporting import render_json, render_rules, render_sarif, render_text
from slint.rules import Severity, load_artifact, save_artifact

DEFAULT_ARTIFACT_DIR = Path(".slint")
CACHE_SUBDIR = "cache/features"
SKIPPED_DIRECTORIES = frozenset(
    {".git", ".slint", ".venv", "node_modules", "__pycache__", ".peer", ".worktrees"}
)
CHECKABLE_SUFFIXES = PROSE_SUFFIXES | frozenset(CODE_LANGUAGES)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slint", description="Semantic compliance: compile rules, check sources."
    )
    parser.add_argument("--version", action="version", version=f"slint {__version__}")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="log what the compiler and runtime decide"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    compile_parser = commands.add_parser(
        "compile", help="compile guides, specs and policies into an artifact"
    )
    compile_parser.add_argument("sources", nargs="+", type=Path, help="markdown files or directories")
    compile_parser.add_argument("-o", "--output", type=Path, default=DEFAULT_ARTIFACT_DIR)
    compile_parser.add_argument("--prefix", default="RULE", help="rule id prefix, e.g. LOQ-PY")
    _model_flags(compile_parser)

    check_parser = commands.add_parser("check", help="check files against a compiled artifact")
    check_parser.add_argument("paths", nargs="+", type=Path)
    check_parser.add_argument("-a", "--artifact", type=Path, default=DEFAULT_ARTIFACT_DIR)
    check_parser.add_argument("--diff", metavar="REV", help="only check chunks touched since REV")
    check_parser.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    check_parser.add_argument("--fail-on", choices=("error", "warning", "info"), default="error")
    check_parser.add_argument(
        "--no-cache", action="store_true", help="do not read or write the feature cache"
    )
    check_parser.add_argument("--no-stats", action="store_true")
    _model_flags(check_parser)

    rules_parser = commands.add_parser("rules", help="show the compiled rules")
    rules_parser.add_argument("-a", "--artifact", type=Path, default=DEFAULT_ARTIFACT_DIR)
    rules_parser.add_argument("--format", choices=("text", "json"), default="text")

    features_parser = commands.add_parser("features", help="dump the semantic IR for files")
    features_parser.add_argument("paths", nargs="+", type=Path)
    features_parser.add_argument("-a", "--artifact", type=Path, default=DEFAULT_ARTIFACT_DIR)
    features_parser.add_argument("--no-cache", action="store_true")
    _model_flags(features_parser)
    return parser


def _model_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--offline", action="store_true", help="never call the model; use native checks and heuristics"
    )
    parser.add_argument("--model", help="TypeSafe model name (default: jev-latest or TYPESAFE_DEFAULT_MODEL)")
    parser.add_argument(
        "--trace", action="store_true", help="print every model exchange as JSON lines on stderr"
    )


def collect_files(paths: Iterable[Path], suffixes: frozenset[str]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in sorted(path.rglob("*")):
                if any(part in SKIPPED_DIRECTORIES for part in candidate.parts):
                    continue
                if candidate.is_file() and candidate.suffix.lower() in suffixes:
                    files.append(candidate)
        elif path.is_file():
            files.append(path)
        else:
            raise SlintError(f"no such file: {path}")
    return files


def _backend(args: argparse.Namespace) -> Jev | None:
    jev = jev_from_env(offline=args.offline, model=args.model)
    if jev is None and not args.offline:
        print(
            "slint: TYPESAFE_API_KEY not set, running offline (native checks and heuristics only)",
            file=sys.stderr,
        )
    if jev is not None and args.trace:
        return RecordingJev(inner=jev)
    return jev


def _dump_trace(jev: Jev | None) -> None:
    if not isinstance(jev, RecordingJev):
        return
    for exchange in jev.log:
        print(
            json.dumps(
                {
                    "state": exchange.state,
                    "questions": {k: q.to_wire() for k, q in exchange.questions.items()},
                    "answers": {k: asdict(a) for k, a in exchange.response.answers.items()},
                }
            ),
            file=sys.stderr,
        )


def run_compile(args: argparse.Namespace) -> int:
    files = collect_files(args.sources, frozenset({".md", ".markdown"}))
    if not files:
        raise SlintError("no markdown guides found")
    jev = _backend(args)
    artifact = compile_guides(files, jev=jev, prefix=args.prefix)
    save_artifact(artifact, args.output)
    _dump_trace(jev)
    counts = ", ".join(
        f"{count} {kind}" for kind, count in sorted(artifact.manifest.evaluator_counts.items())
    )
    print(
        f"compiled {artifact.manifest.rule_count} rules from {len(files)} files into {args.output} ({counts})"
    )
    return 0


def _chunks(paths: Sequence[Path]) -> list[Chunk]:
    return [chunk for file in collect_files(paths, CHECKABLE_SUFFIXES) for chunk in chunk_file(file)]


def run_check(args: argparse.Namespace) -> int:
    artifact = load_artifact(args.artifact)
    chunks = _chunks(args.paths)
    if args.diff:
        cwd = Path.cwd()
        chunks = filter_to_changed(chunks, changed_lines(args.diff, cwd, args.paths), git_root(cwd))
    jev = _backend(args)
    cache_dir = None if args.no_cache else args.artifact / CACHE_SUBDIR
    result = check(artifact, chunks, jev=jev, cache_dir=cache_dir)
    _dump_trace(jev)
    match args.format:
        case "json":
            print(render_json(result))
        case "sarif":
            print(render_sarif(result, artifact))
        case _:
            print(render_text(result, show_stats=not args.no_stats))
    threshold: Severity = args.fail_on
    failing = any(SEVERITY_RANK[f.severity] <= SEVERITY_RANK[threshold] for f in result.findings)
    return 1 if failing else 0


def run_rules(args: argparse.Namespace) -> int:
    artifact = load_artifact(args.artifact)
    if args.format == "json":
        print(json.dumps([asdict(rule) for rule in artifact.rules], indent=2, ensure_ascii=False))
    else:
        print(render_rules(artifact.rules))
        m = artifact.manifest
        print(f"{m.rule_count} rules · compiler {m.compiler_version} · model {m.model} · {m.created_at}")
    return 0


def run_features(args: argparse.Namespace) -> int:
    chunks = [chunk for chunk in _chunks(args.paths) if chunk.kind != "heading"]
    jev = _backend(args)
    cache_dir = None if args.no_cache else args.artifact / CACHE_SUBDIR
    extraction = extract_features(chunks, jev, cache_dir)
    _dump_trace(jev)
    for chunk in chunks:
        features = extraction.features[chunk.id]
        values = {name: value.value for name, value in features.values.items()}
        print(
            json.dumps(
                {"chunk": chunk.location, "kind": chunk.kind, "extractor": features.extractor, **values}
            )
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format="slint: %(message)s")
    try:
        match args.command:
            case "compile":
                return run_compile(args)
            case "check":
                return run_check(args)
            case "rules":
                return run_rules(args)
            case "features":
                return run_features(args)
    except SlintError as error:
        print(f"slint: {error}", file=sys.stderr)
        return 2
    return 2
