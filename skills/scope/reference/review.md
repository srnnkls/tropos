# Scope Review Reference

Reviewer roles, harnesses, report schemas, and edge case handling for the review sub-operation.

---

## Reviewer Roles

### Claude Reviewer (Context-Aware)

- Cross-references with similar features in codebase
- Checks against project terminology and patterns
- Verifies dependencies exist, APIs available
- Applies project documentation standards
- Verifies design depth (alternatives substantiated, invariants testable)

**Strengths:** Deep project context, can verify feasibility against actual codebase, catches integration issues.
**Limitations:** Single model perspective, may be anchored by prior context.

### OpenCode Reviewer (Fresh Perspective)

- Evaluates what's missing that a newcomer would need
- Checks terms and concepts for self-consistency
- Validates logical coherence of described tasks
- Tests clarity for unfamiliar readers
- Assesses whether reasoning is self-contained

**Strengths:** Catches assumptions insiders miss, simulates new team member perspective.
**Limitations:** Cannot verify against actual codebase, may flag project conventions as issues.

---

## Harnesses

### Claude Harness (Native Subagent)

```
Task(
  subagent_type="general",
  prompt="[Review prompt with scope content]"
)
```

Always use `subagent_type="general"` for Claude reviewers.

### OpenCode Harness (External Subprocess)

```bash
timeout 1200 opencode run --model "{MODEL}" --variant {reasoning}-medium "[Review prompt]"
```

**Available models:**

| Model | native | github-copilot |
|---|---|---|
| GPT-5.2 | `openai/gpt-5.2` | `github-copilot/gpt-5.2` |
| GPT-5.3 Codex | `openai/gpt-5.3-codex` | `github-copilot/gpt-5.3-codex` |
| Gemini 3 Flash | `google/gemini-3-flash-preview` | `github-copilot/gemini-3-flash` |
| Gemini 3 Pro | `google/gemini-3-pro-preview` | `github-copilot/gemini-3-pro` |

**Reasoning Effort (--variant flag):**
- `low-medium` — Quick responses
- `medium-medium` — Balanced reasoning
- `high-medium` — Deep analysis (recommended for reviews)
- `xhigh-medium` — Maximum reasoning (GPT-5.2 only)

---

## Report Schema

### Reviewer Report

```yaml
reviewer_report:
  reviewer: claude-opus | opencode-gpt5.2
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
  reviewers: [claude-opus, opencode-gpt5.2]
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
      found_by: [claude-opus, opencode-gpt5.2]
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

**OpenCode timeout (> 20 minutes):**
1. Continue with completed reviews
2. Add warning: "[Reviewer] timed out, partial results"
3. Proceed with synthesis using available data

**Claude subagent timeout:**
1. If OpenCode succeeded: use OpenCode results only
2. If both failed: report failure, suggest retry
3. Never proceed with zero reviews

### Parse Failures

**YAML not found:** Search for partial YAML, attempt parse, mark as failed if not found.
**Malformed YAML:** Report which reviewer failed, include raw output snippet, continue with parseable reviewers.

### No Reviewers Selected

Default to claude-opus only. Warn about single-perspective review.

### Scope Not Found

List available scopes, ask user to specify. Suggest closest match for typos.

### Conflicting Reviews

Gate status = FAIL (conservative). Show which reviewers failed. Include both perspectives. Deduplicate by semantic similarity, mark `found_by: [both]` for higher confidence.
