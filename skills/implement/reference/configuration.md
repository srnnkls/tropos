# Implementation Agent Configuration

Owns `/implement`, `/continue`, and `/loop` configuration resolution plus immutable batch routing snapshots. The [peer routing contract](../../peer/reference/routing.md) owns registry interpretation and dispatch mechanics. Standalone review selection in `validation.yaml.review_config` is separate.

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

1. host-aware defaults from the peer routing contract;
2. current scope config;
3. inline `--config` assignments.

Supported assignments are `tester`, `tester_effort`, `implementer`, `implementer_effort`, `reviewer`, and `reviewer_effort`; reviewer aliases use `+`. `--reviewers` remains a legacy reviewer-only shorthand.

Supplying `--config` accepts a valid merged result without prompting. Otherwise prompt once for all routes. `/implement config <scope>` edits the current epoch instead of creating one.

Validate aliases, host compatibility, execution mechanism, and effort through the live [peer routing contract](../../peer/reference/routing.md). Reject invalid or inactive selections; never infer or silently convert them.

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

## Implementation Dispatch

Resolve each snapshot entry through [peer routing](../../peer/reference/routing.md). Use one external peer call per mutating task. For review, use one fan-out per role and start every role fan-out with all native role Tasks in the same assistant message.

A review gate requires one successful report from every execution class present in the snapshot. Never require an absent class.

Create every output directory through the canonical [peer report layout](../../peer/SKILL.md#report-layout--peer). Save materialized prompts as `prompt.md` and normalized native reports beside peer reports.

## Failures

A tester, implementer, or fix agent mutates the worktree regardless of route. On failure or interruption, preserve partial edits and record status/diff evidence plus its report directory; do not auto-retry, roll back, or advance.

Reviewer failures retain successful reports. Resume only missing reports for the same review wave.
