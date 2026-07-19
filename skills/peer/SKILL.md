---
name: peer
description: |
  Agent-routing utility (`peer` bash tool): role-aware external tester, implementer, and reviewer dispatch plus orchestrator-native route discovery through a canonical model registry, working-directory control, idle-stall watchdog, and reviewer fan-out. Use from implement, review, continue, or loop pipelines — call `peer` or its positional harness form instead of `codex exec` or `pi` directly.
metadata:
  type: generic
---

# peer

`peer` ships at `skills/peer/scripts/peer`. It is the sanctioned way for skills to invoke
external agents; never call `codex exec` or `pi` directly.

**Install:** `mise run install-peer` symlinks the script to `~/.local/bin/peer`
(idempotent; re-run after pulls).

## Harnesses and roles

- **codex** — OpenAI Codex CLI. For `--agent <role>`, `peer` reads
  `agents/<role>.toml` from the target working tree and supplies its
  `developer_instructions` as Codex configuration.
- **pi** — Pi CLI with a provider selected by the registry. For `--agent <role>`, `peer`
  strips the frontmatter from the target working tree's `agents/<role>.md` and appends
  the remaining body to Pi's system prompt.
- **claude** — Claude Code CLI in noninteractive print mode for external role execution. The
  explicit external aliases are `opus-cli` and `sonnet-cli`; the unqualified `opus` and
  `sonnet` aliases remain orchestrator-native. Claude CLI runs with no session
  persistence, `dontAsk`, an exact allowed-tool set, and the stripped matching
  `agents/<role>.md` body. Reviewer and legacy calls expose only `Read,Grep,Glob`;
  tester/implementer calls expose and authorize `Read,Grep,Glob,Bash,Edit,Write`.
- **Role source fallback** — Codex, Pi, and Claude first load the matching role definition
  from the target working tree. If it has no `agents/` directory, they use the definitions
  beside the installed peer source.
- **Orchestrator-native routes** — registry entries with `native: true` are discoverable
  through `peer list/get` but are never spawned by `peer`; fan-out skips them with a
  native-spawn notice. In a Codex-hosted implementation run, `codex-native` is dispatched
  through the native subagent API and inherits the current session's model and reasoning
  effort. Other hosts use their corresponding native subagent mechanism.

Supported roles are `tester`, `implementer`, and `reviewer`:

- `tester` and `implementer` are workspace-write roles, require exactly one external
  peer, and are never retried automatically after a stall or failure.
- `reviewer` is read-only, supports external fan-out, and retries once after a stall or
  empty result. Pi receives only read/search/list tools; it has no shell, edit, or write
  access.
- Omitting `--agent` preserves legacy prompt-only review behavior: read-only with one
  retry and no role file injected.

All harnesses have an idle watchdog because their streaming clients can stall without
self-aborting. The default hard cap is 600 seconds. Idle time auto-scales with prompt
length from a 120-second Codex base or 180-second Pi base; explicit `--idle` overrides it.
A Claude CLI run includes partial message events so active long generations continue to
refresh the watchdog; only its final result event is written as the report.
A report is accepted only after a zero harness exit without an idle kill or hard-cap
termination; partial output from failed or terminated runs is never successful.
Each harness runs in its own process session. Completion, failure, idle timeout, and hard
cap cleanup terminate the whole harness process group, including surviving children.

## Canonical model registry

`peer`'s compatibility-stable `reviewers.yaml` registry is the single source of truth for
peer identity, harness, provider, model, aliases, and default effort. Never hardcode model
strings in a dispatch. The current registry is injected live:

```!
peer list
```

Use `peer get <field> <id|alias>` for `id`, `model`, `harness`, `alias`, `effort`,
`native`, or `provider`.

## Fan-out interface

```bash
peer -C {workdir} -d {outdir} --agent reviewer \
  --peers {ids-or-aliases} --effort {reasoning} "{task_prompt}"

peer -C {workdir} -d {outdir} --agent tester \
  --peers {one-id-or-alias} --effort {reasoning} "{task_prompt}"

peer -C {workdir} -d {outdir} --agent reviewer \
  --peers {ids-or-aliases} --prompt-file {.peer/run/prompt.md}
```

Fan-out is the default action; `peer run ...` remains an alias.

- `-C` / `--cd` sets the agent working root (default: the caller's current directory).
- `-d` / `--out-dir` is required and receives one `{peer-id}.yaml` result per peer.
  Relative output directories are resolved beneath the working root.
- `--agent` selects and injects a role contract. Omit only for legacy prompt-only review.
- Supply exactly one prompt source: a positional prompt or `--prompt-file {file}`. Relative
  prompt-file paths resolve beneath the working root and must name a readable, non-empty
  regular file. The file form avoids command-line size limits end-to-end: fan-out forwards
  only its path, Codex and Claude CLI read it from stdin, and Pi uses its native `@file`
  input.
- `--peers` is a comma-separated list of IDs or aliases. Omit it to select every
  external registry entry. `--reviewers` remains an exact compatibility alias.
- `--effort` accepts `minimal|low|medium|high|xhigh|max|ultra`; omitted values come from
  the registry. Claude CLI supports only `low|medium|high|xhigh|max`; Pi on providers
  without configurable thinking ignores the value.
- `--idle {seconds}` and `--cap {seconds}` override watchdog timing.

Stdout is a TSV manifest, one row per external peer:

```
{peer-id}  ok       {outdir}/{peer-id}.yaml
{peer-id}  stalled  {outdir}/{peer-id}.yaml
```

The caller owns the task-specific report schema. Read every `ok` file and treat
`stalled`, `error`, and `auth` rows as partial or failed results. Exit status is `0` when
at least one result was produced, `1` when none was produced, and `2` for usage errors.

## Single-harness compatibility interface

```bash
peer codex -C {workdir} --agent implementer --effort high -o {outfile} "{task_prompt}"
peer pi -C {workdir} --agent reviewer -o {outfile} "{task_prompt}"
peer claude -C {workdir} --agent reviewer --model opus --effort high \
  -o {outfile} --prompt-file {prompt_file}
peer claude -C {workdir} --agent tester --model sonnet --effort high \
  -o {outfile} "{task_prompt}"
```

The positional `peer codex|pi|claude` forms remain available for single-agent and legacy
callers. Registry-driven callers should not pass a model directly, though `--model` and
`--provider` remain supported for fan-out internals and compatibility. Exit status is
`0` for a non-empty result, `2` for usage, `3` for auth/availability, and `124` after the
role's allowed attempts produce no clean result. Relative `-o` paths are resolved beneath
the working root.

## Dispatch contract for skills

Resolve routing before dispatch. Send native aliases through the host orchestrator's
native subagent API with the matching `tester`, `implementer`, or `reviewer` role. In
Codex, `codex-native` inherits the session model and reasoning effort. Send external
aliases through one `peer` invocation using the same role and task prompt. Composition
belongs to the caller; peer does not require a paired native spawn. Because Pi reviewers have no shell, reviewer
prompts must include any command-only context they need—especially a materialized diff,
requirements, and the required report schema. They can still inspect repository files
with read, search, find, and list tools.
