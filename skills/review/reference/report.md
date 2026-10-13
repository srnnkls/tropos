# Review Report Format

## Reviewer Report

```yaml
reviewer_report:
  reviewer: {role}-{reviewer-id}  # reviewer-ids come from `peer list`

  gates:
    correctness:
      status: pass | fail
      issues:
        - "Logic error in X"
    style:
      status: pass | fail
      issues:
        - "Inconsistent naming"
    performance:
      status: pass | fail
      issues:
        - "N+1 query pattern"
    security:
      status: pass | fail
      issues:
        - "SQL injection risk"
    architecture:
      status: pass | fail
      issues:
        - "Tight coupling between X and Y"
    abstractions:
      status: pass | fail
      issues:
        - "parse_window duplicates dateutil.rrule"

  issues:
    - severity: critical | high | medium
      gate: correctness | style | performance | security | architecture | abstractions
      area: logic | error_handling | type_safety | naming | formatting | efficiency | validation | secrets | coupling | testing | duplication | reimplementation | misfit
      location: "file:line"
      trigger: "Reachable input or state"
      wrong_outcome: "Concrete incorrect result"
      suggestion: "Smallest shared-root fix or needs decision: constraint"

  strengths:
    - "Good error handling"
    - "Clear function names"
```

Every issue uses this base shape. Role extensions add analysis fields; they never redefine gates or issue fields. Missing `trigger` or `wrong_outcome` makes an execution finding schema-invalid.

## Synthesized Report

The main agent produces this after merging reviewer reports.

```yaml
synthesized_report:
  reviewers: [{role}-{reviewer-id}, …]  # one entry per configured reviewer (see `peer list`)

  gates:
    correctness:
      status: pass | fail
      failed_by: [{role}-{reviewer-id}]
    style:
      status: pass | fail
      failed_by: []
    performance:
      status: pass | fail
      failed_by: []
    security:
      status: pass | fail
      failed_by: [{role}-{reviewer-id}, …]
    architecture:
      status: pass | fail
      failed_by: []

  issues:
    - id: C1
      severity: critical
      gate: security
      area: validation
      location: "src/db/query.py:45"
      trigger: "Untrusted search text reaches query construction"
      wrong_outcome: "The text changes the SQL statement"
      suggestion: "Use parameterized queries"
      found_by: [{reviewer-id}, …]
      verified: "How the failure mode was confirmed against the artifact"

  residual:
    - gate: correctness
      location: "src/api/handler.ts:112"
      trigger: "Reported input or state"
      wrong_outcome: "Reported incorrect result"
      found_by: [{reviewer-id}, …]
      reason: unreachable_input | already_falsified | already_grounded | design_as_defect | equivalent_rewrite | deferred_hardening
      evidence: "What rules the report out"

  strengths:
    - "Clear separation of concerns"
    - "Comprehensive error messages"

  summary:
    critical: 1
    high: 2
    medium: 3

  recommendation: ready_to_merge | address_issues
  next_action: "Commit/merge" | "Fix critical/high issues"
```

## Issue Severity

| Severity | Definition |
|----------|------------|
| `critical` | Bugs, security issues, data corruption — must fix before merge |
| `high` | Significant issues, unclear behavior — should fix before merge |
| `medium` | Style issues, minor improvements — can merge, follow-up |

Assign severity after triage. `residual` issues carry no severity and never fail a gate.

A `suggestion` prefixed `needs decision:` names a fix that would add public API surface, a new type, or a signature change; surface it to the user, never to a fix agent.

## Role-Specific Report Extensions

Each role's reviewers add its section alongside the standard gates and issues.

### Architecture Role: `structural_analysis`

```yaml
reviewer_report:
  reviewer: architecture-{reviewer-id}  # reviewer-ids come from `peer list`
  role: architecture
  gates:
    architecture:
      status: pass | fail
      issues: [...]
  structural_analysis:
    coupling_delta: increased | stable | decreased
    new_hotspots: [{ symbol: "name", file: "path", in_degree: N }]
    cycles_introduced: [{ members: ["A", "B", "C"] }]
    seam_violations: [{ symbol: "name", expected_cluster: "X", actual_cluster: "Y" }]
    impact_radius: N  # symbols affected beyond direct changes
  issues: [...]  # Exact base issue schema above
  strengths:
    - "Good structural observation"
```

### Compliance Role: `compliance_analysis`

```yaml
reviewer_report:
  reviewer: compliance-{reviewer-id}  # reviewer-ids come from `peer list`
  role: compliance
  gates:
    style:
      status: pass | fail
      issues: [...]
  compliance_analysis:
    languages_checked: [python, rust]
    rules_evaluated: N
    violations:
      - rule: "naming/5x-rule"
        source: "python/quality.md"
        location: "file:line"
        description: "Variable 'd' should have a descriptive name"
        suggestion: "Rename to 'duration_seconds'"
      - rule: "composition/no-inheritance"
        source: "python/composition.md"
        location: "file:line"
        description: "Class hierarchy 3 levels deep"
        suggestion: "Flatten with composition"
  issues: [...]  # Exact base issue schema above
  strengths:
    - "Good compliance observation"
```

### Abstractions Role: `abstraction_analysis`

```yaml
reviewer_report:
  reviewer: abstractions-{reviewer-id}  # reviewer-ids come from `peer list`
  role: abstractions
  gates:
    abstractions:
      status: pass | fail
      issues: [...]
  abstraction_analysis:
    definitions_checked:
      - definition: "path:symbol"
        searched: [repository, dependencies, change]
        owner: "path:symbol | package@version api | none"
  issues: [...]  # Exact base issue schema above
  strengths:
    - "Good placement observation"
```
