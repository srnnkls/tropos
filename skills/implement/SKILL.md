---
name: implement
description: Scope execution pipeline and implementation methodology. Use for executing scopes (TDD three-phase pipeline), verifying completion, debugging, or building features from requirements.
argument-hint: "[target]"
metadata:
  type: generic
---

## Pre-loaded Context

Active scopes:
!`find scopes -maxdepth 2 -name scope.md 2>/dev/null`

Checkpoints:
!`find scopes -name checkpoint.yaml -maxdepth 2 2>/dev/null`

Git status:
!`git status --short 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

# Implementation & Scope Execution

Executes scopes and tasks via three-phase TDD pipeline (tester → implementer → reviewer).

**INVARIANT: The orchestrator NEVER writes code or tests.** All code authoring — including test code — MUST be delegated to fresh subagents. This applies to ALL routes: scope execution, single tasks, file paths, and task descriptions. No exceptions.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| "verify" or "done" | Verify | Read and follow `operations/verify.md` |
| "debug" or "trace" | Debug | Read and follow `operations/debug.md` |
| Matches `./scopes/*/` path | Execute | Read and follow `operations/execute.md` |
| Exactly one active scope | Execute | Read and follow `operations/execute.md` |
| File path or task description | Direct | Use methodology below |
| No argument | Menu | See fallback |

---

## Menu Fallback

When no argument or ambiguous, use **AskUserQuestion**:

```
Header: Implement
Question: What would you like to do?
multiSelect: false
Options:
- Scope execution: Execute active scope with TDD pipeline (tester → implementer → reviewer)
- Verify: Evidence-based verification before claiming done
- Debug: Root cause tracing for a bug or failure
- Implement: Single implementation task with methodology below
```

**Routing by selection:**

| Selection | Action |
|---|---|
| Scope execution | Read and follow `operations/execute.md` |
| Verify | Read and follow `operations/verify.md` |
| Debug | Read and follow `operations/debug.md` |
| Implement | Use methodology below |

---

## When to Use

- Executing a scope's tasks via three-phase pipeline
- Building features from requirements
- Writing code or creating artifacts
- Deciding on structure, patterns, or approach
- Designing domain models or data structures
- Verifying completion or debugging failures

---

## Git Workflow

When implementing from a spec:

1. **Create a branch for the scope** (if not already on one):
   - Branch from main/master
   - Name: `feat/<scope-name>`
   - Example: `feat/user-auth` for `./scopes/user-auth/`

2. **Verify before starting:**
   - Confirm you're on the correct scope branch
   - Pull latest if branch already exists

---

## Process (Single-Task Pipeline)

**The orchestrator NEVER writes code or tests.** All code authoring is delegated to subagents.

Even for a single task, the four-phase pipeline applies:

### Phase A: Dispatch Tester Subagent

Dispatch a **fresh tester subagent** (`subagent_type: "general"`) to write failing tests.

- Tester reads task requirements and discovers expected behavior independently
- Tester writes tests and verifies RED state
- Orchestrator verifies RED (see Quality Gates in `operations/execute.md`)

**Why a separate subagent?** The orchestrator's understanding of the task leaks into hand-written tests, causing oracle mirroring (tests that mirror implementation logic) and mock tautologies (mocks that assume the answer). A fresh subagent discovers behavior from code and specs independently.

### Phase A.5: Test Review Gate

Dispatch a **fresh test reviewer subagent** on the test files from Phase A.

- Reviewer checks for oracle mirroring, mock tautologies, framework tests, trivial assertions
- If issues found → re-dispatch tester with specific feedback; repeat until clean
- **Gate:** Implementer NEVER receives tests that failed this review

See dispatch template in `reference/subagent-workflow.md`.

### Phase B: Dispatch Implementer Subagent

Dispatch a **fresh implementer subagent** (`subagent_type: "general"`) with the test-review-cleared tester report.

- Implementer makes tests pass (GREEN)
- Implementer refactors while staying green

### Phase C: Review

For single tasks, review can be done inline or via reviewer subagent(s) depending on scope.

### Dispatch Templates

Use the tester and implementer dispatch templates from `reference/subagent-workflow.md`.

### Red Flags

**If you catch yourself writing test code or implementation code directly: STOP.**
You are the orchestrator. You dispatch. You verify. You do not author.

---

## Domain Context

Domain skills inject specifics into this generic methodology:
- **code**: Language guidelines (loqui), code intelligence (gestalt), review roles
- **doc**: Templates, structure, style guides

When invoked via a domain skill, follow the domain-specific guidance provided.

---

## Related Skills

- **dispatch**: Intent router — routes to this skill for execution
- **test**: TDD workflow (write test first, then implement)
- **continue**: Resume from checkpoint
- **review**: Review methodology for completed work

---

## Reference

- [operations/execute.md](operations/execute.md) — Three-phase scope execution pipeline
- [operations/verify.md](operations/verify.md) — Evidence-based completion verification
- [operations/debug.md](operations/debug.md) — Root cause tracing
- [reference/report.md](reference/report.md) — Report format
- [reference/review.md](reference/review.md) — Review workflow
- [reference/checkpoint-format.md](reference/checkpoint-format.md) — Checkpoint format
- [reference/subagent-workflow.md](reference/subagent-workflow.md) — Subagent workflow
- [reference/parallel-detection.md](reference/parallel-detection.md) — Parallel detection
- [reference/defense-in-depth.md](reference/defense-in-depth.md) — Defense in depth
- [reference/root-cause-tracing.md](reference/root-cause-tracing.md) — Root cause tracing
- [reference/roles/](reference/roles/) — Tester, implementer, reviewer role definitions
