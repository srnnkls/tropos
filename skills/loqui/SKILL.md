---
name: loqui
description: |
  Access language-specific coding guidelines from loqui. Use when implementing code and needing patterns, style guidance, or best practices for Python, Go, Rust, Zig, Bash, or Emacs Lisp.
metadata:
  type: generic
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Loqui
          short_description: Apply the canonical loqui skill workflow
          default_prompt: Use $loqui for the requested task.
---

<!-- Generated from skills/loqui/SKILL.md by henia build; edit the canonical source. -->

# Loqui

Language guidelines for writing code with eloquence and style.

---

## Location

Resolve resources relative to the directory containing this `SKILL.md`:

```
reference/loqui/languages/{language}/
```

Phora deploys the Loqui dependency alongside the compiled skill. Read the relevant language README
first, then follow its topic links.

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
