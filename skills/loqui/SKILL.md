---
name: loqui
description: |
  Access language-specific coding guidelines from loqui. Use when implementing code and needing patterns, style guidance, or best practices for Python, Go, Rust, or Bash.
---

# Loqui

Language guidelines for writing code with eloquence and style.

---

## Location

Loqui resources are deployed as part of the `code-implement` skill:

```
~/.claude/skills/code-implement/resources/loqui/languages/{language}/
```

**Use Read tool** (not Glob) to access - paths outside cwd require direct reads.

---

## Languages

| Language | Path |
|----------|------|
| Python | `~/.claude/skills/code-implement/resources/loqui/languages/python/` |
| Go | `~/.claude/skills/code-implement/resources/loqui/languages/go/` |
| Rust | `~/.claude/skills/code-implement/resources/loqui/languages/rust/` |
| Bash | `~/.claude/skills/code-implement/resources/loqui/languages/bash/` |

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
2. Read `~/.claude/skills/code-implement/resources/loqui/languages/{language}/README.md`
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

- `code-implement` - Primary skill for implementation (includes loqui)
- `code-test` - TDD workflow
- `code-review` - Review methodology
