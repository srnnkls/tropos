---
name: loqui
description: |
  Access language-specific coding guidelines from loqui. Use when implementing code and needing patterns, style guidance, or best practices for Python, Go, Rust, or Bash.
metadata:
  type: generic
---

# Loqui

Language guidelines for writing code with eloquence and style.

---

## Location

Loqui resources are in this skill's directory:

```
~/.claude/skills/loqui/reference/loqui/languages/{language}/
```

**Use Read tool** (not Glob) to access - paths outside cwd require direct reads.

---

## Languages

| Language | Path |
|----------|------|
| Python | `~/.claude/skills/loqui/loqui/languages/python/` |
| Go | `~/.claude/skills/loqui/loqui/languages/go/` |
| Rust | `~/.claude/skills/loqui/loqui/languages/rust/` |
| Bash | `~/.claude/skills/loqui/loqui/languages/bash/` |

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

**Start with the README** for quick reference and core principles.

---

## Workflow

1. Identify the target language
2. Read `~/.claude/skills/loqui/reference/loqui/languages/{language}/README.md`
3. Consult specific topic files as needed (composition, errors, modules, etc.)
4. Apply patterns to implementation

---

## Principles

Shared across all languages:

- **Naming over comments** - Spend 5x more time on names than comments
- **Composition over inheritance** - Even in languages that support inheritance
- **Feature-based organization** - Group by domain, not technical layer
- **Parse at boundaries** - Accept permissive input, convert to strict types immediately
- **Explicit over implicit** - Make intent clear through code structure

---

## Related

- `implement` - Generic implementation methodology
- `test` - TDD workflow
- `code` - Code domain (references loqui for compliance review)
