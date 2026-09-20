# Scope Review

Multi-perspective scope review using parallel subagent dispatch.

---

## When to Use

- The mandatory gate every scope must clear before `implement`/`loop` (all issue types)
- After creation to validate before implementation
- When scope feels incomplete or ambiguous
- Standalone review of existing scopes (re-run to clear/refresh the gate)

---

## Workflow

### Step 1: Identify Scope

1. Parse scope name from argument (e.g., [scope](../SKILL.md) with `review auth-system`)
2. **Locate scope:** If name provided, search `scopes/{draft,active,done}/<name>/`. If no argument: find most recent `scope.md` under `scopes/*/*/`.
3. Read scope documents: `scope.md`, `tasks.yaml`, `validation.yaml`, and `design.md` (if present)

### Step 2: Select Reviewers

Select reviewers from live registry metadata and validate the whole selection through the canonical [peer routing contract](../../peer/reference/routing.md). Scope review chooses reviewers and one shared effort; it never restates host compatibility or dispatch mechanics.

### Step 3: Dispatch Reviewers in Parallel

**CRITICAL:** Dispatch all selected reviewers in the same message for true parallelism.

**Review Prompt Template:**

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

Append the exact Reviewer Report schema from this document to the materialized prompt. Mint the
report directory with `outdir=$(peer path scope-{name} review)` and save the prompt as
`{outdir}/prompt.md`.

In one assistant message, dispatch every selected reviewer using [peer routing](../../peer/reference/routing.md), then apply the [canonical review result gate](../../review/reference/harnesses.md#results).

### Step 4: Synthesize Reviews

1. **Parse reports** — Extract YAML from all outputs
2. **Merge issues** — Deduplicate by similarity, combine multi-reviewer findings (higher confidence)
3. **Aggregate gates** — Gate fails if ANY reviewer fails it
4. **Prioritize questions** — Rank: Scope > Behavior > Data Model > Constraints > Edge Cases > Integration > Terminology

### Step 5: Present Review

Gate summary table + issues by severity (Critical → High → Medium), noting which reviewers found each.

### Step 6: Clarifying Questions

Use **AskUserQuestion** with questions grouped by taxonomy area. Record answers for validation.yaml.

### Step 7: Update Validation

Add clarification session to `validation.yaml`. Update markers (close resolved, add new for deferred).

### Step 8: Record Gate Result and Recommend Action

This review is the mandatory blocking gate a scope must clear before implementation (the scope-level analog of the `issue` skill's pre-publish gate). Write the outcome to `validation.yaml` under `review_gate`:

Triage findings before they gate anything, per [review synthesis](../../review/reference/synthesis.md): a `critical`/`high` issue blocks only when it names a concrete defect in the scope — a requirement that contradicts another, a task with no achievable acceptance criterion, a dependency that cannot be satisfied. Reviewer agreement is not validity. Findings that only narrow, restate, or re-litigate a grounded question are recorded as deferred nits and do not fail the gate.

- **No triaged `critical`/`high` issue** → `review_gate.status: passed` (record reviewers, timestamp, `blocking_resolved`, and any deferred `medium` nits). Report "Ready for implementation."
- **Any triaged `critical`/`high` issue** → `review_gate.status: failed`. Fold the findings back into the scope documents and re-run under the canonical [synthesis round limits](../../review/reference/synthesis.md).

`implement`/`loop` will not execute a scope whose `review_gate.status` is absent or `failed` (enforced at `implement/operations/execute.md` Step 2).

When invoked standalone ([scope](../SKILL.md) with `review <name>`) the same gate semantics apply — a passing run writes `review_gate.status: passed`, unblocking implementation.

---

## Reviewer Roles

### Host-Native Reviewer (Context-Aware)

- Cross-references with similar features in codebase
- Checks against project terminology and patterns
- Verifies dependencies exist, APIs available
- Applies project documentation standards
- Verifies design depth (alternatives substantiated, invariants testable)

Deep project context, can verify feasibility against actual codebase, catches integration issues. Single model perspective, may be anchored by prior context.

### External Reviewer (Fresh Perspective — via `peer`)

- Evaluates what's missing that a newcomer would need
- Checks terms and concepts for self-consistency
- Validates logical coherence of described tasks
- Tests clarity for unfamiliar readers
- Assesses whether reasoning is self-contained

Catches assumptions insiders miss, simulates new team member perspective. Cannot verify against actual codebase, may flag project conventions as issues.

---

## Harnesses

See [review](../../review/SKILL.md) for harness details, models, and dispatch templates:
- [reference/harnesses.md](../../review/reference/harnesses.md) — dispatch configuration
- [reference/models.md](../../review/reference/models.md) — available models and reasoning levels

---

## Report Schema

Scope review owns the pre-implementation document schema below. It shares the review harness and synthesis discipline but not the runtime code-failure schema: `description` names a concrete contradiction, omission, or infeasible requirement, while `clarifying_questions` records missing decisions.

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

---

## Gate Definitions

| Gate | What It Checks |
|------|----------------|
| **Completeness** | All requirements specified, no missing behaviors |
| **Consistency** | Documents align, no contradictions, terms used consistently |
| **Feasibility** | Tasks implementable, dependencies available, no blockers |
| **Clarity** | Unambiguous, fresh developer can understand scope |
| **Design Depth** | Alternatives substantiated, invariants testable (n/a when no design.md) |

## Issue Severity

| Severity | Definition | Action |
|----------|------------|--------|
| `critical` | Blocks implementation | Must fix before proceeding |
| `high` | Significant gap | Should fix before proceeding |
| `medium` | Minor improvement | Can proceed, address later |

## Taxonomy Areas

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

---

## Edge Case Playbook

### Timeout Handling

Configured reviewer timeout or error: retain completed reports, apply the [canonical result gate](../../review/reference/harnesses.md#results), and deliberately redispatch only missing reports for the same wave.

### Parse Failures

**YAML not found:** Search for partial YAML, attempt parse, mark as failed if not found.
**Malformed YAML:** Report which reviewer failed, include raw output snippet, continue with parseable reviewers.

### No Reviewers Selected

Return to the scope reviewer-configuration step and resolve the selection under [peer routing](../../peer/reference/routing.md).

### Scope Not Found

List available scopes, ask user to specify. Suggest closest match for typos.

### Conflicting Reviews

Gate status = FAIL (conservative). Show which reviewers failed. Include all completed perspectives,
deduplicate by semantic similarity, and record the actual reviewer aliases in `found_by`.
