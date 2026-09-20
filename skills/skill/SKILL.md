---
name: skill
description: Create canonical multi-harness skills following project patterns and best practices. Use when building new skills, extracting reusable capabilities, or converting commands to skills.
metadata:
  type: domain
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Skill
          short_description: Apply the canonical skill skill workflow
          default_prompt: Use $skill for the requested task.
---

<!-- Generated from skills/skill/SKILL.md by henia build; edit the canonical source. -->

# Skill Creation

Create well-structured skills using progressive disclosure and project conventions.

> **Reference:** [best-practices.md](best-practices.md) for comprehensive guidance, [reference.md](reference.md) for project patterns and frontmatter specs.

---

## Workflow

### Step 1: Understand Use Cases

Gather concrete examples of how the skill will be used:

- What tasks will it handle?
- What would users say to trigger it?
- What variations exist?

Skip this step only when usage patterns are already clearly understood.

### Step 2: Plan Contents

Analyze each use case to identify reusable resources:

| Resource Type | When to Use | Example |
|---------------|-------------|---------|
| `scripts/` | Same code rewritten repeatedly | `rotate_pdf.py` |
| `reference/` | Domain knowledge the agent needs | `schema.md`, `api.md` |
| `assets/` | Files used in output | `template.html`, `logo.png` |
| `templates/` | Document structure patterns | `report.md` |

### Step 3: Choose Frontmatter

**Required fields:**

```yaml
name: skill-name          # Lowercase, hyphens, max 64 chars
description: |            # Max 1024 chars
  [What it does]. Use when [context].
```

**Canonical metadata:**

Keep portable `name`, `description`, `metadata`, `license` and `compatibility` at
the top level. Put harness-specific metadata under `henia.targets.<profile>`.
Use `henia.auto_invoke: false` for explicit-only skills, `henia.variables` for
context inputs, and `henia.targets.codex.openai.interface` for Codex UI metadata.

Write canonical skill references as backtick `$skill-name` spans outside code
examples. Use portable relative Markdown links in copied reference documents.
Run `mise run prototype:sync` in the Tropos checkout to build, deploy and smoke-test all harnesses.

**Naming pattern:** `<namespace>[-<subnamespace>]-<action>`
- `dispatch`, `scope`, `git worktree`

**Description format:** Third person, what + when.
- "Generate GitHub issue drafts from spec directories. Use when converting specs to GitHub issues."

### Step 4: Create Structure

```bash
mkdir -p skills/{skill-name}
```

**Standard structure:**

```
skills/{skill-name}/
├── SKILL.md              # Main instructions (<500 lines)
├── templates/            # Document templates (.md)
├── scripts/              # Executable code (.sh, .py)
└── reference/           # Extended documentation
```

### Step 5: Implement & Test

**Write SKILL.md:**
- Keep under 200 lines (500 max)
- Progressive disclosure: SKILL.md → reference/
- Include concrete examples, no emojis
- Apply the [single-source-of-truth contract](../../instructions/AGENTS.md#single-source-of-truth)

**Test with real tasks:**
1. Does the description trigger correctly?
2. Can each harness find bundled resources?
3. Does the workflow complete successfully?

---

## Degrees of Freedom

Match specificity to task fragility:

**High freedom** - Multiple approaches valid, context-dependent:
```markdown
## Code review
1. Analyze structure and organization
2. Check for bugs and edge cases
3. Suggest improvements
```

**Low freedom** - Operations fragile, consistency critical:
```markdown
## Database migration
Run exactly: `python scripts/migrate.py --verify --backup`
Do not modify flags.
```

---

## Skill Types

| Type | Characteristics | Examples |
|------|-----------------|----------|
| **Operational** | Multi-step workflow, state changes, document templates | `scope` |
| **Generation** | Transform input → structured output, format templates | `docs-implement` |
| **Guidance** | Imperative instructions, code patterns | `implement`, `loqui` |

---

## Success Criteria

- Name follows `<namespace>[-<subnamespace>]-<action>`
- Description is third person with what + when
- SKILL.md under 200 lines (500 max)
- Workflow steps numbered and actionable
- Templates extracted to separate files
- References point to authoritative sources
- No emojis (text markers only)

---

## Reference

- [best-practices.md](best-practices.md) - Core principles, patterns, checklist
- [reference.md](reference.md) - Project patterns, frontmatter specs, anti-patterns
