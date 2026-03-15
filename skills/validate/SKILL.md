---
name: validate
description: Unified validation dispatcher. Auto-detects validation type from argument or presents selection menu. Routes to test, dispatch (verify), or hooks-test.
argument-hint: "[target]"
allowed-tools: Bash(find *), Bash(git status *)
metadata:
  type: generic
---

## Pre-loaded Context

Uncommitted:
!`git status --short 2>/dev/null`

# Validate Dispatcher

Routes to the appropriate validation skill based on argument type.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| Contains "hook" or path to hooks file | Hooks | `Skill(hooks-test, $ARGUMENTS)` |
| Contains "completion", "done", or "verify" | Completion | `Skill(dispatch, verify)` |
| Contains "test" or "tdd" | TDD | `Skill(test)` |
| No argument | Menu fallback | See below |

---

## Menu Fallback

When no argument or ambiguous, use **AskUserQuestion**:

```
Header: Validate
Question: What would you like to validate?
multiSelect: false
Options:
- TDD: RED-GREEN-REFACTOR test-driven development
- Completion: Evidence-based verification before claiming done
- Hooks: Test Claude Code hooks at unit/integration/e2e levels
```

**Routing by selection:**

| Selection | Action |
|---|---|
| TDD | `Skill(test)` |
| Completion | `Skill(dispatch, verify)` |
| Hooks | `Skill(hooks-test)` |

> **Protocol:** [dispatch/protocol.md](../dispatch/protocol.md)
