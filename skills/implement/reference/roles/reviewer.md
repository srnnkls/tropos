# Reviewer Role

Multi-agent review of batch implementations. Multiple reviewers run in parallel for diverse perspectives.

## Roles × Harnesses

**Per role, dispatch a Claude `Task` + one `peer` in parallel (SINGLE message).**

### Roles

| Role | Primary Gates | Focus | Skill |
|------|---------------|-------|-------|
| **General** | Correctness, Security, Performance | Logic, edge cases, vulnerabilities | `code` review |
| **Architecture** | Architecture | Coupling, hotspots, cycles, seams, impact | `gestalt` |
| **Compliance** | Style | Naming, composition, modules, error patterns | `loqui` |

### Harnesses

See `/review` [reference/harnesses.md](../../../review/reference/harnesses.md) for harness details and dispatch templates.

### Roles × Harnesses

Every role is reviewed by Claude **and** the configured external reviewers. Per role,
that's one Claude `Task` + one `peer` (which fans the role prompt out to all
external harnesses) — **not** a per-harness list of shell-outs.

| Role | Claude | External (via `peer`) |
|------|--------|---------------------------|
| General | 1 `Task` (required) | codex + gemini, from validation.yaml/defaults |
| Architecture | 1 `Task` (required) | codex + gemini, from validation.yaml/defaults |
| Compliance | 1 `Task` (required) | codex + gemini, from validation.yaml/defaults |

**Registry / models:** `peer list` (see the [peer skill](../../../peer/SKILL.md)).

**CRITICAL:** Per role, dispatch the Claude `Task` + the `peer` in the same message
for true parallelism. Never shell out to codex/gemini directly.

## Purpose

Reviewers check the **diff of changes** from a batch, ensuring quality and scope compliance before proceeding to the next batch. Reviewers work with the git diff, not full file contents.

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

All Codex models and reasoning effort configured in `validation.yaml` under `review_config`.
Review prompts per role: see `code` review skill Step 4.

## When Reviewers Run

**After ALL implementers in a batch complete** - as Phase C of the pipeline.

```
Batch N:
├── Phase A:   Testers (parallel)
├── Phase A.5: Test review gate (Claude Task + one peer)
├── Phase B:   Implementers (parallel)
└── Phase C:   Reviewers (per role: Claude Task + one peer) ← this role
    ├── General      — Claude Task + peer (codex + gemini)
    ├── Architecture — Claude Task + peer (codex + gemini)
    └── Compliance   — Claude Task + peer (codex + gemini)
```

## Report Format

**OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
No prose, no explanation, no summary of what you did. The full subagent conversation
gets embedded into the parent session context — every extra token costs budget.

Each reviewer produces a YAML report with gates:

```yaml
reviewer_report:
  reviewer: {role}-{reviewer-id}  # reviewer-ids from `peer list`
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

`peer` owns the idle-stall watchdog, retry-once, and skip; the caller reads `peer`'s
per-reviewer manifest status and synthesizes what landed (minimum 1 Claude required),
noting any skipped reviewer as partial results. Exit codes and details:
**[peer skill](../../../peer/SKILL.md)**. Never block the pipeline on an external harness.

## Example

**Batch:** Tasks T002, T003, T004 (parallel)

**Dispatch (single message):** per role, a Claude `Task` + one `peer` (peer fans the
role prompt out to every configured external harness). See **[peer skill](../../../peer/SKILL.md)**.
```
# Per role (General / Architecture / Compliance):
Task(general): "{role} review: batch T002-T004" ...
Bash(background): peer -d {role_outdir} --effort {reasoning_effort} "{role} review: ..."
```

**Individual Outputs:**

Claude (General):
```yaml
reviewer_report:
  reviewer: general-{reviewer-id}
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

External (General):
```yaml
reviewer_report:
  reviewer: general-{reviewer-id}
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
  Found by: [{reviewer-id}, …]
  Fix: Use parameterized queries + input validation

Action: Dispatch fix subagent before proceeding
```
