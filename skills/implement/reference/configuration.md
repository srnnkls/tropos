# Implementation Agent Configuration

Canonical routing for `/implement`, `/continue`, and `/loop`. Standalone review selection in `validation.yaml.review_config` is separate.

## Schema

Scope routing lives at `scopes/<state>/<scope>/config.yaml`:

```yaml
version: 1
epoch:
  id: <peer-run-id>
  started_at: <timestamp>
  updated_at: <timestamp>
routing:
  tester: {agent: codex-native, effort: inherit}
  implementer: {agent: codex-native, effort: inherit}
  reviewer: {agents: [codex-native], effort: inherit}
```

A top-level scope execution creates a new epoch. `/continue` and `/loop` reuse it. Direct tasks keep the same structure in memory and write reports under subject `direct`.

Tester and implementer each select one agent. Reviewer selects one or more agents. Persist `inherit` or a declared effort for every route.

## Resolution

Merge, last source winning:

1. host-aware defaults;
2. current scope config;
3. inline `--config` assignments.

Supported assignments are `tester`, `tester_effort`, `implementer`, `implementer_effort`, `reviewer`, and `reviewer_effort`; reviewer aliases use `+`. `--reviewers` remains a legacy reviewer-only shorthand.

Supplying `--config` accepts a valid merged result without prompting. Otherwise prompt once for all routes. `/implement config <scope>` edits the current epoch instead of creating one.

Defaults:

- Codex host with native delegation: all roles `codex-native`, effort `inherit`.
- Claude host with Task: tester/implementer `opus` at `inherit`; reviewer `opus+gpt+gemini` at `high` when those routes are available.
- No native mechanism: require explicit routing.

## Host and Registry Rules

Use live `peer list` metadata. Alias names never decide the mechanism.

| Current host | Same-family route | Cross-family route |
|---|---|---|
| Codex | `codex-native` delegation | registered external peer aliases |
| Claude | native `opus`/`sonnet` Task | `ROUTABLE=yes` native subagent, otherwise peer |

- `codex-native` is a persisted token for inherited Codex delegation. Never pass it to peer or attach an explicit model/effort.
- `opus` and `sonnet` are Claude-host Task aliases. Their peer CLI forms are distinct aliases such as `opus-peer` and `sonnet-peer`.
- Reject same-host-family loopback using registry harness/family metadata. Ask for a corrected selection; never silently convert.
- A Claude-host alias with `ROUTABLE=yes` dispatches as a generated native subagent. `RUN-BY-PEER=yes` only says peer can run it.
- Gate every routable selection on `peer route check <role>=<alias>[@<effort>]` returning `active`. Never fall back to peer when the proxy or generated definition is unavailable.
- Validate external aliases and effort support against `peer list`. One reviewer effort must be supported by every selected peer.
- Reject unknown keys, aliases, duplicate assignments, empty values, malformed sets, unavailable variants, and host-incompatible routes.

## Effort Variants

Task has no reasoning-effort argument. A native route expresses non-inherited effort through its generated definition name:

```text
<role>-<effort>
<role>-<alias>-<effort>
```

The level must appear in `reviewers.yaml` `efforts:` and the exact routable variant must pass `peer route check`. Naming a generated definition directly bypasses the global `peer route` hook, so this precondition is mandatory.

Peer routes receive the same level through `--effort`. `codex-native` accepts only `inherit`.

When a singular route changes to a host-native alias without an explicit effort, normalize it to `inherit`. When it changes to a peer route, require or select a peer-supported effort. An all-native reviewer set without an effort normalizes to `inherit`.

## Batch Snapshot

Read and validate `config.yaml` once at the start of each batch. Persist an immutable routing snapshot in the checkpoint:

```yaml
routing_snapshot:
  epoch_id: <id>
  tester: {agent: <alias>, effort: <level>, class: native|external}
  implementer: {agent: <alias>, effort: <level>, class: native|external}
  reviewer:
    agents:
      - {alias: <alias>, effort: <level>, class: native|external}
```

Every phase and concurrent review role in that batch uses the snapshot. A mid-batch config edit applies to the next batch. A direct single-task run snapshots once in memory.

## Dispatch

- `codex-native`: native Codex delegation with inherited session settings.
- Claude native alias: `Task(subagent_type="<role>", model="<alias>", prompt=...)`.
- Routable alias: `Task(subagent_type="<role>-<alias>[-<effort>]", prompt=...)`, with no model argument.
- External alias: write the complete prompt to `<outdir>/prompt.md`, then run:

```bash
peer -C <workdir> -d <outdir> --agent <role> \
  --peers <aliases> --effort <effort> --prompt-file <outdir>/prompt.md
```

Use one external peer call per mutating task. For review, use one fan-out per role and start all role fan-outs with all native role Tasks in the same assistant message.

A review gate requires one successful report from every execution class present in the snapshot. Never require an absent class.

## Report Layout

Use `peer path <subject> <stage> --run <epoch-id>` for every directory. Never assemble paths by hand.

```text
.peer/<subject>/<epoch-id>/b3-tester-T003/
.peer/<subject>/<epoch-id>/b3-implementer-T003/
.peer/<subject>/<epoch-id>/b3-review-general/
.peer/<subject>/<epoch-id>/integration-review/
```

Save materialized prompts as `prompt.md`. Store normalized native reports alongside peer reports.

## Failures

A tester, implementer, or fix agent mutates the worktree regardless of route. On failure or interruption, preserve partial edits and record status/diff evidence plus its report directory; do not auto-retry, roll back, or advance.

Reviewer failures retain successful reports. Resume only the missing reports for the same review wave.
