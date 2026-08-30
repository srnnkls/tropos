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

Write at true wave boundaries:

1. Batch start: persist the immutable routing snapshot, tasks, phase, report directories, and every tester mutation before dispatch.
2. Mutating-wave boundary: after results land, clear successful entries, retain failed/interrupted evidence, and arm every mutation in the next wave in one write before dispatch.
3. Read-only boundary: only after every mutation clears its gate, remove those entries, set the review phase, and record report directories in one write. A failed mutation retains its mutating phase and pauses.
4. After review or fix synthesis: advance the phase once. Every fix wave still receives durable mutation markers before dispatch and one result write afterward.
5. Batch completion: after the commit exists, record its actual ID and the next derived batch/phase. Task and review details remain in their authoritative files.

A successful process exit alone never clears a mutating entry; its report and RED/GREEN/fix gate must pass.

## Recovery Priority

1. Recover `in_flight_mutations` exactly; preserve partial edits.
2. Otherwise resume the recorded batch phase and read existing reports from their directories.
3. Redispatch only missing work in that wave.
4. Derive task readiness from `tasks.yaml` and dependency batches; never from TodoWrite or copied checkpoint summaries.

The routing snapshot remains fixed for a recovered batch. Current `config.yaml` applies only after that batch completes. Legacy checkpoints may be normalized once after the live branch is active; ask when more than one recovery phase is plausible.
