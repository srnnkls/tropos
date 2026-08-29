# Checkpoint Format

A checkpoint stores only durable recovery state for an explicit scope implementation. Task status belongs to `tasks.yaml`; findings and deferred issues belong to `review.yaml`.

## Location

`scopes/<state>/<scope>/checkpoint.yaml`

## Schema

```yaml
checkpoint:
  scope_name: auth-system
  scope_path: scopes/active/auth-system
  branch: feat/auth-system
  last_commit: a1b2c3d4
  updated_at: 2026-08-29T12:00:00Z

  batch:
    number: 3
    tasks: [T003, T004]
    phase: red | green | review | fix | integration | complete
    status: pending | in_progress | completed | failed

  routing_snapshot:
    epoch_id: 20260829T120000Z-a1b2c3
    tester: {agent: opus, effort: inherit, class: native}
    implementer: {agent: gpt, effort: high, class: native}
    reviewer:
      agents:
        - {alias: opus, effort: high, class: native}
        - {alias: gemini, effort: high, class: external}

  reports:
    tester: {T003: .peer/auth-system/<run>/b3-tester-T003}
    implementer: {T003: .peer/auth-system/<run>/b3-implementer-T003}
    review:
      general: .peer/auth-system/<run>/b3-review-general
      architecture: .peer/auth-system/<run>/b3-review-architecture
      compliance: .peer/auth-system/<run>/b3-review-compliance

  in_flight_mutations:
    - task: T003
      phase: green
      agent: gpt
      report_dir: .peer/auth-system/<run>/b3-implementer-T003
      status: in_progress | failed
      evidence:
        before: {git_status: "...", git_diff: "..."}
        after_failure: {git_status: "...", git_diff: "..."}
      failure: null
```

Omit empty report sections and `in_flight_mutations` entries. Do not mirror done/pending task lists, next-batch calculations, TodoWrite, or deferred findings.

## Writes

Write at wave boundaries, not around each agent:

1. Batch start: persist the immutable routing snapshot, tasks, phase, and report directories.
2. Before a parallel mutating wave: add every dispatched task to `in_flight_mutations` in one write with baseline evidence.
3. After all results land: remove successful entries and retain failed/interrupted entries with current evidence in one write.
4. Before a read-only review wave: record its phase and report directories once. Report files carry per-reviewer completion state.
5. After review/fix synthesis: advance the phase once.
6. Batch completion: record `last_commit` and the next derived batch/phase; task and review details remain in their authoritative files.

A successful process exit alone never clears a mutating entry; its report and RED/GREEN/fix gate must pass.

## Recovery Priority

1. Recover `in_flight_mutations` exactly; preserve partial edits.
2. Otherwise resume the recorded batch phase and read existing reports from their directories.
3. Redispatch only missing work in that wave.
4. Derive task readiness from `tasks.yaml` and dependency batches; never from TodoWrite or copied checkpoint summaries.

The routing snapshot remains fixed for a recovered batch. Current `config.yaml` applies only after that batch completes. Legacy checkpoints may be normalized once after the live branch is active; ask when more than one recovery phase is plausible.
