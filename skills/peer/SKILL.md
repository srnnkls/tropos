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

## Report layout — `.peer/`

`.peer/` holds every artifact a peer dispatch produces, for every caller. This section is its
only specification; skills reference it rather than restating a shape.

```
.peer/<subject>/<run>/<stage>/
```

Exactly three segments below `.peer/` — never two, never four. A dispatch that needs to
distinguish itself from a sibling extends the `<stage>` name with a `-`; it does not open a
new directory level.

| Segment | Is | Examples |
|---|---|---|
| `<subject>` | what the work is about | `auth-system` (scope), `issue-745`, `pr-312`, `working`, `direct` |
| `<run>` | one dispatch session, minted once per gate round | `20260820T101112Z-a1b2c3` |
| `<stage>` | the specific dispatch within that run | `b3-tester-T003`, `b3-test-review`, `final-review-arch`, `issue-review`, `review` |

Each leaf directory holds the materialized `prompt.md` and one `{peer-id}.yaml` per external
peer. Native reports are written alongside them by the orchestrator, so a run's evidence is
complete in one place.

Never assemble these paths by hand. `peer path` is the sanctioned constructor: it validates
every segment, creates the directory, and appends `.peer/` to the repository's `.gitignore`
when absent.

```bash
run=$(peer run-id)                                   # 20260820T101112Z-a1b2c3
dir=$(peer path auth-system b3-tester-T003 --run "$run")
# ... write $dir/prompt.md ...
peer -C "$workdir" -d "$dir" --agent tester --peers glm --prompt-file "$dir/prompt.md"
```

Omit `--run` and `peer path` mints one; pass the same `--run` to group every stage of a round
under a single session. `-C {dir}` roots the `.peer/` tree somewhere other than the current
directory.

`peer` rejects a non-conforming `-d` or `-o` path under any `.peer/` root with exit `2`, before
it creates anything or dispatches. A path outside `.peer/` is outside this convention and is
not checked. `peer-layout-test` covers the constructor and the rejections.

## Fan-out interface

```bash
peer -C {workdir} -d {outdir} --agent reviewer \
  --peers {ids-or-aliases} --effort {reasoning} "{task_prompt}"

peer -C {workdir} -d {outdir} --agent tester \
  --peers {one-id-or-alias} --effort {reasoning} "{task_prompt}"

peer -C {workdir} -d {outdir} --agent reviewer \
  --peers {ids-or-aliases} --prompt-file {outdir}/prompt.md
```

Fan-out is the default action; `peer run ...` remains an alias.

- `-C` / `--cd` sets the agent working root (default: the caller's current directory).
- `-d` / `--out-dir` is required and receives one `{peer-id}.yaml` result per peer. Relative
  output directories are resolved beneath the working root. Get it from `peer path` — see
  [Report layout](#report-layout--peer).
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
{peer-id}  ok         {outdir}/{peer-id}.yaml
{peer-id}  misconfig  {outdir}/{peer-id}.yaml
{peer-id}  blocked    {outdir}/{peer-id}.yaml
{peer-id}  stalled    {outdir}/{peer-id}.yaml
```

The caller owns the task-specific report schema. Read every `ok` file; every other status
means no report was produced and the file is empty. Exit status is `0` when at least one
result was produced, `1` when none was produced, and `2` for usage errors.

## Failure classification

A failed dispatch reports one status, and each names a different fix. Do not read a
`misconfig` row as a credential, timeout, or reachability problem.

| Status | Meaning | Exit | Fix |
|---|---|---|---|
| `misconfig` | the harness cannot serve this model or provider | 2 | correct `reviewers.yaml` |
| `blocked` | a peer in this run was denied an operation, so this row's cause is unverified | 2 or 3 | re-run unrestricted, then re-read the row |
| `auth` | the harness rejected its stored credentials | 3 | re-run that harness's login flow |
| `limit` | rate or quota limit | 4 | retry later |
| `stalled` | idle watchdog or hard cap fired | 124 | retry, or raise `--idle`/`--cap` |
| `error` | any other unclean exit | 124 | read the peer's stderr line |

Three properties make these statuses trustworthy:

- Classification reads only harness-emitted error records. Prompt text, tool output, and
  the agent's own report never reach the classifier, so reviewing authentication code
  cannot produce an `auth` row.
- Model and provider are checked against the harness before dispatch, so a registry
  mistake fails in seconds instead of consuming the full cap twice. The checks stay silent
  when the harness's model list is unavailable or stale, and a preflight that cannot
  enumerate the harness at all dispatches anyway rather than reporting `misconfig`: an
  unreadable catalog is evidence about the environment, never about `reviewers.yaml`.
- A fan-out's peers share one environment, so they share one blast radius. Once any of
  them is denied an operation, every sibling `misconfig` and `auth` row in that run is
  relabelled `blocked` — a restricted harness names a specific file or credential to fix,
  and that name is unearned. Only an unrestricted re-run can make one a finding again.

`peer-classify-test`, `peer-preflight-test`, and `peer-fanout-test` beside the script cover
these properties.

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
callers. Registry-driven callers should not pass a model directly, though `--model`, `--provider`,
and `--peer-id` remain supported for fan-out internals and compatibility. Exit status
follows the failure-classification table above: `0` for a non-empty result, `2` for usage
and misconfiguration, `3` for auth, `4` for a rate or quota limit, and `124` after the
role's allowed attempts produce no clean result. Only `stalled` and `error` are retried;
a misconfigured, unauthenticated, or rate-limited harness fails immediately. Relative `-o`
paths are resolved beneath the working root.

## Dispatch contract for skills

Resolve routing before dispatch. Send native aliases through the host orchestrator's
native subagent API with the matching `tester`, `implementer`, or `reviewer` role. In
Codex, `codex-native` inherits the session model and reasoning effort. Send external
aliases through one `peer` invocation using the same role and task prompt. Composition
belongs to the caller; peer does not require a paired native spawn.

Peer tells each agent its registry id, so a peer asked for a `reviewer_id` can state the
right one. Treat the result filename and manifest row as the authoritative provenance
regardless: they are assigned by peer, whereas a self-declared id is unverifiable. Do not
void a substantive report solely because its self-declared id is wrong. Because Pi reviewers have no shell, reviewer
prompts must include any command-only context they need—especially a materialized diff,
requirements, and the required report schema. They can still inspect repository files
with read, search, find, and list tools.

## Report triage

A peer report is evidence, not a verdict. The caller owns disposition and is the last
check before a finding becomes work. Manifest status describes dispatch, not content: an
`ok` row means a report exists, never that its findings hold.

Accept a finding only when it names a concrete failure mode checkable against the artifact
under review — an input that yields the wrong output, a check that cannot fire, a false
failure for a conformant implementation. Verify the load-bearing ones empirically before
they gate anything; a finding that survives only as prose is not yet a finding.

Disposition these as residual records or reject them with the evidence, without opening a
fix round:

- ever-narrower edge cases with no reachable input
- speculative hardening of a check that already has falsification evidence
- questions an earlier round or another peer already grounded
- the design restated as a defect

Report volume tracks reasoning effort, not defect density, and high-effort peers reliably
produce refinement spirals past the first round. Converge in one fix round unless a later
round surfaces a new verified failure mode; round count is a cost, not a quality signal.
Fan-out exists to get independent angles on the first round, not to accumulate rounds — a
finding's `found_by` count is agreement, not validity.

For multi-reviewer runs this bar is the triage step of
[review synthesis](../review/reference/synthesis.md), which owns the `residual` dispositions
and the rule that only triaged issues fail a gate.
