---
name: loqui
description: |
  Access language-specific coding guidelines from loqui. Use when implementing code and needing patterns, style guidance, or best practices for Python, Go, Rust, Zig, Bash, or Emacs Lisp.
metadata:
  type: generic
---

# Loqui

Language guidelines for writing code with eloquence and style.

---

## Location

Resolve resources relative to the directory containing this `SKILL.md`:

```
reference/loqui/languages/{language}/
```

This works through the dotfiles deployment in Claude, Codex, and other harnesses. Read the relevant
language README first, then follow its topic links. If `reference/loqui` is missing, restore the
reference using dotfiles deployment or tropos's `mise run loqui-link --path /path/to/loqui` task.

---

## Languages

| Language | Path |
|----------|------|
| Python | `reference/loqui/languages/python/` |
| Go | `reference/loqui/languages/go/` |
| Rust | `reference/loqui/languages/rust/` |
| Zig | `reference/loqui/languages/zig/` |
| Bash | `reference/loqui/languages/bash/` |
| Emacs Lisp | `reference/loqui/languages/elisp/` |

---

## Structure

Each language directory follows this structure:

```
{language}/
├── README.md        # Overview, core principles, anti-patterns checklist
├── quality.md       # Naming, comments, documentation conventions
├── composition.md   # Structuring behavior (classes/functions/modules)
├── modules.md       # Package structure, organization, public APIs
├── errors.md        # Error handling patterns
└── ...              # Additional language-specific resources
```

Start with the README for the working model, priorities, invariants, and topic map. For Zig async/I/O,
read `reference/loqui/languages/zig/async-io.md` and verify APIs against the consuming project's
pinned compiler; do not substitute remembered APIs from another Zig release.

---

## Principles

Shared across all languages:

- Naming over comments — spend 5x more time on names than comments
- Composition over inheritance
- Feature-based organization — group by domain, not technical layer
- Parse at boundaries — accept permissive input, convert to strict types immediately
- Explicit over implicit

---

## Related

- `implement` - Generic implementation methodology
- `test` - TDD workflow
- `code` - Code domain (references loqui for compliance review)
