# Reviewer Role

Multi-agent review of batch implementations. Multiple reviewers run in parallel for diverse perspectives.

## Roles × Harnesses

**All role × harness combinations dispatch in parallel (SINGLE message).**

### Roles

| Role | Primary Gates | Focus | Skill |
|------|---------------|-------|-------|
| **General** | Correctness, Security, Performance | Logic, edge cases, vulnerabilities | `code` review |
| **Architecture** | Architecture | Coupling, hotspots, cycles, seams, impact | `gestalt` |
| **Compliance** | Style | Naming, composition, modules, error patterns | `loqui` |

### Harnesses

See `/review` [reference/harnesses.md](../../../review/reference/harnesses.md) for harness details and dispatch templates.

### Roles × Harnesses

Full cartesian product: every role dispatches on every harness.

| Role | Claude | Pi |
|------|--------|----------|
| General | 1 (required) | 0-N (from validation.yaml) |
| Architecture | 1 (required) | 0-N (from validation.yaml) |
| Compliance | 1 (required) | 0-N (from validation.yaml) |

**Available models:** See `/review` [reference/models.md](../../../review/reference/models.md).

**CRITICAL:** Dispatch all role × harness combinations in the same message for true parallelism.

## Purpose

Reviewers check the **diff of changes** from a batch, ensuring quality and scope compliance before proceeding to the next batch.

**This is Phase C of the Three-Phase Pipeline.** It is mandatory - no batch completes without review.

**Key:** Reviewers work with the git diff, not full file contents. This keeps reviews focused and efficient.

## Skills to Invoke

**General reviewer:**
- **First:** Invoke `code` review skill for review methodology
- **Second:** Invoke `implement` skill for language-specific patterns

**Architecture reviewer:**
- **First:** Invoke `gestalt` skill for code intelligence commands
- Run `gestalt analyze`, `gestalt diff`, and additional commands as needed

**Compliance reviewer:**
- **First:** Invoke `loqui` skill for language guidelines
- Read loqui resources for each language detected in the diff

## Input

Each reviewer receives:

**1. Batch diff (primary input):**
```diff
# git diff <last_batch_commit>..HEAD
diff --git a/src/feature_a.py b/src/feature_a.py
new file mode 100644
...
```

**2. Implementer reports (context):**
```yaml
# Task N1
implementer_report:
  status: success
  implementation_files: [src/feature_a.py]
  test_output: "3 passed"

# Task N2
implementer_report:
  status: success
  implementation_files: [src/feature_b.py]
  test_output: "2 passed"
```

**3. Task specs from tasks.yaml (requirements)**

## Responsibilities

1. Review all changes from the batch together
2. Evaluate against five gates (Correctness, Style, Performance, Security, Architecture)
3. Check each task against its spec requirements
4. Verify tests cover the implementation
5. Identify issues by severity
6. Report with actionable feedback

## Dispatch Configuration

Dispatch per `/review` infrastructure. See `/review` [reference/harnesses.md](../../../review/reference/harnesses.md) for dispatch templates.

All Pi models and reasoning effort configured in `validation.yaml` under `review_config`.
Review prompts per role: see `code` review skill Step 4.

## When Reviewers Run

**After ALL implementers in a batch complete** - as Phase C of the pipeline.

```
Batch N:
├── Phase A: Testers (parallel)
├── Phase B: Implementers (parallel)
└── Phase C: Reviewers (roles × harnesses in parallel) ← this role
    ├── General × Claude [required]
    ├── General × Pi (0-N from validation.yaml)
    ├── Architecture × Claude [required]
    ├── Architecture × Pi (0-N from validation.yaml)
    ├── Compliance × Claude [required]
    └── Compliance × Pi (0-N from validation.yaml)
```

## Report Format

**OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
No prose, no explanation, no summary of what you did. The full subagent conversation
gets embedded into the parent session context — every extra token costs budget.

Each reviewer produces a YAML report with gates:

```yaml
reviewer_report:
  reviewer: general-claude-opus  # or general-pi-gpt5.5, general-pi-gemini-3-pro, architecture-claude-opus, compliance-claude-opus
  gates:
    correctness:
      status: pass | fail
      issues: ["Logic error in X"]
    style:
      status: pass | fail
      issues: []
    performance:
      status: pass | fail
      issues: []
    security:
      status: pass | fail
      issues: ["SQL injection risk"]
    architecture:
      status: pass | fail
      issues: []
  issues:
    - task: N1
      severity: critical | high | medium
      gate: security
      location: "src/db/query.py:45"
      description: "SQL injection via unsanitized input"
      suggestion: "Use parameterized queries"
  strengths:
    - "Good test coverage for edge cases"
    - "Clean separation of concerns"
```

## Synthesizing Multiple Reviews

Synthesize per `/review` [reference/synthesis.md](../../../review/reference/synthesis.md): parse reports, group by role, merge issues, aggregate gates and severity.

**Gate Summary Table (by role):**

