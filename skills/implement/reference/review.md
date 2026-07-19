# Review Format

Implementation review tracking in `review.yaml`. Mirrors validation.yaml structure.

## Location

```
./scopes/<state>/<scope-name>/review.yaml
```

`<state>` is the lifecycle dir (`draft`, `active`, `done`).

## Schema

```yaml
# Review: ${SCOPE_NAME}
# Machine + human readable implementation review tracking
#
# This file tracks batch reviews, accumulated issues, gate results, and
# final review status. Intended for both programmatic access (dispatch execute,
# continue) and human review.

metadata:
  scope_name: ${SCOPE_NAME}
  scope_path: ./scopes/${STATE}/${SCOPE_NAME}  # ${STATE} ∈ {draft, active, done}
  branch: feat/${SCOPE_NAME}
  created: ${DATE}
  last_updated: ${TIMESTAMP}
  total_batches: ${N}
  batches_reviewed: ${M}

# Informational snapshot of the live implementation route used most recently.
# Batch entries below remain the authoritative record of agents that actually ran.
implementation_config:
  epoch_id: ${EPOCH_ID}
  reviewer:
    agents: ${REVIEWER_ALIASES}
    effort: ${REVIEWER_EFFORT}  # peer-only when mixed; inherit for all-native

# Accumulated gate status across all batch reviews.
# Gate fails if ANY batch review failed it.
# Status values: pass | fail | pending
gates:
  correctness:
    status: ${STATUS}
    failed_batches: []  # [1, 3] if batches 1 and 3 failed this gate
  style:
    status: ${STATUS}
    failed_batches: []
  performance:
    status: ${STATUS}
    failed_batches: []
  security:
    status: ${STATUS}
    failed_batches: []
  architecture:
    status: ${STATUS}
    failed_batches: []

# Batch reviews record each review session.
# Written after Phase C of each batch.
batch_reviews:
  - batch: 1
    timestamp: ${TIMESTAMP}
    commit: ${SHA}
    tasks: [T001, T002]
    reviewers:
      # one entry per configured reviewer (see `peer list`)
      - id: {role}-{reviewer-id}
        execution_class: native | external
        effort: inherit | ${PEER_EFFORT}
        status: success  # or timeout | failed
        gates:
          correctness: pass
          style: pass
          performance: pass
          security: pass
          architecture: pass
    synthesized:
      gates:
        correctness: pass
        style: fail
        performance: pass
        security: pass
        architecture: pass
      critical_issues: 0
      high_issues: 0
      medium_issues: 1
    outcome: approved  # or changes_requested
  # Additional batches follow same structure

# Accumulated issues across all batches.
# Grouped by severity, includes resolution status.
issues:
  critical:
    - id: C001
      batch: 2
      task: T003
      gate: security
      location: "src/auth/login.py:45"
      description: "SQL injection via unsanitized input"
      suggestion: "Use parameterized queries"
      found_by: [{reviewer-id}, …]
      status: resolved  # or open
      resolution:
        batch: 2
        commit: ${SHA}
        fix: "Added parameterized query"
  high:
    - id: H001
      batch: 1
      task: T001
      gate: correctness
      location: "src/models/user.py:23"
      description: "Missing null check before dereference"
      suggestion: "Add guard clause"
      found_by: [{reviewer-id}]
      status: resolved
      resolution:
        batch: 1
        commit: ${SHA}
        fix: "Added None check"
  medium:
    - id: M001
      batch: 1
      task: T002
      gate: style
      location: "src/auth/auth.py:45"
      description: "Variable name 'x' is unclear"
      suggestion: "Rename to 'retry_count'"
      found_by: [{reviewer-id}]
      status: deferred  # medium issues can be deferred
      resolution: null

# Deferred issues (medium severity, noted for later).
# Carried forward in checkpoints.
deferred_issues:
  - id: M001
    batch: 1
    description: "Variable naming in auth.py:45"
    gate: style
  # Additional deferred issues

# Final review (after all batches complete).
# Comprehensive review of entire implementation.
final_review:
  status: pending  # pending | in_progress | completed
  timestamp: null
  reviewers: []
  reviewer_effort: null  # peer-only when mixed; inherit for all-native
  native_effort: inherit
  gates:
    correctness: pending
    style: pending
    performance: pending
    security: pending
    architecture: pending
  scope_compliance:
    all_tasks_complete: ${BOOL}
    acceptance_criteria_met: ${BOOL}
    edge_cases_handled: ${BOOL}
  issues: []
  strengths: []
  overall_assessment: null
  recommendation: null  # ready_to_merge | changes_requested

# Readiness checklist for merge/PR.
# All items must be true for implementation to be considered complete.
readiness:
  all_batches_reviewed: ${BOOL}
  critical_issues_resolved: ${BOOL}
  high_issues_resolved: ${BOOL}
  final_review_passed: ${BOOL}
  tests_passing: ${BOOL}

# Notes for additional context.
notes: |
  ${NOTES}
```

## Usage

### Writing review.yaml

**After each batch review (Phase C):**

1. Read existing review.yaml (or create if first batch)
2. Reload the live implementation config and record its epoch/reviewer snapshot
3. Append a new `batch_reviews` entry containing every agent actually dispatched and its outcome
4. Update accumulated gates
5. Add new issues to appropriate severity list
6. Update deferred_issues if medium issues noted
7. Write updated review.yaml
8. Include in batch commit

**After final review:**

1. Read review.yaml
2. Populate final_review section
3. Update readiness checklist
4. Write final review.yaml

### Reading review.yaml

**By continue:**
- Check last batch reviewed
- Load deferred issues
- Determine next batch

**By code review (final mode):**
- Load all batch results
- Identify patterns across batches
- Complete final_review section

## Relationship to Other Files

| File | Purpose |
|------|---------|
| validation.yaml | Pre-implementation scope quality/review only; its `review_config` never routes implementation agents |
| config.yaml | Live tester, implementer, and reviewer routing for the current implementation epoch |
| review.yaml | Post-implementation: code quality, batch reviews |
| checkpoint.yaml | Session state: progress, next batch |
| tasks.yaml | Task definitions and status |

## Gates

| Gate | What It Checks |
|------|----------------|
| correctness | Logic errors, edge cases, error handling, type safety |
| style | Naming conventions, formatting, readability, idioms |
| performance | Efficiency, data structures, unnecessary computation |
| security | Input validation, secrets exposure, injection risks |
| architecture | Design patterns, coupling, separation of concerns |
