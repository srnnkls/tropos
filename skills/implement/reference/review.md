# Implementation Review State

`review.yaml` is the sole authority for implementation findings, resolutions, deferred issues, batch review outcomes, and optional multi-batch integration review.

## Location

`scopes/<state>/<scope>/review.yaml`

## Schema

```yaml
metadata:
  scope_name: auth-system
  branch: feat/auth-system
  last_updated: 2026-08-29T12:00:00Z
  total_batches: 3

gates:
  correctness: pass | fail | pending
  style: pass | fail | pending
  performance: pass | fail | pending
  security: pass | fail | pending
  architecture: pass | fail | pending

batch_reviews:
  - batch: 1
    commit: a1b2c3d4
    tasks: [T001, T002]
    routing_epoch: 20260829T120000Z-a1b2c3
    reviewers:
      - id: general-claude-opus
        execution_class: native
        effort: high
        status: success | timeout | failed
    synthesized:
      gates: {correctness: pass, style: pass, performance: pass, security: pass, architecture: pass}
      critical_issues: 0
      high_issues: 0
      medium_issues: 1
    outcome: approved | changes_requested

issues:
  - id: H001
    batch: 1
    task: T001
    finding: "Exact admitted issue record from ../../review/reference/report.md"
    found_by: [general-claude-opus]
    status: open | resolved | deferred | residual | needs_decision
    resolution: null

integration_review:
  required: true  # false for one batch
  status: pending | in_progress | completed
  reviewers: []
  acceptance_criteria_met: false
  cross_batch_validation: pending | pass | fail
  issues: []
  recommendation: ready_to_merge | changes_requested | null
```

Each `finding` is the exact admitted issue object from the canonical [review report](../../review/reference/report.md). Batch/task attribution and resolution state are implementation-owned extensions. Derive deferred lists and readiness from issue statuses, task state, batch reviews, validation evidence, and the integration result; do not persist duplicate rollups.

Record the actual agent, effort, and execution class from the batch snapshot. Do not copy live routing into a second configuration block.

## Writes

After one concurrent Phase C wave:

1. append one batch entry;
2. update aggregate gates;
3. add only findings admitted by synthesis;
4. record resolutions, residuals, `needs_decision`, and medium deferrals;
5. write once with the batch commit.

A one-batch scope sets `integration_review.required: false` and treats its Phase C plus native validation as final. A multi-batch scope writes one holistic integration result after all batches; it does not repeat General/Architecture/Compliance.

## Readers

- [continue](../../continue/SKILL.md) reads the latest batch/integration outcome and existing report directories from the checkpoint.
- [implement](../SKILL.md) derives blocking findings and readiness from authoritative task, issue, validation, and integration state.
- [scope](../../scope/SKILL.md) with `done` checks task state, acceptance evidence, native validation, and the required integration outcome.

`tasks.yaml` owns task status. `checkpoint.yaml` owns the current recovery wave. `validation.yaml` owns pre-implementation scope review and its reviewer configuration.