```
| Gate         | Status | General              | Architecture | Compliance |
|--------------|--------|----------------------|--------------|------------|
| Correctness  | PASS   | pass          | —            | —          |
| Style        | FAIL   | —             | —            | fail       |
| Performance  | PASS   | pass          | pass         | —          |
| Security     | FAIL   | fail (Claude) | —            | —          |
| Architecture | PASS   | —             | pass         | —          |
```

`—` = not in scope for this role. On failure, parenthetical = which harness(es) failed.

**Structural Analysis (Architecture role):**

```
Coupling: stable | New hotspots: 0 | Cycles: 0 | Impact radius: 3
```

**Compliance Analysis (Compliance role):**

```
Languages: python | Rules: 12 | Violations: 1
```

**Issues by Severity:**

```
## Critical (found by 2+ harnesses — high confidence)
- [C1] SQL injection at src/db/query.py:45
  Role: General | Found by: Claude, Gemini
  Suggestion: Use parameterized queries

## High
- [H1] Missing null check at src/api/handler.ts:112
  Role: General | Found by: Codex
  Suggestion: Add guard clause

## Medium
- [M1] Variable 'd' should have descriptive name (naming/5x-rule)
  Role: Compliance | Rule: python/quality.md
  Suggestion: Rename to 'duration_seconds'
```

## Issue Severity

| Severity | Definition | Action |
|----------|------------|--------|
| Critical | Bugs, security issues, data corruption | Fix immediately before next batch |
| High | Significant issues, missing coverage | Fix before next batch |
| Medium | Style, naming, small improvements | Note for later, proceed |

## Handling Timeouts

If Pi reviewer times out (> 5 minutes):

1. Continue with completed reviews (minimum 1 Claude required)
2. Note: "[Reviewer] timed out, partial results"
3. Proceed with available data
4. Consider re-running if critical issues suspected

## Quality Criteria

Review is good when it:
- Evaluates all five gates
- Covers all tasks in the batch
- Provides actionable feedback (not vague)
- Prioritizes issues by severity
- Acknowledges strengths
- Includes file/line references

## Example

**Batch:** Tasks T002, T003, T004 (parallel)

**Dispatch (single message, full cartesian product):**
```
# 3 roles × Claude
Task(general): "General review: batch T002-T004" ...
Task(general): "Architecture review: batch T002-T004" ...
Task(general): "Compliance review: batch T002-T004" ...
# 3 roles × Pi model 1
Bash(background): pi -p --model openai-codex/gpt-5.5 --thinking {reasoning_effort} "General review: ..."
Bash(background): pi -p --model openai-codex/gpt-5.5 --thinking {reasoning_effort} "Architecture review: ..."
Bash(background): pi -p --model openai-codex/gpt-5.5 --thinking {reasoning_effort} "Compliance review: ..."
# 3 roles × Pi model 2
Bash(background): pi -p --model google-gemini-cli/gemini-3.1-pro-preview --thinking {reasoning_effort} "General review: ..."
Bash(background): pi -p --model google-gemini-cli/gemini-3.1-pro-preview --thinking {reasoning_effort} "Architecture review: ..."
Bash(background): pi -p --model google-gemini-cli/gemini-3.1-pro-preview --thinking {reasoning_effort} "Compliance review: ..."
```

**Individual Outputs:**

Claude (General):
```yaml
reviewer_report:
  reviewer: general-claude-opus
  gates:
    correctness: { status: fail, issues: ["Missing null check"] }
    style: { status: pass, issues: [] }
    performance: { status: pass, issues: [] }
    security: { status: fail, issues: ["SQL injection"] }
    architecture: { status: pass, issues: [] }
  issues:
    - task: T002
      severity: critical
      gate: security
      location: "src/db/query.py:45"
      description: "SQL injection via unsanitized input"
      suggestion: "Use parameterized queries"
```

Pi Gemini (General):
```yaml
reviewer_report:
  reviewer: general-pi-gemini-3-pro
  gates:
    correctness: { status: pass, issues: [] }
    style: { status: pass, issues: [] }
    performance: { status: pass, issues: [] }
    security: { status: fail, issues: ["Unsanitized query parameter"] }
    architecture: { status: pass, issues: [] }
  issues:
    - task: T002
      severity: critical
      gate: security
      location: "src/db/query.py:45"
      description: "Query parameter not sanitized"
      suggestion: "Add input validation"
```

**Synthesized:**
```
## Gate Summary
| Gate         | Status | General              | Architecture | Compliance |
|--------------|--------|----------------------|--------------|------------|
| Correctness  | FAIL   | fail (Claude)        | —            | —          |
| Style        | PASS   | —                    | —            | pass       |
| Security     | FAIL   | fail (Claude, Gemini)| —            | —          |
| Performance  | PASS   | pass                 | pass         | —          |
| Architecture | PASS   | —                    | pass         | —          |

## Critical (2 reviewers agree)
- [C1] SQL injection at src/db/query.py:45
  Found by: general-claude-opus, general-pi-gemini-3-pro
  Fix: Use parameterized queries + input validation

Action: Dispatch fix subagent before proceeding
```
