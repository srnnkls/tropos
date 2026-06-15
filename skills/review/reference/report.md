# Review Report Format

YAML schema for structured review handoff and synthesis.

---

## Reviewer Report

Each reviewer outputs this structure:

```yaml
reviewer_report:
  reviewer: {role}-{harness}-{model}  # e.g., general-claude-opus, architecture-codex-gpt5.5, compliance-gemini-3.5-flash

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
  reviewers: [general-claude-opus, general-codex-gpt5.5, architecture-claude-opus, architecture-codex-gpt5.5, compliance-claude-opus, compliance-codex-gpt5.5]

  gates:
    correctness:
      status: pass | fail
      failed_by: [general-claude-opus]
    style:
      status: pass | fail
      failed_by: []
    performance:
      status: pass | fail
      failed_by: []
    security:
      status: pass | fail
      failed_by: [general-claude-opus, general-gemini-3.5-flash]
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
      found_by: [general-claude-opus, general-gemini-3.5-flash]

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

| Status | Meaning |
|--------|---------|
| `pass` | No issues found for this gate |
| `fail` | One or more issues found |

---

## Issue Severity

| Severity | Definition | Action |
|----------|------------|--------|
| `critical` | Bugs, security issues, data corruption | Must fix before merge |
| `high` | Significant issues, unclear behavior | Should fix before merge |
| `medium` | Style issues, minor improvements | Can merge, follow-up |

---

## Issue Areas

| Area | Covers |
|------|--------|
| `logic` | Control flow, algorithms, conditionals |
| `error_handling` | Exceptions, error states, recovery |
| `type_safety` | Type correctness, nullability |
| `naming` | Variable, function, class names |
| `formatting` | Code layout, indentation, spacing |
| `efficiency` | Time/space complexity, caching |
| `validation` | Input checking, sanitization |
| `secrets` | Credentials, keys, tokens |
| `coupling` | Dependencies, interfaces |
| `testing` | Test coverage, testability |

---

## Role-Specific Report Extensions

### Architecture Role: `structural_analysis`

Architecture reviewers include this section alongside standard gates/issues:

```yaml
reviewer_report:
  reviewer: architecture-claude-opus
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
  reviewer: compliance-claude-opus
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
