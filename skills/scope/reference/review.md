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

1. Parse scope name from argument (e.g., `/scope review auth-system`)
2. **Locate scope:** If name provided, search `scopes/{draft,active,done}/<name>/`. If no argument: find most recent `scope.md` under `scopes/*/*/`.
3. Read scope documents: `scope.md`, `tasks.yaml`, `validation.yaml`, and `design.md` (if present)

### Step 2: Select Reviewers

Select reviewers per the unified `/review` host matrix and live registry metadata:

- Codex host: native `codex-native`; cross-host Claude family through peer
  (`opus-cli`/`sonnet-cli`); reject native `opus`/`sonnet` and every registry Codex-family peer
  alias.
- Claude host: native `opus`/`sonnet`; cross-host GPT/Codex family through peer; reject
  `codex-native` and every registry Claude-family peer alias.
- Allow unrelated peer families when available. Never silently convert an incompatible selection.

All-native selections use effort `inherit`. If any peer is selected, choose an explicit effort
supported by every selected peer. Validate `opus-cli`/`sonnet-cli` against their contract subset
`low|medium|high|xhigh|max`; in mixed sets the effort applies only to peers and native dispatches
inherit.

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

Append the exact Reviewer Report schema from this document to the materialized prompt, then save it
as `.reviews/scope-<name>/prompt.md`.

**In a single message**, dispatch the configured mechanisms:

```
Codex native delegation(role=reviewer, prompt={review_prompt})  # codex-native on Codex
Task(subagent_type="reviewer", model={native_alias}, prompt={review_prompt})  # opus/sonnet on Claude
Bash(run_in_background=true):                                  # only when externals configured
  peer -C {workdir} -d .reviews/scope-{name} --agent reviewer \
    --peers {external_aliases} --effort {peer_effort} \
    --prompt-file .reviews/scope-{name}/prompt.md
```

Never pass host-native aliases to peer. Read the TSV manifest when peer ran; pull each `ok` report
file and note failed rows. The mandatory gate requires one success from every execution class
actually configured. Full contract: **[review](../../review/SKILL.md)** and
**[peer](../../peer/SKILL.md)**.

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

This review is the **mandatory blocking gate** a scope must clear before implementation (the scope-level analog of the `issue` skill's 2×2 gate before publish). Write the outcome to `validation.yaml` under `review_gate`:

- **No `critical`/`high` issue from any reviewer** → `review_gate.status: passed` (record reviewers, timestamp, `blocking_resolved`, and any deferred `medium` nits). Report "Ready for implementation."
- **Any `critical`/`high` issue** → `review_gate.status: failed`. Report "Address critical/high issues, then re-run /scope review." Fold the findings back into `scope.md` / `tasks.yaml` / `design.md` and re-run until clean.

`implement`/`loop` will not execute a scope whose `review_gate.status` is absent or `failed` (enforced at `implement/operations/execute.md` Step 2).

When invoked standalone (`/scope review <name>`) the same gate semantics apply — a passing run writes `review_gate.status: passed`, unblocking implementation.

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

**Configured reviewer timeout / error:**
1. Keep completed reports and mark the failed agent partial
2. Do not pass the mandatory scope gate until every configured execution class has a success
3. Deliberately redispatch the missing class; never proceed with zero reviews

### Parse Failures

**YAML not found:** Search for partial YAML, attempt parse, mark as failed if not found.
**Malformed YAML:** Report which reviewer failed, include raw output snippet, continue with parseable reviewers.

### No Reviewers Selected

Codex host defaults to `codex-native`; Claude host defaults to native `opus` plus configured
cross-host GPT peers. If neither native mechanism is available, ask for explicit registry aliases.

### Scope Not Found

List available scopes, ask user to specify. Suggest closest match for typos.

### Conflicting Reviews

Gate status = FAIL (conservative). Show which reviewers failed. Include all completed perspectives,
deduplicate by semantic similarity, and record the actual reviewer aliases in `found_by`.
