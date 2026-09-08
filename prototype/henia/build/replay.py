#!/usr/bin/env python3
"""Replay local Henia build commands; retain inputs, outputs, and exit codes."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).parent / "fixtures/skills/probe/SKILL.md"
RUN = ROOT / ".henia/evidence/build" / time.strftime("%Y%m%d-%H%M%S")
RUN.mkdir(parents=True)
BIN = shutil.which("henia")
ENV = dict(os.environ, HOME=str(RUN / "home"))
Path(ENV["HOME"]).mkdir()
BASE = FIXTURE.read_text()
SIMPLE = "---\nname: probe\ndescription: Build probe.\n---\nBody.\n"
PROFILE = '[harness.claude]\nprofile="claude"\n'
records = []


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def prepare(name, config=PROFILE, body=SIMPLE):
    case = RUN / name
    put(case / "henia.toml", config)
    put(case / "source/skills/probe/SKILL.md", body)
    return case


def run(case, expected="success", args=None, env=None, output=True):
    command = [BIN, "build", str(case / "source"), "--config", str(case / "henia.toml")]
    if output:
        command += ["--output", str(case / "out")]
    command += args or []
    active_env = env or ENV
    result = subprocess.run(command, cwd=case, env=active_env, text=True, capture_output=True)
    put(case / "stdout.log", result.stdout)
    put(case / "stderr.log", result.stderr)
    reproduction = "cd " + shlex.quote(str(case)) + " && HOME=" + shlex.quote(active_env["HOME"]) + " " + shlex.join(command)
    put(case / "command.sh", reproduction + "\n")
    files = sorted(str(p.relative_to(case)) for p in (case / "out").rglob("*") if p.is_file())
    records.append(dict(case=case.name, expected=expected, exit=result.returncode, files=files, command=reproduction))
    print(f"{case.name}: exit={result.returncode} files={len(files)} expected={expected}")
    return case


profiles = ["claude", "codex", "opencode", "gemini", "github", "cursor", "chatgpt", "claude-upload", "agentskills"]
for profile in profiles:
    for fmt in ["xml", "directives", "markdown"]:
        config = f'[harness.{profile}]\nprofile="{profile}"\nformat="{fmt}"\n[harness.{profile}.variables]\npriority="harness"\n'
        case = prepare(f"matrix-{profile}-{fmt}", config, BASE)
        put(case / "source/skills/probe/reference/data.txt", "verbatim {{.priority}} :badge[resource]\n")
        script = put(case / "source/skills/probe/scripts/check", "#!/bin/sh\nprintf 'resource-ok\\n'\n")
        script.chmod(0o751)
        run(case)

run(prepare("defaults-all", "", SIMPLE))
run(prepare("select-two", "", SIMPLE), args=["--harness", "claude,codex"])
run(prepare("unknown-harness"), "failure", args=["--harness", "missing"])
run(prepare("canonical-precedence", PROFILE, BASE))
run(prepare("frontmatter-precedence", PROFILE, BASE.replace("    priority: canonical\n", "")))
run(prepare("missing-template", PROFILE, SIMPLE + "Missing={{.absent}}.\n"), "missing-key diagnostic desired")
run(prepare("invalid-template", PROFILE, SIMPLE + "{{if}}\n"), "failure")
run(prepare("template-code", PROFILE, SIMPLE + '```text\n{{.name}}\n```\n'), "templates expand before code parsing")
run(prepare("leaf-directive", PROFILE, SIMPLE + "\n::note{tone=high}\n"), "deferred; remains literal")
run(prepare("unclosed-directive", PROFILE, SIMPLE + "\n:::note\nBody\n"), "failure")
refs = PROFILE + '''[harness.claude.references.command]
output="command:{{.Name}}"
[harness.claude.references.agent]
output="agent:{{.Name}}"
[harness.claude.references.file]
output="[{{.Name}}](resource/{{.Name}})"
'''
run(prepare("all-references", refs, BASE))
run(prepare("invalid-reference-template", PROFILE + '[harness.claude.references.skill]\noutput="{{if}}"\n', SIMPLE + '`$probe`\n'), "failure desired")
run(prepare("reference-code", PROFILE, SIMPLE + '```text\n`$probe`\n```\n\n\\`$probe\\`\n'), "code literal preserved desired")

native = '''---
name: probe
description: Native override probe.
model_tier: strong
tools: [read, bash]
user_invocable: true
henia:
  auto_invoke: true
  targets:
    claude:
      auto_invoke: false
      user_invocable: null
      frontmatter:
        model: native-model
        license: null
        argument-hint: "[path]"
    codex:
      auto_invoke: false
      openai:
        interface:
          display_name: Probe
          short_description: Compile a local fixture
          default_prompt: Use $probe.
        policy:
          allow_implicit_invocation: true
        dependencies:
          tools:
            - type: mcp
              value: local
license: MIT
---
Native body.
'''
run(prepare("native-overrides", '[harness.claude]\nprofile="claude"\n[harness.codex]\nprofile="codex"\n', native))
run(prepare("strict-warning", PROFILE + "strict=true\n", BASE), "failure")
run(prepare("canonical-type", PROFILE, SIMPLE.replace("description: Build probe.", "description: 42")), "failure")
run(prepare("native-type", PROFILE, native.replace("model: native-model", "model: false")), "failure")
run(prepare("openai-type", '[harness.codex]\nprofile="codex"\n', native.replace("display_name: Probe", "display_name: false")), "failure")
run(prepare("tool-scalar", PROFILE, SIMPLE.replace("description: Build probe.", 'description: Build probe.\ntools: "Bash(git diff *)"')))
run(prepare("model-missing", PROFILE, SIMPLE.replace("description: Build probe.", "description: Build probe.\nmodel_tier: absent")), "failure")
run(prepare("alias-conflict", PROFILE, SIMPLE.replace("description: Build probe.", 'description: Build probe.\nargument_hint: first\nargument-hint: second')), "failure")

custom = '''fields=["name","description","metadata","automatic","renamed","count","seen","retained"]
controls=["auto_invoke"]
consume=["source","checks"]
[aliases]
label="renamed"
[computed]
automatic='settings.auto_invoke'
count='len(input.checks)'
seen='input.label'
retained='nil'
[files.json]
path="skills/{name}/manifest.json"
format="json"
value='{name: require(input.name, "name required"), count: len(input.checks), merged: merge({a: [1], enabled: true}, {a: [2], enabled: false}), path: ctx.path, variable: ctx.variables.flag, native: native.frontmatter.renamed}'
[files.yaml]
path="skills/{name}/extra.yaml"
format="yaml"
value='{name: input.name, enabled: false}'
[files.text]
path="skills/{name}/extra.txt"
format="text"
value='"text:" + input.name'
[files.nil]
path="skills/{name}/nil.txt"
format="text"
value='nil'
[files.empty]
path="skills/{name}/empty.json"
format="json"
value='{}'
'''
custom_body = '''---
name: probe
description: Custom profile probe.
source: raw
label: alias-value
retained: keep-me
checks: [one, two]
henia:
  auto_invoke: false
  targets:
    custom:
      frontmatter:
        renamed: native-value
---
Custom body.
'''
custom_config = '''[harness.custom]
profile="custom"
[harness.custom.variables]
flag="project"
[harness.custom.keys]
source="label"
[harness.custom.values.label]
raw="mapped"
'''
# Keep alias input unambiguous; legacy key mapping feeds alias/computation.
custom_body = custom_body.replace("label: alias-value\n", "")
def custom_case(name, transform=custom, body=custom_body):
    case = prepare(name, custom_config, body)
    put(case / ".henia/harnesses/custom/transform.toml", transform)
    return case
run(custom_case("custom-profile"))
for name, old, new in [
    ("expr-parse", "len(input.checks)", "len("),
    ("expr-runtime", "len(input.checks)", 'require(nil, "required probe")'),
    ("sidecar-type", "'\"text:\" + input.name'", "'42'"),
    ("sidecar-traversal", "skills/{name}/extra.txt", "../escape.txt"),
    ("sidecar-absolute", "skills/{name}/extra.txt", "/escape.txt"),
    ("sidecar-backslash", "skills/{name}/extra.txt", "skills\\\\escape.txt"),
    ("sidecar-main-collision", "skills/{name}/extra.txt", "skills/{name}/SKILL.md"),
    ("sidecar-file-directory", "skills/{name}/extra.txt", "skills/{name}/manifest.json/child"),
    ("sidecar-format", 'format="text"', 'format="binary"'),
]:
    run(custom_case(name, custom.replace(old, new)), "failure")
case = custom_case("sidecar-shared-collision", custom.replace("skills/{name}/manifest.json", "shared.json"))
put(case / "source/skills/second/SKILL.md", custom_body.replace("name: probe", "name: second"))
run(case, "failure")
case = prepare("sidecar-resource-collision", '[harness.codex]\nprofile="codex"\n', native)
put(case / "source/skills/probe/agents/openai.yaml", "source: sidecar\n")
run(case, "failure")
run(prepare("missing-profile", '[harness.custom]\nprofile="missing"\n'), "failure")

legacy = '''artifacts=["skills","commands","agents"]
[harness.legacy]
structure="flat"
format="directives"
generate_commands_from_skills=true
[harness.legacy.keys]
model_tier="model"
[harness.legacy.values.model]
strong="mapped-model"
[harness.legacy.artifact_mappings.agents.keys]
description="agent-description"
'''
case = prepare("legacy-flat", legacy, SIMPLE.replace("description: Build probe.", "description: Build probe.\nmodel_tier: strong"))
put(case / "source/agents/helper.md", "---\ndescription: Agent probe.\n---\nAgent body.\n")
put(case / "source/commands/launch.md", "---\ndescription: Command probe.\n---\nCommand body.\n")
put(case / "source/skills/probe/reference/data.txt", "resource\n")
run(case, "flat three types, generated command and per-artifact mapping requested")
run(prepare("generated-command", legacy), "skill plus generated command requested")
run(prepare("profile-flat", PROFILE + 'structure="flat"\n'), "failure")

case = prepare("merge-layers", PROFILE + 'strict=false\ninclude=["probe"]\n[harness.claude.variables]\npriority="project"\n', BASE)
home = case / "home"
put(home / ".config/henia/henia.toml", PROFILE + 'strict=true\ninclude=["second"]\n[harness.claude.variables]\npriority="user"\n')
put(case / "source/skills/second/SKILL.md", SIMPLE.replace("name: probe", "name: second"))
run(case, env=dict(ENV, HOME=str(home)))
case = custom_case("profile-layer-merge")
home = case / "home"
put(home / ".config/henia/harnesses/custom/transform.toml", 'fields=["from-user"]\n[computed]\n"from-user"="true"\n')
run(case, env=dict(ENV, HOME=str(home)))
run(prepare("toml-null", PROFILE + 'strict=null\n'), "failure; TOML has no null")
for name, filters in [("include-exclude", 'include=["probe","second"]\nexclude=["second"]\n'), ("include-glob", 'include=["pro*"]\n'), ("exclude-all", 'exclude=["probe","second"]\n')]:
    case = prepare(name, PROFILE + filters)
    put(case / "source/skills/second/SKILL.md", SIMPLE.replace("name: probe", "name: second"))
    run(case, "success" if name == "include-exclude" else "failure; no artifacts")
run(prepare("configured-output", '[build]\noutput="configured/out"\n' + PROFILE), output=False)
run(prepare("cli-relative-output", '[build]\noutput="unused"\n' + PROFILE), output=False, args=["--output", "relative/out"])
run(prepare("unknown-option", PROFILE + 'unknown=true\n'), "failure")
run(prepare("sources-setting", '[sources]\nlocal="."\n' + PROFILE), "failure; Phora boundary")
run(prepare("deployment-setting", PROFILE + 'path="install"\n'), "failure; Phora boundary")

case = prepare("resource-symlink")
put(case / "outside/resource.txt", "outside\n")
(case / "source/skills/probe/link").symlink_to(case / "outside/resource.txt")
run(case, "failure")
case = prepare("resource-directory-symlink")
(case / "source/skills/probe/link").symlink_to(case / "source/skills/probe", target_is_directory=True)
run(case, "failure")
case = prepare("output-symlink-escape")
(case / "outside").mkdir()
(case / "out/claude/skills").mkdir(parents=True)
(case / "out/claude/skills/probe").symlink_to(case / "outside", target_is_directory=True)
run(case, "failure")
case = prepare("output-symlink-internal")
(case / "out/claude/inside").mkdir(parents=True)
(case / "out/claude/skills").mkdir(parents=True)
(case / "out/claude/skills/probe").symlink_to(case / "out/claude/inside", target_is_directory=True)
run(case)
case = prepare("output-source-alias")
(case / "out/claude").mkdir(parents=True)
(case / "out/claude/skills").symlink_to(case / "source/skills", target_is_directory=True)
run(case, "failure")
case = prepare("harness-root-symlink")
(case / "out").mkdir()
(case / "outside").mkdir()
(case / "out/claude").symlink_to(case / "outside", target_is_directory=True)
run(case, "harness root is the resolved confinement boundary")
case = prepare("source-main-symlink")
put(case / "outside/SKILL.md", SIMPLE)
main = case / "source/skills/probe/SKILL.md"
main.rename(case / "original-main.md")
main.symlink_to(case / "outside/SKILL.md")
run(case, "observe source main symlink handling")
case = prepare("preflight-all-or-none", '[harness.claude]\nprofile="claude"\n[harness.codex]\nprofile="codex"\n')
put(case / "source/skills/broken/SKILL.md", SIMPLE.replace("name: probe", "name: broken") + "{{if}}\n")
run(case, "failure with no writes")
case = prepare("write-partial")
put(case / "source/skills/zeta/SKILL.md", SIMPLE.replace("name: probe", "name: zeta"))
(case / "out/claude/skills/zeta/SKILL.md").mkdir(parents=True)
run(case, "failure with partial output")
case = prepare("write-permission")
(case / "out/claude").mkdir(parents=True)
(case / "out/claude").chmod(0o555)
try:
    run(case, "failure")
finally:
    (case / "out/claude").chmod(0o755)
case = prepare("stale-rebuild")
put(case / "out/claude/skills/stale/SKILL.md", "stale marker\n")
put(case / "out/claude/skills/probe/SKILL.md", "old generated content\n")
run(case, "overwrites generated, retains stale")
case = prepare("resource-mode-rebuild")
resource = put(case / "source/skills/probe/script", "#!/bin/sh\ntrue\n")
resource.chmod(0o755)
existing = put(case / "out/claude/skills/probe/script", "old\n")
existing.chmod(0o644)
run(case, "executable resource mode retained desired")

reference_line = '`$probe` `/launch` `@helper` `#reference/data.txt` `!read` `!unknown`\n'
run(prepare("references-isolated", refs, SIMPLE + reference_line))
run(prepare("references-after-fence", refs, SIMPLE + '```text\nliteral\n```\n' + reference_line), "references outside fence rewritten desired")
run(prepare("references-in-tilde-fence", refs, SIMPLE + '~~~text\n' + reference_line + '~~~\n'), "code literal preserved desired")
run(prepare("references-indented-code", refs, SIMPLE + '\n    `$probe`\n'), "code literal preserved desired")
run(prepare("references-escaped-backticks", refs, SIMPLE + '\\`$probe`\n'), "escaped literal preserved desired")
run(prepare("tool-native-scalar", PROFILE, SIMPLE.replace("description: Build probe.", 'description: Build probe.\nallowed_tools: "Bash(git diff *)"')))
run(prepare("tool-native-exact", PROFILE, SIMPLE.replace("description: Build probe.", 'description: Build probe.\nallowed_tools: read')))
run(prepare("template-false-branch", PROFILE, SIMPLE + '{{if .absent}}yes{{else}}no{{end}}\n'))
run(prepare("nested-template-array", PROFILE, SIMPLE.replace("description: Build probe.", 'description: Build probe.\nhenia:\n  targets:\n    claude:\n      frontmatter:\n        paths: ["{{.name}}/one", "{{.name}}/two"]')))
markup = r'''\n:outer[Use :inner[nested]{#inner .one .two}]{title="Use \"quotes\" & <tags>"}

:x[y]{a="line\nnext\tcolumn"}

> :::quote
> text
> :::

- :::list
  text
  :::

    :::indented-literal

:::outer
```
:::
```
:::
'''.replace(r'\n:outer', '\n:outer', 1)
for fmt in ["xml", "directives", "markdown"]:
    run(prepare("markup-contexts-" + fmt, PROFILE + f'format="{fmt}"\n', SIMPLE + markup))
for name, body in [("attribute-duplicate", ':x[y]{a=1 a=2}'), ("attribute-malformed", ':x[y]{a=}'), ("inline-unclosed", ':x[unclosed')]:
    run(prepare(name, PROFILE, SIMPLE + '\n' + body + '\n'), "failure")
case = prepare("resource-empty-directory")
(case / "source/skills/probe/empty").mkdir()
run(case, "observe empty resource directory retention")
case = prepare("resource-hidden")
put(case / "source/skills/probe/.hidden", "hidden resource\n")
put(case / "source/skills/probe/reference/.hidden", "nested hidden resource\n")
run(case, "observe hidden resource discovery")
case = prepare("source-directory-symlink")
(case / "source/skills/probe").rename(case / "outside")
(case / "source/skills/probe").symlink_to(case / "outside", target_is_directory=True)
run(case, "observe directory source symlink discovery")
case = prepare("source-direct-overwrite", '[harness.source]\nprofile="claude"\n')
run(case, "failure", args=["--output", str(case)])
case = prepare("source-inside-output")
run(case, "failure", args=["--output", str(case / "source/skills/probe/output")])
case = prepare("duplicate-artifact")
put(case / "source/skills/probe.md", SIMPLE)
run(case, "failure; duplicate main destination")
run(prepare("invalid-harness-name", '[harness."../escape"]\nformat="xml"\n'), "failure")
run(prepare("invalid-format", PROFILE + 'format="html"\n'), "failure")
run(prepare("unknown-profile-key", '[harness.custom]\nprofile="custom"\n'), "failure; missing profile")
case = custom_case("native-null-merge", custom, custom_body.replace('renamed: native-value', 'renamed: null'))
run(case)

put(RUN / "results.json", json.dumps(records, indent=2) + "\n")
put(RUN / "provenance.json", json.dumps(dict(binary=BIN, sha256=hashlib.sha256(Path(BIN).read_bytes()).hexdigest(), fixture_sha256=hashlib.sha256(FIXTURE.read_bytes()).hexdigest()), indent=2) + "\n")
print(f"Evidence: {RUN}")
