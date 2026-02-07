# Review Report Format

YAML schema for structured review handoff and synthesis.

---

## Reviewer Report

Each reviewer outputs this structure:

```yaml
reviewer_report:
  # Which reviewer produced this report
  reviewer: claude-opus | opencode-gpt5.2

  # Gate evaluations
  gates:
    completeness:
      status: pass | fail
      issues:
        - "Missing X"
    consistency:
      status: pass | fail
      issues:
        - "Term Y used inconsistently"
    feasibility:
      status: pass | fail
      issues:
        - "Task Z depends on undefined API"
    clarity:
      status: pass | fail
      issues:
        - "Scope boundary unclear"
    design_depth:
      status: pass | fail | n/a
      issues:
        - "Alternatives lack rejection rationale"

  # Detailed issues with suggestions
  issues:
    - severity: critical | high | medium
      gate: completeness | consistency | feasibility | clarity | design_depth
      area: scope | behavior | data_model | constraints | edge_cases | integration | terminology | design
      description: "Clear description of the issue"
      suggestion: "Actionable fix"

  # Questions requiring user input
  clarifying_questions:
    - area: scope | behavior | data_model | constraints | edge_cases | integration | terminology | design
      question: "What needs clarification?"

  # Positive observations
  strengths:
    - "Well-defined acceptance criteria"
    - "Clear task breakdown"
```

---

## Synthesized Report

Main agent produces this after merging reviewer reports:

```yaml
synthesized_report:
  reviewers: [claude-opus, opencode-gpt5.2]

  # Aggregate gate status (fail if either fails)
  gates:
    completeness:
      status: pass | fail
      failed_by: [claude-opus]  # empty if passed
    consistency:
      status: pass | fail
      failed_by: []
    feasibility:
      status: pass | fail
      failed_by: [claude-opus, opencode-gpt5.2]
    clarity:
      status: pass | fail
      failed_by: []
    design_depth:
      status: pass | fail | n/a
      failed_by: []

  # Merged and deduplicated issues
  issues:
    - id: C1
      severity: critical
      gate: completeness
      area: edge_cases
      description: "Missing error handling for timeout"
      suggestion: "Add timeout case to edge cases section"
      found_by: [claude-opus, opencode-gpt5.2]  # higher confidence

  # Prioritized questions
  clarifying_questions:
    - area: scope
      question: "User roles not defined"
      priority: 1
    - area: behavior
      question: "What happens on auth failure?"
      priority: 2

  # Combined strengths
  strengths:
    - "Clear acceptance criteria"
    - "Good task granularity"

  # Recommendation
  recommendation: ready_to_promote | address_issues
  next_action: "/spec.promote" | "Fix issues, re-run /spec.review"
```

---

## Gate Status Values

| Status | Meaning |
|--------|---------|
| `pass` | No issues found for this gate |
| `fail` | One or more issues found |
| `n/a` | Gate not applicable (e.g., design_depth when no design.md present) |

---

## Issue Severity

| Severity | Definition | Action |
|----------|------------|--------|
| `critical` | Blocks implementation | Must fix before proceeding |
| `high` | Significant gap | Should fix before proceeding |
| `medium` | Minor improvement | Can proceed, address later |

---

## Taxonomy Areas

Used for `area` field to categorize issues:

| Area | Covers |
|------|--------|
| `scope` | Goals, boundaries, success criteria |
| `behavior` | User flows, system responses |
| `data_model` | Entities, relationships, schemas |
| `constraints` | Performance, security, compatibility |
| `edge_cases` | Error handling, limits |
| `integration` | APIs, dependencies, interfaces |
| `terminology` | Domain terms, definitions |
| `design` | Alternatives, invariants, complexity analysis |
