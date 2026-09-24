---
name: peer
description: |
  Agent-routing utility (`peer` bash tool): role-aware external dispatch plus Claude Code native/proxy route discovery through a canonical model registry, working-directory control, idle-stall watchdog, and reviewer fan-out. Use from implement, review, continue, or loop pipelines — call `peer` or its positional harness form instead of `codex exec` or `pi` directly.
metadata:
  type: generic
henia:
  variables:
    context_commands:
      - label: Available peers
        command: peer list 2>/dev/null || true
      - label: Default reviewers
        command: peer defaults reviewers 2>/dev/null || true
      - label: Resolved routes
        command: peer route show -C . 2>/dev/null || true
      - label: Dispatch surface
        command: peer herdr 2>/dev/null || true
  targets:
    codex:
      openai:
        interface:
          display_name: Peer routing
          short_description: Resolve agent routes and dispatch external peers
          default_prompt: Use $peer to resolve routes and dispatch the selected peers.
---

<!-- Generated from skills/peer/SKILL.md by henia build; edit the canonical source. -->

## {{if eq .preload_context "true"}}Pre-loaded Context{{else}}Runtime Context{{end}}

{{.context_instruction}}

{{range .context_commands}}{{.label}}:
{{if eq $.preload_context "true"}}!`{{.command}}`{{else}}```bash
{{.command}}
```{{end}}

{{end}}
# peer

`peer` ships at `skills/peer/scripts/peer`.

Install: `mise run install-peer` links the runner, base roles, and current generated routes. Re-run it after role or registry changes.

## Harness and role loading

`peer list` and `peer get` render the current route ID, harness, provider, model, alias, effort, and independent native, proxy, and peer capabilities from the registry. `peer defaults reviewers` renders the default reviewer ensemble and each execution mechanism. The [routing contract](reference/routing.md) owns their interpretation.

For role dispatch, Codex, Pi, and Claude receive the same Markdown base-role body plus any harness-specific shim. `peer` resolves that body from the target working tree first and the installed source second. It also materializes fresh repository orientation before the harness starts; orientation failure blocks dispatch.

Runtime checks enforce the interface:

- tester and implementer calls select exactly one external peer and keep workspace write access;
- reviewer calls may fan out, run read-only, and require the platform sandbox when the harness cannot enforce read-only itself;
- failed, stalled, or partial harness output never becomes a successful report.

Omitting `--agent` preserves legacy prompt-only review behavior.

Every harness runs under an idle watchdog and hard cap. The defaults adapt to prompt size; `--idle` and `--cap` override them. Completion and failure terminate the whole harness process group, including surviving children.

## Registry and routing

The live registry and all host/native/external routing semantics are owned by [reference/routing.md](reference/routing.md). Load it when selecting, validating, or dispatching a route.

Run `peer --help` and `peer route --help` for the current command surface. Query facts with `peer list`, `peer get`, and `peer defaults reviewers`; inspect resolved status with `peer route show`; validate direct generated-role dispatch with `peer route check`.

Generated definitions are ignored local artifacts. Edit base roles or registry data, then run `peer route sync`; never edit generated files.

## Report layout — `.peer/`

`peer path` is the constructor and validator for report directories. Run `peer path --help` for the current shape and arguments.

```bash
run=$(peer run-id)
dir=$(peer path auth-system b3-tester-T003 --run "$run")
```

Pass the same run ID to group every stage of one gate round. Each returned directory holds the materialized `prompt.md`, external `{peer-id}.yaml` reports, and normalized native reports.

The command validates every segment, creates only the report directory, and never writes Git state. Dispatch rejects a nonconforming path under any `.peer/` root before creating files or starting a harness. `peer-layout-test` covers construction and rejection.

## Fan-out interface

Fan-out is the default action; `peer run` remains an alias. Run `peer --help` for the current flags, prompt forms, and path arguments. Construct `OUTDIR` with `peer path`.

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

## Herdr pane dispatch

Called from a live Herdr pane, a fan-out runs its peers as visible agent panes instead of headless child processes. `peer herdr` reports which surface a fan-out started right now would use: `HERDR_ENV` is inherited and outlives its pane, so it only selects the check — the live pane decides. One tab per round, labelled `peer-<subject>-<stage>` from the `.peer` report path; the first peer takes the tab's root pane and later peers split off it, alternating right and down. Each pane carries `peer` metadata — title, display agent, state label, and `peer`/`role`/`status` tokens — so the Herdr UI names what is running where.

The peer writes its own report: the pane agent is pointed at the prompt file and told to write `{peer-id}.yaml`, and peer waits for that file. A positional prompt is materialized beside the report first, since a pane agent reads its assignment from disk. Reviewer panes run behind the same read-only profile as headless reviewers, widened only by the stage directory the report goes in. A pane stopped at an approval or question dialog is reported, never answered.

A round closes its own tab. Before it does, every peer that wrote no report has its pane terminal saved beside the empty report as `{peer-id}.pane.log` — the only account of a peer that declined, stalled, or stopped at a dialog, and it outlives the pane. `PEER_HERDR_KEEP=1` keeps the tab instead, for answering a blocked peer by hand. `peer herdr clean` reaps whatever accumulated: every settled `peer-` tab in the live workspace, sparing tabs that still carry a working or blocked peer and tabs that are not peer rounds.

The manifest, statuses, and exit codes are identical to headless dispatch. `PEER_HERDR=0` forces headless inside a Herdr pane, and a failed `tab create` falls back to it automatically. `peer-herdr-test` covers pane dispatch against a stub Herdr CLI.

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

Run `peer --help` for the positional Codex, Pi, and Claude forms. They remain compatibility interfaces; registry-driven callers use the fan-out interface and [routing contract](reference/routing.md). Exit status follows the failure-classification table.

:::instruction{priority=high}
## Dispatch contract for skills

Resolve every selected mechanism through the canonical [routing contract](reference/routing.md). Composition belongs to the caller; peer never requires a paired native spawn.

Peer tells each agent its registry id, so a peer asked for a `reviewer_id` can state the
right one. Treat the result filename and manifest row as the authoritative provenance
regardless: they are assigned by peer, whereas a self-declared id is unverifiable. Do not
void a substantive report solely because its self-declared id is wrong. Because Pi reviewers have no shell, reviewer
prompts must include any command-only context they need—especially a materialized diff,
requirements, and the required report schema. They can still inspect repository files
with read, search, find, and list tools.
:::

## Report triage

An `ok` manifest row proves only that a report exists. Callers apply the canonical [finding bar](../review/reference/finding-bar.md) and [review synthesis](../review/reference/synthesis.md); peer does not maintain another admission, residual, or round policy.
