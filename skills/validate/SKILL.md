---
name: validate
description: Unified validation dispatcher. Auto-detects validation type from argument or presents selection menu. Routes to test, implement (verify), or, on Claude Code with the hooks-test skill installed, hooks-test.
metadata:
  type: generic
henia:
  targets:
    claude:
      frontmatter:
        argument-hint: '[target]'
        allowed-tools: Bash(find *), Bash(git status *)
    codex:
      openai:
        interface:
          display_name: Validate
          short_description: Apply the canonical validate skill workflow
          default_prompt: Use $validate for the requested task.
---

<!-- Generated from skills/validate/SKILL.md by henia build; edit the canonical source. -->

## Context

Uncommitted:
!`git --no-optional-locks status --short 2>/dev/null || true`

# Validate Dispatcher

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| Contains "hook" or path to hooks file | Hooks | `Skill(hooks-test, $ARGUMENTS)` on Claude Code with `hooks-test` installed; otherwise the menu fallback |
| Contains "completion", "done", or "verify" | Completion | `Skill(implement, verify)` |
| Contains "test" or "tdd" | TDD | `Skill(test)` |
| No argument | Menu fallback | See below |

---

## Menu Fallback

When no argument or ambiguous, use `AskUserQuestion`:

```
Header: Validate
Question: What would you like to validate?
multiSelect: false
Options:
- TDD: RED-GREEN-REFACTOR test-driven development
- Completion: Evidence-based verification before claiming done
- Hooks: Test Claude Code hooks at unit/integration/e2e levels (only when `hooks-test` is available)
```

| Selection | Action |
|---|---|
| TDD | `Skill(test)` |
| Completion | `Skill(implement, verify)` |
| Hooks | `Skill(hooks-test)` |

> Protocol: [dispatch/protocol.md](../dispatch/protocol.md)
