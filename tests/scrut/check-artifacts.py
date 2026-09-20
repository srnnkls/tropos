#!/usr/bin/env python3
"""Check this prototype's compiled artifacts against its harness contracts."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


COMMON_FIELDS = {"name", "description", "metadata"}
CLAUDE_FIELDS = COMMON_FIELDS | {
    "argument-hint",
    "allowed-tools",
    "disable-model-invocation",
    "context",
    "hooks",
}


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def yaml(path, frontmatter=False):
    args = ["yq", "-o=json", "-p=yaml"]
    if frontmatter:
        args += ["--front-matter=extract"]
    return json.loads(subprocess.check_output([*args, ".", str(path)], text=True))


def snapshot(root):
    result = {}
    for directory in (
        "skills",
        "agents",
        "instructions",
        ".henia/build",
        ".claude",
        ".agents",
        ".pi",
        ".omp",
    ):
        for path in sorted((root / directory).rglob("*")):
            if path.is_file() and ".git" not in path.parts:
                result[str(path.relative_to(root))] = [
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    path.stat().st_mode & 0o777,
                    os.readlink(path) if path.is_symlink() else None,
                ]
    return result


def check(root, build=None):
    skills = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
    require(bool(skills), "canonical skill inventory is empty")
    for harness, directory in (
        ("claude", ".claude"),
        ("codex", ".agents"),
        ("pi", ".pi"),
        ("omp", ".omp"),
    ):
        target = build / harness if build else root / directory
        mains = sorted((target / "skills").glob("*/SKILL.md"))
        require(
            {path.parent.name for path in mains} == skills,
            f"{harness}: expected the complete canonical skill inventory in {directory}/skills",
        )
        for path in mains:
            name = path.parent.name
            fm = yaml(path, frontmatter=True)
            require(fm.get("name") == name, f"{path}: name must match directory")
            require(
                isinstance(fm.get("description"), str)
                and 0 < len(fm["description"]) <= 1024,
                f"{path}: invalid description",
            )
            fields = CLAUDE_FIELDS if harness == "claude" else COMMON_FIELDS
            if harness in {"pi", "omp"}:
                fields = COMMON_FIELDS | {"disable-model-invocation"}
            require(
                set(fm) <= fields, f"{path}: unexpected frontmatter: {set(fm) - fields}"
            )
            require(
                all(
                    isinstance(value, str) for value in fm.get("metadata", {}).values()
                ),
                f"{path}: metadata must have string values",
            )
            body = path.read_text().split("---", 2)[2]
            require(
                "{{" not in body and "<no value>" not in body,
                f"{path}: unexpanded template",
            )
            if build is None:
                compiled = (
                    root / ".henia/build" / harness / "skills" / name / "SKILL.md"
                )
                require(
                    not path.is_symlink()
                    and path.read_bytes() == compiled.read_bytes(),
                    f"{path}: expected the committed compiled artifact",
                )
            canonical = yaml(root / "skills" / name / "SKILL.md", frontmatter=True)
            require(
                set(canonical) <= COMMON_FIELDS | {"license", "compatibility", "henia"},
                f"{name}: native metadata outside henia.targets",
            )
            if canonical.get("henia", {}).get("variables", {}).get("context_commands"):
                if harness == "claude":
                    require(
                        "## Pre-loaded Context" in body and "!`" in body,
                        f"{path}: missing Claude dynamic context",
                    )
                else:
                    require(
                        "## Runtime Context" in body
                        and "!`" not in body
                        and "```bash" in body,
                        f"{path}: harness must receive shell instructions",
                    )
            if name in {"code", "implement"}:
                directive = (
                    '<instruction priority="high">'
                    if harness == "claude"
                    else ':::instruction{priority="high"}'
                )
                require(directive in body, f"{path}: incorrect directive rendering")
            if name in {"code", "test"}:
                reference = "`/implement`" if harness == "claude" else "`$implement`"
                if harness in {"pi", "omp"}:
                    reference = "`/skill:implement`"
                require(reference in body, f"{path}: incorrect skill invocation")
            if canonical.get("henia", {}).get("auto_invoke") is False and harness in {
                "claude",
                "pi",
                "omp",
            }:
                require(
                    fm.get("disable-model-invocation") is True,
                    f"{path}: explicit invocation required",
                )
            if harness == "codex":
                sidecar = yaml(path.parent / "agents/openai.yaml")
                ui = sidecar["interface"]
                require(
                    isinstance(ui["display_name"], str) and ui["display_name"],
                    f"{path}: missing display name",
                )
                require(
                    25 <= len(ui["short_description"]) <= 64,
                    f"{path}: invalid short description",
                )
                require(
                    f"${name}" in ui["default_prompt"],
                    f"{path}: missing explicit invocation in prompt",
                )
                if canonical.get("henia", {}).get("auto_invoke") is False:
                    require(
                        sidecar.get("policy", {}).get("allow_implicit_invocation")
                        is False,
                        f"{path}: explicit invocation required",
                    )
            for resource in (root / "skills" / name).rglob("*"):
                if resource.is_file() and resource.name != "SKILL.md":
                    deployed = path.parent / resource.relative_to(
                        root / "skills" / name
                    )
                    require(
                        deployed.is_file()
                        and deployed.read_bytes() == resource.read_bytes(),
                        f"{deployed}: missing or changed resource",
                    )
                    require(
                        bool(deployed.stat().st_mode & 0o111)
                        == bool(resource.stat().st_mode & 0o111),
                        f"{deployed}: executable mode differs from source",
                    )
        for role in ("tester", "implementer", "reviewer"):
            source = root / "agents" / f"{role}.md"
            deployed = target / "agents" / f"{role}.md"
            fm = yaml(deployed, frontmatter=True)
            require(fm["name"] == role, f"{deployed}: role name differs")
            if harness != "claude":
                require(
                    set(fm) == {"name", "description"},
                    f"{deployed}: Claude metadata leaked",
                )
            require(
                deployed.read_text().split("---", 2)[2]
                == source.read_text().split("---", 2)[2],
                f"{deployed}: role contract changed",
            )
        require(
            (target / "instructions/AGENTS.md").read_bytes()
            == (root / "instructions/AGENTS.md").read_bytes(),
            f"{target}: instructions differ",
        )
        native = target / ("CLAUDE.md" if harness == "claude" else "AGENTS.md")
        require(
            native.read_text()
            == (root / "instructions/AGENTS.md").read_text().replace("](../", "]("),
            f"{native}: native instructions differ",
        )
        manifest = json.loads((target / "loqui-manifest.json").read_text())
        guides = target / "skills/loqui/reference/loqui"
        if build is None:
            require(
                set(manifest)
                == {
                    str(p.relative_to(guides)) for p in guides.rglob("*") if p.is_file()
                },
                f"{guides}: dependency inventory differs",
            )
            for relative, digest in manifest.items():
                require(
                    hashlib.sha256((guides / relative).read_bytes()).hexdigest()
                    == digest,
                    f"{guides / relative}: dependency bytes differ",
                )
            for language in ("bash", "elisp", "go", "python", "rust", "zig"):
                require(
                    (guides / "languages" / language / "README.md").is_file(),
                    f"{guides}: missing {language} guidance",
                )
        print(
            f"{harness}: {len(skills)} skills; metadata, body, resources and support OK"
        )


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    if "--snapshot" in sys.argv[2:]:
        print(json.dumps(snapshot(root), sort_keys=True, indent=2))
    else:
        check(
            root,
            Path(sys.argv[sys.argv.index("--build") + 1]).resolve()
            if "--build" in sys.argv
            else None,
        )
