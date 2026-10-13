---
name: bash
description: Ultra-concise bash command patterns. Use when constructing shell commands or one-liners.
metadata:
  type: generic
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Bash
          short_description: Apply the canonical bash skill workflow
          default_prompt: Use $bash for the requested task.
---

# Bash Use Skill

## Quick Reference

- Quote paths with spaces: `cd "/path with spaces/dir"`.
- Delete with `trash ./build`, never `rm`.
- Chain with `&&` to stop on failure; use `;` only to continue regardless.
- Substitute with `result=$(command)`, never backticks.
- Check a command exists: `command -v jq &>/dev/null || echo "not found"`.
- `2>&1` sends stderr to stdout; `&>/dev/null` suppresses all output.
- Process substitution: `diff <(cmd1) <(cmd2)`.

## Full Guidelines

`henia show loqui/languages/bash/reference/commands.md`

:::related
- `code` — language style through `code.style` providers, bash included
- `test` — TDD workflow
:::
