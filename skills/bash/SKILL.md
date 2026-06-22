---
name: bash
description: Ultra-concise bash command patterns. Use when constructing shell commands or one-liners.
metadata:
  type: generic
---

# Bash Use Skill

Patterns for interactive bash commands, one-liners, and CLI usage.

---

## When to Use

- Constructing shell commands
- Writing one-liners
- Interactive CLI usage
- Command debugging or improvement

---

## Quick Reference

Quote paths with spaces:
```bash
cd "/path with spaces/dir"
```

`rm` requires relative paths — absolute paths through `$HOME`, `/`, etc. are blocked:
```bash
rm -rf ./build       # relative: allowed
rm -rf $HOME/build   # absolute: blocked
```

Chain commands:
```bash
cmd1 && cmd2 && cmd3  # Stop on failure
cmd1; cmd2; cmd3      # Continue regardless
```

Command substitution:
```bash
result=$(command)  # Not `command`
```

Check command exists:
```bash
command -v jq &>/dev/null || echo "not found"
```

Output redirection:
```bash
command 2>&1        # Stderr to stdout
command &>/dev/null # Suppress all
```

Process substitution:
```bash
diff <(cmd1) <(cmd2)
```

---

## Full Guidelines

`~/.claude/skills/loqui/reference/loqui/languages/bash/reference/commands.md`

---

## Anti-Patterns Checklist

- ✘ Unquoted paths with spaces
- ✘ Absolute paths with `rm`
- ✘ Using `;` when `&&` is needed
- ✘ Backticks instead of `$()`

---

## Related Skills

- `implement`: Language-specific patterns (includes bash)
- `test`: TDD workflow
