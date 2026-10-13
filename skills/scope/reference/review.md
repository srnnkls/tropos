# Scope Review

Runs as the creation gate ([Step 8](../SKILL.md#step-8-review-gate-mandatory)) or standalone via [scope](../SKILL.md) with `review <name>`, with the same gate semantics.

### Step 1: Identify Scope

Locate the scope per [Scope Location](../SKILL.md#scope-location); read `scope.md`, `tasks.yaml`, `validation.yaml`, and `design.md` if present. If not found, list available scopes, suggest the closest match, and ask.

### Step 2: Select Reviewers

Select reviewers and one shared effort per [reviewer selection](../../review/SKILL.md#reviewer-selection). With no reviewers selected, return to reviewer configuration ([Step 3.7](../SKILL.md#step-37-configure-scope-reviewers)).

Host-native reviewers check codebase features, terminology, patterns, documentation standards, dependency/API existence, and design depth. External reviewers (via `peer`) check newcomer gaps, term consistency, task coherence, clarity, and self-contained reasoning; they cannot see the codebase and may flag project conventions.

Dispatch details: [review](../../review/SKILL.md), [harnesses](../../review/reference/harnesses.md), [models](../../review/reference/models.md).

### Step 3: Dispatch Reviewers in Parallel

Review prompt template:

```
You are reviewing a scope for completeness and feasibility.

## Scope Documents
[Include scope.md content]
[Include tasks.yaml content]
[Include design.md content if present]

## Review Focus
Evaluate against these gates:
1. **Completeness** - Are all requirements specified? Missing behaviors?
2. **Consistency** - Do documents contradict each other? Ambiguous terms?
3. **Feasibility** - Can tasks be implemented as described? Missing dependencies?
4. **Clarity** - Would a fresh developer understand what to build?
5. **Design Depth** - Are alternatives substantiated, invariants testable? (n/a if no design.md)

## Output Format
Return the exact YAML reviewer_report schema embedded below.
```

Append the exact [Reviewer Report](#reviewer-report) schema. Mint the report directory with `outdir=$(peer path scope-{name} review)` and save the prompt as `{outdir}/prompt.md`.

In one assistant message, dispatch every selected reviewer using [peer routing](../../peer/reference/routing.md), then apply the [canonical review result gate](../../review/reference/harnesses.md#results). On timeout or error, keep completed reports, apply that gate, and redispatch only the missing reports for the same wave.

### Step 4: Synthesize Reviews

1. Extract YAML from every output, falling back to partial YAML, else mark the reviewer failed. For malformed YAML, report the reviewer with a raw snippet and continue.
2. Merge, aggregate gates and severity, and prioritize per [review synthesis](../../review/reference/synthesis.md); record actual reviewer aliases in `found_by`.
3. Rank questions in the row order of the [ambiguity scan](../SKILL.md#step-3-validation-human-in-the-loop) table.

### Step 5: Present Review

1. Show the gate summary and issues per the [synthesis presentation formats](../../review/reference/synthesis.md#issue-presentation-format).
2. Ask clarifying questions via AskUserQuestion, grouped by taxonomy area.
3. Add the clarification session with its answers to `validation.yaml`; close resolved markers and add markers for deferred items.

### Step 6: Record Gate Result and Recommend Action

Triage per [review synthesis](../../review/reference/synthesis.md): a `critical`/`high` issue blocks only when it names a concrete scope defect — a requirement contradicting another, a task with no achievable acceptance criterion, an unsatisfiable dependency. Reviewer agreement is not validity. Record findings that only narrow, restate, or re-litigate a grounded question as deferred nits; they do not fail the gate.

Write `review_gate` in `validation.yaml`:

- No triaged `critical`/`high` → `status: passed` with reviewers, timestamp, `blocking_resolved`, and deferred `medium` nits. Report "Ready for implementation."
- Otherwise → `status: failed`. Fold the findings into `scope.md` / `tasks.yaml` / `design.md` and re-run within the [synthesis round limits](../../review/reference/synthesis.md).

## Report Schema

Use this document schema, not the runtime code-failure schema: `description` names a concrete contradiction, omission, or infeasible requirement; `clarifying_questions` records missing decisions.

### Reviewer Report

```yaml
reviewer_report:
  reviewer: {reviewer-id}  # from `peer list`
  gates:
    completeness:
      status: pass | fail
      issues: []
    consistency:
      status: pass | fail
      issues: []
    feasibility:
      status: pass | fail
      issues: []
    clarity:
      status: pass | fail
      issues: []
    design_depth:
      status: pass | fail | n/a
      issues: []
  issues:
    - severity: critical | high | medium
      gate: completeness | consistency | feasibility | clarity | design_depth
      area: scope | behavior | data_model | constraints | edge_cases | integration | terminology | design
      description: "Clear description"
      suggestion: "Actionable fix"
  clarifying_questions:
    - area: scope | behavior | ...
      question: "What needs clarification?"
  strengths:
    - "Positive observation"
```

### Synthesized Report

```yaml
synthesized_report:
  reviewers: [{reviewer-id}, …]
  gates:
    completeness:
      status: pass | fail
      failed_by: []
  issues:
    - id: C1
      severity: critical
      gate: completeness
      area: edge_cases
      description: "Missing error handling"
      suggestion: "Add error case"
      found_by: [{reviewer-id}, …]
  recommendation: ready_to_implement | address_issues
```

## Severity

| Severity | Definition | Action |
|----------|------------|--------|
| `critical` | Blocks implementation | Must fix before proceeding |
| `high` | Significant gap | Must fix before proceeding |
| `medium` | Minor improvement | Can proceed, address later |

Taxonomy areas: [ambiguity scan](../SKILL.md#step-3-validation-human-in-the-loop); `design` covers alternatives, invariants, complexity analysis.
