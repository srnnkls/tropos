#!/usr/bin/env python3
"""Check compiled Tropos artifacts against their harness contracts."""

import json
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


def check(root, build):
    canonical_root = root
    skills = {path.parent.name for path in (canonical_root / "skills").glob("*/SKILL.md") }
    require(bool(skills), "canonical skill inventory is empty")
    for harness in ("claude", "codex", "pi", "omp"):
        target = build / harness
        mains = sorted((target / "skills").glob("*/SKILL.md"))
        require(
            {path.parent.name for path in mains} == skills,
            f"{harness}: expected the complete canonical skill inventory",
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
            canonical = yaml(canonical_root / "skills" / name / "SKILL.md", frontmatter=True)
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
            for resource in (canonical_root / "skills" / name).rglob("*"):
                if resource.is_file() and resource.name != "SKILL.md":
                    deployed = path.parent / resource.relative_to(
                        canonical_root / "skills" / name
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
            source = canonical_root / "agents" / f"{role}.md"
            deployed = target / "agents" / f"{role}.md"
            fm = yaml(deployed, frontmatter=True)
            require(fm["name"] == role, f"{deployed}: role name differs")
            canonical_agent = yaml(source, frontmatter=True)
            expected_metadata = {key: canonical_agent[key] for key in ("name", "description")}
            if harness == "claude":
                expected_metadata |= canonical_agent["henia"]["targets"]["claude-agent"]["frontmatter"]
            require(fm == expected_metadata, f"{deployed}: agent metadata differs")
            require(
                deployed.read_text().split("---", 2)[2]
                == source.read_text().split("---", 2)[2],
                f"{deployed}: role contract changed",
            )
        require(
            (target / "instructions/AGENTS.md").read_bytes()
            == (canonical_root / "instructions/AGENTS.md").read_bytes(),
            f"{target}: instructions differ",
        )
        native = target / ("CLAUDE.md" if harness == "claude" else "AGENTS.md")
        require(
            native.read_text()
            == (canonical_root / "instructions/AGENTS.md").read_text().replace("](../", "]("),
            f"{native}: native instructions differ",
        )
        guides = target / "skills/loqui/reference/loqui"
        canonical_guides = canonical_root / "skills/loqui/reference/loqui"
        expected_guides = {str(p.relative_to(canonical_guides)) for p in canonical_guides.rglob("*") if p.is_file()}
        require(bool(expected_guides), "transitive Loqui input is missing")
        require(expected_guides == {str(p.relative_to(guides)) for p in guides.rglob("*") if p.is_file()}, f"{guides}: dependency inventory differs")
        for relative in expected_guides:
            require((guides / relative).read_bytes() == (canonical_guides / relative).read_bytes(), f"{guides / relative}: dependency bytes differ")
        for language in ("bash", "elisp", "go", "python", "rust", "zig"):
            require((guides / "languages" / language / "README.md").is_file(), f"{guides}: missing {language} guidance")
        print(
            f"{harness}: {len(skills)} skills; metadata, body, resources and support OK"
        )


if __name__ == "__main__":
    check(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
