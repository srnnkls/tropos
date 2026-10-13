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

# Skill Creation

## Writing

Skills are read by agents only. Keep a line only if removing it changes what the agent does: instructions, contracts, schemas, pointers. No rationale, narration, unused examples, emphasis, or decoration. Tell the agent what to do; negate only a named pattern that has no single alternative. Verify cuts against a real task (Step 5).

## Workflow

### Step 1: Understand Use Cases

Collect tasks, triggers, and variations unless known.

### Step 2: Plan Contents

Pick a type and follow its shape:

- Operational (`scope`): validate input, gather context, change files/state, update indices, report.
- Generation (`doc`): validate source, parse input type, apply templates, generate, give usage.
- Guidance (`bash`): core principles, do/don't, code patterns, integration notes.

Give context-dependent tasks goals; fragile operations exact commands with flags fixed.

### Step 3: Choose Frontmatter

```yaml
name: skill-name          # Lowercase, hyphens, max 64 chars
description: |            # Max 1024 chars
  [What it does]. Use when [context].
```

Name: `<namespace>[-<subnamespace>]-<action>`. Description: third person, what + when. Full rules: [reference.md](reference.md).

- Top level holds only portable `name`, `description`, `metadata`, `license`, `compatibility`; harness metadata goes in `henia.targets.<profile>` (Codex UI: `.codex.openai.interface`), context inputs in `henia.variables`.
- `henia.auto_invoke: false` blocks model invocation and subagent preload: only for skills no agent preloads. Preloadable workflow skills state explicit-use policy in `description`.
- Slots (global contract, Project slots): owners declare `henia.slots` and a `## Slots` table, one `<skill>.<slot>` row with provider coverage each. Skills applying slots list them in a `Slot providers` context entry's `slots`; seams a slot replaces name it and link the owner's Slots section.
- Modes, per harness in `henia.toml` `[harness.<name>.skills]` (`default`, `static`, `dynamic`, `hybrid`): `static` installs all; `dynamic` nothing (served by `henia show`); `hybrid` a head rendered on load. User entry skills hybrid, the rest dynamic.
- Hybrid heads: wrap routes, hard rules, the context template, and `:slot[...]` directives in `:::head` (an existing `:::instruction` in `::::head`), max 150 marked lines; the rest loads via `henia show <skill>#<section>`. Without `:::head` the head is a thin launcher.
- Reference skills as `$<skill-name>` outside code; link skill files with relative links, which Henia renders as `henia show` commands where the file is not beside the text.

### Step 4: Create Structure

```
skills/{skill-name}/
├── SKILL.md              # Main instructions (<500 lines)
├── templates/            # Document structure patterns (.md)
├── scripts/              # Code otherwise rewritten each run (.sh, .py)
├── reference/            # Domain knowledge the agent needs
└── assets/               # Files used in output
```

### Step 5: Implement & Test

- SKILL.md under 200 lines (500 max), numbered steps; detail in `reference/`.
- Only examples the agent copies or pattern-matches; no emojis.
- Apply the [single-source-of-truth contract](../../instructions/AGENTS.md#single-source-of-truth).
- Run `mise run test-artifacts` in the Tropos checkout.
- On a real task confirm: description triggers, `henia show <skill>` lists resources, hybrid heads carry routes, links resolve, workflow completes on each target model.

:::references
- [best-practices.md](best-practices.md) — structure, workflows, evaluation, scripts
- [reference.md](reference.md) — frontmatter rules, Claude fields, anti-patterns
:::
