# Implementation Agent Configuration

Owns configuration resolution and batch routing snapshots for [implement](../SKILL.md), [continue](../../continue/SKILL.md), and [loop](../../loop/SKILL.md). The [peer routing contract](../../peer/reference/routing.md) owns registry interpretation, validation, and dispatch mechanics. Standalone review selection in `validation.yaml.review_config` is separate.

## Schema

`scopes/<state>/<scope>/config.yaml`:

```yaml
version: 1
epoch:
  id: <peer-run-id>
  started_at: <timestamp>
  updated_at: <timestamp>
routing:
  tester: {agent: <route-id>, effort: inherit}
  implementer: {agent: <route-id>, effort: inherit}
  reviewer: {agents: [<route-id>], effort: inherit}
```

A top-level scope execution creates a new epoch; continue and loop reuse it. Direct tasks hold the same structure in memory and write reports under subject `direct`. Tester and implementer select one agent each; reviewer selects one or more. Persist `inherit` or a declared effort for every route.

## Resolution

Merge, last source winning:

1. tester and implementer defaults from the peer routing contract, plus the reviewer ensemble from `peer defaults reviewers`;
2. current scope config;
3. inline `--config` assignments: `tester`, `tester_effort`, `implementer`, `implementer_effort`, `reviewer`, `reviewer_effort`; reviewer aliases join with `+`. `--reviewers` is a legacy reviewer-only shorthand.

With `--config`, accept a valid merged result without prompting; otherwise prompt once for all routes. `config <scope>` edits the current epoch. Validate the result under the live peer routing contract.

## Batch Snapshot

Read and validate `config.yaml` once per batch and persist an immutable snapshot in the checkpoint:

```yaml
routing_snapshot:
  epoch_id: <id>
  tester: {agent: <route-id>, effort: <level>, class: native|native-proxy|peer}
  implementer: {agent: <route-id>, effort: <level>, class: native|native-proxy|peer}
  reviewer:
    agents:
      - {agent: <route-id>, effort: <level>, class: native|native-proxy|peer}
```

Every phase and review role in the batch uses it; edits apply to the next batch. A direct single-task run snapshots once in memory.

## Implementation Dispatch

Dispatch every snapshot entry under peer routing, preserving its class and mechanism. Create output directories through the [peer report layout](../../peer/SKILL.md#report-layout--peer); save materialized prompts as `prompt.md` and normalized native reports beside peer reports. Review results: [review result gate](../../review/reference/harnesses.md#results).

## Failures

[execute.md](../operations/execute.md#recovery-rules).
