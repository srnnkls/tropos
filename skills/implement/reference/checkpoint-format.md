# Checkpoint Format

Durable recovery state only, at `scopes/<state>/<scope>/checkpoint.yaml`. Task status lives in `tasks.yaml`; findings and deferred issues in `review.yaml`.

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
    tester: {agent: claude-opus, effort: inherit, class: native}
    implementer: {agent: claude-gpt5.6-sol, effort: high, class: native-proxy}
    reviewer:
      agents:
        - {agent: claude-opus, effort: high, class: native}
        - {agent: peer-gpt6-astra, effort: high, class: peer}

  reports:
    tester: {T003: .peer/auth-system/<run>/b3-tester-T003}
    implementer: {T003: .peer/auth-system/<run>/b3-implementer-T003}
    review:
      general: .peer/auth-system/<run>/b3-review-general
      architecture: .peer/auth-system/<run>/b3-review-architecture
      compliance: .peer/auth-system/<run>/b3-review-compliance
      abstractions: .peer/auth-system/<run>/b3-review-abstractions

  in_flight_mutations:
    - task: T003
      phase: green
      agent: claude-gpt5.6-sol
      report_dir: .peer/auth-system/<run>/b3-implementer-T003
      status: in_progress | failed
      evidence:
        before: {git_status: "...", git_diff: "..."}
        after_failure: {git_status: "...", git_diff: "..."}
      failure: null
```

Omit empty report sections and `in_flight_mutations` entries. Do not mirror task lists, next-batch calculations, TodoWrite, or deferred findings.

## Writes

One write per boundary:

1. Batch start, before tester dispatch: snapshot, tasks, phase, report directories, and every task as an in-flight tester mutation with baseline status/diff.
2. Mutating boundary (RED→GREEN, fix): clear entries whose gate passed, retain failed/interrupted evidence, and arm the next wave's mutations before dispatch.
3. Read-only boundary: only once every mutation clears its gate, remove the entries, set phase `review`, and record review report directories; otherwise keep the mutating phase and pause.
4. After review or fix synthesis: advance the phase once.
5. After the batch commit: record its ID and the next batch/phase.

A process exit alone never clears a mutating entry.

## Recovery Priority

1. Recover `in_flight_mutations` exactly, preserving partial edits.
2. Otherwise resume the recorded phase, reading existing reports and redispatching only missing work.
3. Otherwise derive readiness from `tasks.yaml` and dependency batches.

A recovered batch keeps its routing snapshot; current `config.yaml` applies after it completes. Normalize a legacy checkpoint once after the live branch is active; ask when more than one recovery phase is plausible.
