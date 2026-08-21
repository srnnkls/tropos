# Review Report Format

YAML schema for structured review handoff and synthesis.

---

## Reviewer Report

Each reviewer outputs this structure:

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

  issues:
    - severity: critical | high | medium
      gate: correctness | style | performance | security | architecture
      area: logic | error_handling | type_safety | naming | formatting | efficiency | validation | secrets | coupling | testing
      location: "file:line"
      description: "Clear description of the issue"
      suggestion: "Actionable fix"

  strengths:
    - "Good error handling"
    - "Clear function names"
```

---

## Synthesized Report

Main agent produces this after merging reviewer reports:

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
      description: "SQL injection via unsanitized user input"
      suggestion: "Use parameterized queries"
      found_by: [{reviewer-id}, …]  # reviewer-ids come from `peer list`
      verified: "How the failure mode was confirmed against the artifact"

  residual:
    - gate: correctness
      location: "src/api/handler.ts:112"
      description: "Reported issue that did not clear triage"
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

---

## Gate Status Values

`pass` | `fail`

---

## Issue Severity

| Severity | Definition |
|----------|------------|
| `critical` | Bugs, security issues, data corruption — must fix before merge |
| `high` | Significant issues, unclear behavior — should fix before merge |
| `medium` | Style issues, minor improvements — can merge, follow-up |

Severity is assigned after triage. Issues in `residual` carry no severity and never fail a
gate; see [synthesis.md](synthesis.md) for the validity bar and
[finding-bar.md](finding-bar.md) for what reviewers may report at all.

A `suggestion` prefixed `needs decision:` names a fix that would add public API surface, a new
type, or a signature change. It is surfaced to the user, never handed to a fix agent.

---

## Issue Areas

`logic` | `error_handling` | `type_safety` | `naming` | `formatting` | `efficiency` | `validation` | `secrets` | `coupling` | `testing`

---

## Role-Specific Report Extensions

### Architecture Role: `structural_analysis`

Architecture reviewers include this section alongside standard gates/issues:

```yaml
reviewer_report:
  reviewer: architecture-{reviewer-id}  # reviewer-ids come from `peer list`
  role: architecture
  gates:
    architecture:
      status: pass | fail
      issues: [...]
    performance:
      status: pass | fail
      issues: [...]
  structural_analysis:
    coupling_delta: increased | stable | decreased
    new_hotspots: [{ symbol: "name", file: "path", in_degree: N }]
    cycles_introduced: [{ members: ["A", "B", "C"] }]
    seam_violations: [{ symbol: "name", expected_cluster: "X", actual_cluster: "Y" }]
    impact_radius: N  # symbols affected beyond direct changes
  issues:
    - severity: critical | high | medium
      gate: architecture
      area: coupling
      location: "file:line"
      description: "Clear description"
      suggestion: "Actionable fix"
  strengths:
    - "Good structural observation"
```

### Compliance Role: `compliance_analysis`

Compliance reviewers include this section alongside standard gates/issues:

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
  issues:
    - severity: critical | high | medium
      gate: style
      area: naming
      location: "file:line"
      description: "Clear description"
      suggestion: "Actionable fix"
  strengths:
    - "Good compliance observation"
```
