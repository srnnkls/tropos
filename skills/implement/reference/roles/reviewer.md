# Reviewer Role

Multi-agent review of batch implementations. Multiple reviewers run in parallel for diverse perspectives.

## Roles × Harnesses

**Per role, dispatch configured host-native reviewers plus an external `peer` fan-out when
configured, in parallel (SINGLE message).**

### Roles

| Role | Primary Gates | Focus | Skill |
|------|---------------|-------|-------|
| **General** | Correctness, Security, Performance | Logic, edge cases, vulnerabilities | `code` review |
| **Architecture** | Architecture | Coupling, hotspots, cycles, seams, impact | `gestalt` |
| **Compliance** | Style | Naming, composition, modules, error patterns | `loqui` |

### Harnesses

See `/review` [reference/harnesses.md](../../../review/reference/harnesses.md) for harness details and dispatch templates.

### Roles × Harnesses

Every role is reviewed by the agents in the live scope configuration. Per role, that is Codex
delegation for `codex-native`, one Task per configured Claude-host-native alias, and one
`peer --agent reviewer` fan-out only when external aliases are configured.

| Role | Host-native | External (via `peer`) |
|------|-------------|-----------------------|
| General | configured Codex delegation / Claude Tasks | configured external reviewer aliases |
| Architecture | configured Codex delegation / Claude Tasks | configured external reviewer aliases |
| Compliance | configured Codex delegation / Claude Tasks | configured external reviewer aliases |

**Registry / models:** `peer list` (see the [peer skill](../../../peer/SKILL.md)).

**CRITICAL:** Per role, dispatch all configured host-native calls and any external `peer` in the
same message. Never pass `codex-native`, `opus`, or `sonnet` to peer; `opus-cli`/`sonnet-cli` are
distinct external aliases.

## Purpose

Reviewers check the **materialized diff of changes** from a batch, ensuring quality and scope
compliance before proceeding. Every prompt embeds the diff, requirements, and exact report schema;
git commands/workdir are optional aids for shell-capable reviewers, not required inputs.

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

**4. Exact reviewer YAML report schema**

**5. Verbatim finding bar** — [`/review` reference/finding-bar.md](../../../review/reference/finding-bar.md)

## Responsibilities

1. Review all changes from the batch together
2. Evaluate against five gates (Correctness, Style, Performance, Security, Architecture)
3. Check each task against its spec requirements
4. Verify tests cover the implementation
5. Identify issues by severity
6. Report with actionable feedback

## Dispatch Configuration

Immediately before dispatching each Phase C role, re-read the scope's `config.yaml` and resolve
`routing.reviewer.agents` plus `routing.reviewer.effort`. This live configuration is the only
execution-routing source; never use `checkpoint.yaml` or `validation.yaml.review_config`.

Dispatch `codex-native` through Codex native delegation with inherited settings. Dispatch
`opus`/`sonnet` through `Task(subagent_type="reviewer", model=<alias>, ...)`. Dispatch all external
aliases (`gpt`, `gemini`, `opus-cli`, `sonnet-cli`, and other peer registry entries) together only
when configured:

Filter these choices through the strict host matrix: Codex rejects registry Codex-family peer
aliases in favor of `codex-native`; Claude rejects registry Claude-family peer aliases in favor of
native `opus`/`sonnet`. Cross-family peers remain valid; never silently convert config.

```bash
peer -C <workdir> -d <role-outdir> --agent reviewer \
  --peers <external-aliases> --effort <routing.reviewer.effort> \
  --prompt-file <role-outdir>/prompt.md
```

Use `<role-outdir>=$(peer path <scope> b<batch>-review-<role> --run <run>)`. Record the
reviewers actually used in `review.yaml`. A config edit affects the next dispatch, not reviewers
already running. Materialize the batch diff, requirements, schema, and finding bar into each role
prompt so a shell-less peer can complete it; save that prompt as `<role-outdir>/prompt.md` before
dispatch.

## When Reviewers Run

**After ALL implementers in a batch complete** - as Phase C of the pipeline.

```
Batch N:
├── Phase A:   Testers (parallel)
├── Phase A.5: Test review gate (configured host-native and/or peer reviewers)
├── Phase B:   Implementers (parallel)
└── Phase C:   Reviewers (per role: configured host-native and/or external dispatch) ← this role
    ├── General      — configured reviewer agents
    ├── Architecture — configured reviewer agents
    └── Compliance   — configured reviewer agents
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

`peer --agent reviewer` owns the idle-stall watchdog, retry-once, and skip; the caller reads `peer`'s
per-reviewer manifest status and synthesizes what landed. The gate requires at least one success
from every execution class actually configured; note skipped reviewers as partial results and
pause when the configured-class minimum is not met. Exit codes and details:
**[peer skill](../../../peer/SKILL.md)**.

## Example

**Batch:** Tasks T002, T003, T004 (parallel)

**Dispatch (single message):** per role, configured host-native dispatches plus one `peer` when
external aliases are configured. See **[peer skill](../../../peer/SKILL.md)**.
```
# Per role (General / Architecture / Compliance):
Codex native delegation(role=reviewer): "{role} review: batch T002-T004" ...
Task(subagent_type="reviewer", model={native_alias}): "{role} review: batch T002-T004" ...
Bash(background): peer -C {workdir} -d {role_outdir} --agent reviewer --peers {external_aliases} --effort {reasoning_effort} --prompt-file {role_outdir}/prompt.md
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
