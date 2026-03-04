---
name: validate
description: Unified validation dispatcher. Auto-detects validation type from argument or presents selection menu. Routes to spec-validate, code-test, task-completion-verify, or hooks-test.
argument-hint: "[target]"
allowed-tools: Bash(find *), Bash(git status *)
---

## Pre-loaded Context

Draft specs:
!`find ./specs/draft -maxdepth 1 -mindepth 1 -type d 2>/dev/null`

Active specs:
!`find ./specs/active -maxdepth 1 -mindepth 1 -type d 2>/dev/null`

Uncommitted:
!`git status --short 2>/dev/null`

# Validate Dispatcher

Routes to the appropriate validation skill based on argument type.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Invocation |
|---|---|---|
| Matches `./specs/draft/*/` or `./specs/active/*/` | Requirements | `Skill(spec-validate)` |
| Contains "hook" or path to hooks file | Hooks | `Skill(hooks-test, $ARGUMENTS)` |
| Contains "completion", "done", or "verify" | Completion | `Skill(task-completion-verify)` |
| Contains "test" or "tdd" | TDD | `Skill(code-test)` |
| No argument | Menu fallback | See below |

---

## Menu Fallback

When no argument or ambiguous, use **AskUserQuestion**:

```
Header: Validate
Question: What would you like to validate?
multiSelect: false
Options:
- Requirements: Clarify requirements through structured questioning
- TDD: RED-GREEN-REFACTOR test-driven development
- Completion: Evidence-based verification before claiming done
- Hooks: Test Claude Code hooks at unit/integration/e2e levels
```

**Routing by selection:**

| Selection | Action |
|---|---|
| Requirements | `Skill(spec-validate)` |
| TDD | `Skill(code-test)` |
| Completion | `Skill(task-completion-verify)` |
| Hooks | `Skill(hooks-test)` |

---

## Delegation Pattern

1. Check `$ARGUMENTS` against auto-detect rules (in order)
2. If match: invoke target skill directly
3. If no match: present AskUserQuestion menu
4. Based on selection: invoke target skill
5. Target skill handles any further interaction

Do NOT duplicate target skill logic. Only route.
