---
name: doc
description: General reference documents by domain. Use when creating architecture docs, strategy documents, specs, or guides.
metadata:
  type: domain
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Doc
          short_description: Apply the canonical doc skill workflow
          default_prompt: Use $doc for the requested task.
---

<!-- Generated from skills/doc/SKILL.md by henia build; edit the canonical source. -->

# Docs Implement Skill

Domain-specific reference documents for non-code artifacts.

---

## Domains

| Domain | Purpose |
|--------|---------|
| architecture | System design, component diagrams, data flow |
| strategy | Decision frameworks, trade-off analysis |
| specs | API contracts, interface definitions |
| guides | How-to documentation, playbooks |

:::related
- `implement` — language-specific coding guidelines
- `scope` — scope documents with validation
:::
