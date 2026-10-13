# Canonical Skill Reference

Edit only `skills/`; build into `.henia/build/`, deploy with Phora.

## Frontmatter Specification

- `name`: max 64 characters; lowercase letters, numbers, hyphens; no XML tags; no `anthropic` or `claude`.
- `description`: 1–1024 characters; no XML tags; third person ("Processes files").

Claude-native fields go in Claude's `henia.targets` block:

```yaml
context: fork              # run in a forked subagent context
agent: haiku               # haiku | sonnet | opus
user-invocable: false      # slash command menu; default true
allowed-tools:             # restrict tools, YAML list
  - Read
  - Bash
hooks:
  PreToolUse:              # before each tool
    - command: ./scripts/before-tool.sh
      timeout: 5000
  PostToolUse:             # after each tool
    - command: ./scripts/after-tool.sh
  Stop:                    # at completion
    - command: ./scripts/cleanup.sh
```

## Command Delegation Pattern

A command delegates to a skill in about 20 lines:

```markdown
---
description: Create planning documents for task
---

## User Input

```text
$ARGUMENTS
```

## Task

Use the `scope` skill to create planning documents.

Input: `$ARGUMENTS` (optional scope name)

Follow the scope skill workflow.
```

## Anti-Patterns

- Information the model already knows

List related skills in a `:::related` block and resource links in a `:::references` block.
