# Scope Review

Multi-perspective scope review using parallel subagent dispatch.

---

## When to Use

- After creation to validate before implementation
- When scope feels incomplete or ambiguous
- Before `implement` for Initiatives
- Standalone review of existing scopes

---

## Workflow

### Step 1: Identify Scope

1. Parse scope name from argument (e.g., `/scope review auth-system`)
2. **Locate scope:** If name provided, search `scopes/{draft,active,done}/<name>/`. If no argument: find most recent `scope.md` under `scopes/*/*/`.
3. Read scope documents: `scope.md`, `tasks.yaml`, `validation.yaml`, and `design.md` (if present)

### Step 2: Select Reviewers

Select reviewers per `/review` infrastructure. See `/review` SKILL.md "Reviewer Selection (Interactive)" for prompts and model mapping.

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
Return a YAML reviewer_report (see Report Schema below).
```

**In a single message**, dispatch the Claude subagent and `peer` together:

```
Task(subagent_type="general", prompt={review_prompt})              # Claude — agent-native
Bash(run_in_background=true):                                      # codex + gemini — peer fans out (agentic)
  peer -d {outdir} --reviewers {external_aliases} --effort {reasoning} "{review_prompt}"
```

Read the TSV manifest `peer` prints; pull each `ok` report file, skip `stalled`/`error`/`auth` rows (note them as partial results). Full contract in the **[peer skill](../../../peer/SKILL.md)**.

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

### Step 8: Recommend Action

All gates pass → "Ready for implementation." Issues found → "Address critical/high issues, re-run /scope review."

---

## Reviewer Roles

### Claude Reviewer (Context-Aware)

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

See `/review` for harness details, models, and dispatch templates:
- [reference/harnesses.md](../../review/reference/harnesses.md) — dispatch configuration
- [reference/models.md](../../review/reference/models.md) — available models and reasoning levels

---

## Report Schema

Base report format: see `/review` [reference/report.md](../../review/reference/report.md).

Scope reviews use domain-specific gates and areas instead of the code review gates.

### Reviewer Report

```yaml
reviewer_report:
  reviewer: claude-opus | codex-gpt5.5
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
  reviewers: [claude-opus, codex-gpt5.5]
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
      found_by: [claude-opus, codex-gpt5.5]
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

**Codex timeout / error:**
1. Continue with completed reviews
2. Add warning: "[Reviewer] timed out or errored, partial results"
3. Proceed with synthesis using available data

**Claude subagent timeout:**
1. If Codex succeeded: use Codex results only
2. If both failed: report failure, suggest retry
3. Never proceed with zero reviews

### Parse Failures

**YAML not found:** Search for partial YAML, attempt parse, mark as failed if not found.
**Malformed YAML:** Report which reviewer failed, include raw output snippet, continue with parseable reviewers.

### No Reviewers Selected

Default to claude-opus only.

### Scope Not Found

List available scopes, ask user to specify. Suggest closest match for typos.

### Conflicting Reviews

Gate status = FAIL (conservative). Show which reviewers failed. Include both perspectives. Deduplicate by semantic similarity, mark `found_by: [both]` for higher confidence.
