---
name: dispatch
description: Intent router. Auto-detects execution mode from context and routes to the appropriate skill.
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

# Intent Router

Routes user intent to the appropriate execution skill.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| "continue" or "resume" | Resume | `Skill(continue, $ARGUMENTS)` |
| "debug" or "trace" | Debug | `Skill(implement, debug $ARGUMENTS)` |
| "test" or "tdd" | TDD | `Skill(test, $ARGUMENTS)` |
| "verify" or "done" | Verify | `Skill(implement, verify $ARGUMENTS)` |
| Matches `./scopes/*/` path | Execute | `Skill(implement, $ARGUMENTS)` |
| Checkpoint in pre-loaded context | Resume | `Skill(continue)` |
| Exactly one active scope (no checkpoint) | Execute | `Skill(implement)` |
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
| Scope execution | `Skill(implement)` |
| Continue | `Skill(continue)` |
| Implement | `Skill(implement)` |
| TDD | `Skill(test)` |
| Verify | `Skill(implement, verify)` |
| Other: debug | `Skill(implement, debug)` |

> **Protocol:** [dispatch/protocol.md](protocol.md)
