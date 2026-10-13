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

:::head{.context}



:::
# peer

Runner: `skills/peer/scripts/peer`, deployed by Phora to `~/.local/bin/peer`, reading the deployed skill's registry and helpers (`PEER_HOME` overrides). Commands: `peer --help`, `peer route --help`.

## Dispatch

- All harnesses get one base-role body plus shim, from the target working tree, else the installed source. Orientation failure blocks dispatch.
- Tester, implementer: exactly one external peer, workspace writable.
- Reviewer: may fan out; read-only, platform-sandboxed when the harness cannot enforce it.
- Failed, stalled, or partial output never becomes a successful report.
- No `--agent`: legacy prompt-only review.
- An idle watchdog and hard cap (prompt-sized; `--idle`, `--cap` override) bound every harness; exit kills its process group.
- Positional harness forms are compatibility only; registry-driven callers use fan-out.

## Report layout — `.peer/`

`peer path` constructs and validates report directories (`peer path --help`):

```bash
run=$(peer run-id)
dir=$(peer path auth-system b3-tester-T003 --run "$run")
```

Reuse one run ID across a gate round's stages. A directory holds `prompt.md`, external `{peer-id}.yaml` reports, and normalized native reports. `peer path` creates only that directory, never Git state; dispatch rejects nonconforming `.peer/` paths before creating files.

## Fan-out

Fan-out is the default (alias `peer run`); build `OUTDIR` with `peer path`. Stdout is a TSV manifest, one row per external peer:

```
{peer-id}  {status}  {outdir}/{peer-id}.yaml
```

The caller owns the report schema. Read every `ok` file; others are empty. Exit `0` if any result, `1` if none, `2` on usage error; failures exit per the table.

| Status | Meaning | Exit | Fix |
|---|---|---|---|
| `misconfig` | harness cannot serve model or provider | 2 | correct `reviewers.yaml` |
| `blocked` | a peer in this run was denied an operation; cause unverified | 2 or 3 | re-run unrestricted, re-read |
| `auth` | stored credentials rejected | 3 | re-run that harness's login |
| `limit` | rate or quota limit | 4 | retry later |
| `stalled` | watchdog or cap fired | 124 | retry, or raise `--idle`/`--cap` |
| `error` | other unclean exit | 124 | read the peer's stderr line |

- Statuses come only from harness error records; `misconfig` never means credentials, timeout, or reachability.
- Preflight checks model and provider; with an unreadable or stale model list it dispatches anyway, never `misconfig`.
- After any denial in a fan-out, sibling `misconfig` and `auth` rows become `blocked` until an unrestricted re-run.

## Herdr pane dispatch

Surface precedence: `--dispatch`, `PEER_DISPATCH`, registry `defaults.dispatch`, `herdr`. `cli` runs headless. `herdr` runs peers visibly in the `peer-review` session (`herdr session attach peer-review`), else headless when no live pane exists or the session or `workspace create` fails; `HERDR_ENV` does not decide. `peer herdr` reports the current surface. Manifest, statuses, exits match headless.

- Workspace per round `peer-<subject>-<stage>`, tab per peer id.
- Pane agents read the prompt file and write `{peer-id}.yaml`; positional prompts are materialized beside it.
- Reviewer panes: read-only except the stage directory.
- Peer reports approval or question dialogs, never answers them.
- A peer without a report leaves `{peer-id}.pane.log`; read it. Rounds close their workspace unless `PEER_HERDR_KEEP=1`.
- `peer herdr clean` removes settled `peer-` round workspaces, sparing working or blocked peers.

::::head

:::instruction{priority=high}
## Dispatch contract for skills

Use the [routing contract](reference/routing.md) to interpret `peer list`, `peer get`, `peer defaults reviewers` and to select, validate, and dispatch routes. The caller owns composition; peer never requires a paired native spawn.

Provenance is the result filename and manifest row; do not void a substantive report for a wrong self-declared id. Pi reviewers have no shell (they can read, search, find, list): put command-only context in the prompt, especially a materialized diff, requirements, and the report schema.
:::

::::

## Report triage

An `ok` row proves only that a report exists. Apply the [finding bar](../review/reference/finding-bar.md) and [review synthesis](../review/reference/synthesis.md); peer has no admission, residual, or round policy.
