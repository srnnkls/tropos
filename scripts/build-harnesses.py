#!/usr/bin/env python3
"""Compile and validate a complete bundle before replacing generated artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib


HARNESSES = ("claude", "codex", "pi", "omp")
LANGUAGES = ("bash", "elisp", "go", "python", "rust", "zig")


def yaml(value: dict) -> str:
    return subprocess.check_output(
        ["yq", "-P", "-p=json", "-o=yaml", ".", "-"],
        input=json.dumps(value),
        text=True,
    )


def copy_guides(source: Path, destination: Path) -> tuple[dict[str, str], str]:
    """Read Loqui's committed dependency surface; Phora installs that same pin."""
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source, text=True
    ).strip()
    tree = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            revision,
            "README.md",
            "languages",
            "resources",
        ],
        cwd=source,
        text=True,
    )
    hashes = {}
    for relative in tree.splitlines():
        data = subprocess.check_output(
            ["git", "show", f"{revision}:{relative}"], cwd=source
        )
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
        hashes[relative] = hashlib.sha256(data).hexdigest()
    for language in LANGUAGES:
        if f"languages/{language}/README.md" not in hashes:
            raise ValueError(
                f"Loqui is missing languages/{language}/README.md at {revision}"
            )
    return hashes, revision


def snapshot_repository(path: Path) -> str:
    # Content-addressed local packaging: identical input trees keep the same pin.
    env = dict(
        os.environ,
        GIT_AUTHOR_DATE="2000-01-01T00:00:00Z",
        GIT_COMMITTER_DATE="2000-01-01T00:00:00Z",
    )
    git = [
        "git",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "user.name=Tropos package",
        "-c",
        "user.email=package@example.invalid",
    ]
    for args in (
        ["init", "-q", "-b", "main", "--template="],
        ["add", "--all"],
        ["commit", "-qm", "Canonical dependency snapshot"],
    ):
        subprocess.run([*git, *args], cwd=path, env=env, check=True)
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=path, text=True
    ).strip()


def toml_value(value: object) -> str:
    if isinstance(value, dict):
        return (
            "{ "
            + ", ".join(
                f"{json.dumps(key)} = {toml_value(item)}" for key, item in value.items()
            )
            + " }"
        )
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    return json.dumps(value)


def build(root: Path, loqui: Path) -> None:
    generated = root / ".henia"
    generated.mkdir(exist_ok=True)
    binary = generated / "bin/henia"
    executable = str(binary) if binary.is_file() else shutil.which("henia")
    if executable is None:
        raise ValueError(
            "Build Henia first with mise run prototype:build, or put henia on PATH"
        )
    with tempfile.TemporaryDirectory(prefix="compile-", dir=generated) as temporary:
        temporary = Path(temporary)
        stage = temporary / "build"
        subprocess.run(
            [
                executable,
                "--config",
                str(root / "henia.toml"),
                "build",
                str(root),
                "--output",
                str(stage),
            ],
            cwd=root,
            check=True,
        )
        guides = temporary / "loqui"
        if not loqui.is_dir():
            raise ValueError(f"Loqui is missing: {loqui}")
        hashes, revision = copy_guides(loqui, guides)
        for harness in HARNESSES:
            output = stage / harness
            shutil.copytree(root / "instructions", output / "instructions")
            instructions = (output / "instructions/AGENTS.md").read_text()
            native_name = "CLAUDE.md" if harness == "claude" else "AGENTS.md"
            (output / native_name).write_text(instructions.replace("](../", "]("))
            agents = output / "agents"
            agents.mkdir()
            for role in ("tester", "implementer", "reviewer"):
                source = root / "agents" / f"{role}.md"
                metadata = json.loads(
                    subprocess.check_output(
                        ["yq", "--front-matter=extract", "-o=json", ".", str(source)],
                        text=True,
                    )
                )
                if harness == "claude":
                    for key in ("tools", "skills"):
                        if isinstance(metadata.get(key), str):
                            metadata[key] = [
                                item.strip() for item in metadata[key].split(",")
                            ]
                else:
                    metadata = {key: metadata[key] for key in ("name", "description")}
                body = source.read_text().split("---", 2)[2].lstrip("\n")
                (agents / f"{role}.md").write_text(
                    "---\n" + yaml(metadata) + "---\n\n" + body
                )
            subprocess.run(
                [executable, "lint", str(output / "skills")], cwd=root, check=True
            )
            (output / "loqui-manifest.json").write_text(
                json.dumps(hashes, sort_keys=True, indent=2) + "\n"
            )
            # Lint canonical Tropos artifacts; external reference repositories have
            # their own authoring dialects and are verified by their manifest.
        subprocess.run(
            [
                "python3",
                str(root / "tests/scrut/check-artifacts.py"),
                str(root),
                "--build",
                str(stage),
            ],
            check=True,
        )
        # The consumer builds the advertised canonical source; every compiled ref
        # carries Tropos's own dependency manifest so transitive=True is sufficient.
        advertised = tomllib.loads((root / "phora.toml").read_text())
        advertised["sources"].pop("tropos")
        dependency = advertised["sources"]["loqui"]
        dependency.pop("branch", None)
        dependency["rev"] = revision
        dependency["git"] = os.environ.get("TROPOS_LOQUI_REMOTE", dependency["git"])
        manifest = (
            "\n".join(
                f"{key} = {toml_value(value)}" for key, value in advertised.items()
            )
            + "\n"
        )
        packages = temporary / "packages"
        package = packages / "tropos"
        package.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "--bare", "-q", "--template=", str(package)], check=True
        )
        for harness in HARNESSES:
            output = stage / harness
            (output / "phora.toml").write_text(manifest)
            snapshot_repository(output)
            subprocess.run(
                ["git", "fetch", "-q", str(output), f"HEAD:refs/heads/{harness}"],
                cwd=package,
                check=True,
            )
        subprocess.run(
            ["git", "symbolic-ref", "HEAD", "refs/heads/claude"],
            cwd=package,
            check=True,
        )
        installed = []
        try:
            for name, candidate in (("build", stage), ("packages", packages)):
                published = generated / name
                if published.is_symlink():
                    raise ValueError(
                        f"Generated output must be a real directory: {published}"
                    )
                backup = temporary / ("previous-" + name)
                if published.exists():
                    published.rename(backup)
                installed.append((published, backup))
                candidate.rename(published)
        except (OSError, ValueError):
            for published, backup in reversed(installed):
                if published.exists():
                    shutil.rmtree(published)
                if backup.exists():
                    backup.rename(published)
            raise
    print("Published one Tropos source with four harness refs and its Loqui dependency")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--loqui",
        type=Path,
        default=Path(
            os.environ.get("TROPOS_LOQUI_SOURCE", str(Path.home() / "projects/loqui"))
        ),
    )
    args = parser.parse_args()
    build(Path(__file__).resolve().parents[1], args.loqui.expanduser().resolve())


if __name__ == "__main__":
    main()
