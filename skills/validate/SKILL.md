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

::::head

## Context

Uncommitted:
!`git --no-optional-locks status --short 2>/dev/null || true`

# Validate Dispatcher

:::routes{.ordered .protocol}
| Pattern | Route | Action |
|---|---|---|
| Contains "hook" or path to hooks file | Hooks | `Skill(hooks-test, $ARGUMENTS)` on Claude Code with `hooks-test` installed; otherwise the menu fallback |
| Contains "completion", "done", or "verify" | Completion | `Skill(implement, verify)` |
| Contains "test" or "tdd" | TDD | `Skill(test)` |
| No argument | Menu fallback | See below |
:::

## Menu Fallback

When the argument is missing or ambiguous, ask with `AskUserQuestion`, then run the matching route's action (Hooks: `Skill(hooks-test)`):

:::menu{header="Validate" question="What would you like to validate?"}
- TDD: RED-GREEN-REFACTOR test-driven development
- Completion: Evidence-based verification before claiming done
- Hooks: Test Claude Code hooks at unit/integration/e2e levels (only when `hooks-test` is available)
:::

::::
