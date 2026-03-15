---
name: dispatch
description: Unified execution dispatcher. Auto-detects execution mode from context or presents selection menu. Routes to execute, continue, implement, test, verify, or debug operations.
argument-hint: "[target]"
allowed-tools: Bash(find *), Bash(git status *), Bash(git branch *)
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

# Execution Dispatcher

Routes to the appropriate execution operation or skill based on argument or context.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| "continue" or "resume" | Resume | `Skill(continue, $ARGUMENTS)` |
| "debug" or "trace" | Debug | Read and follow `operations/debug.md` |
| "test" or "tdd" | TDD | `Skill(test, $ARGUMENTS)` |
| "verify" or "done" | Verify | Read and follow `operations/verify.md` |
| Matches `./scopes/*/` path | Execute | Read and follow `operations/execute.md` |
| Checkpoint in pre-loaded context | Resume | `Skill(continue)` |
| Exactly one active scope (no checkpoint) | Execute | Read and follow `operations/execute.md` |
| File path or task description | Implement | `Skill(implement, $ARGUMENTS)` |
| No argument | Menu | See fallback |

---

## Menu Fallback

When no argument or ambiguous, use **AskUserQuestion**:

```
Header: Dispatch
Question: What would you like to execute?
multiSelect: false
Options:
- Scope execution: Execute active scope with TDD pipeline (tester → implementer → reviewer)
- Continue: Resume scope implementation from checkpoint
- Implement: Single implementation task with language guidelines
- TDD: Write failing test first, then implement (RED-GREEN-REFACTOR)
- Verify: Evidence-based verification before claiming done
```

With "Other" covering: debug (root cause tracing).

**Routing by selection:**

| Selection | Action |
|---|---|
| Scope execution | Read and follow `operations/execute.md` |
| Continue | `Skill(continue)` — target skill finds checkpoint |
| Implement | `Skill(implement)` — target skill handles directly |
| TDD | `Skill(test)` — target skill handles directly |
| Verify | Read and follow `operations/verify.md` |
| Other: debug | Read and follow `operations/debug.md` |

> **Protocol:** [dispatch/protocol.md](protocol.md)
