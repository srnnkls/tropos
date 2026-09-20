---
name: dispatch
description: Intent router. Routes explicit workflow requests and leaves ordinary work in direct execution.
metadata:
  type: generic
henia:
  targets:
    claude:
      frontmatter:
        argument-hint: '[target]'
    codex:
      openai:
        interface:
          display_name: Dispatch
          short_description: Apply the canonical dispatch skill workflow
          default_prompt: Use $dispatch for the requested task.
---

<!-- Generated from skills/dispatch/SKILL.md by henia build; edit the canonical source. -->

# Intent Router

Workflow skills are explicit opt-ins. A file path or task description stays in direct current-agent execution.

## Routes

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Action |
|---|---|
| `continue` or `resume` | `Skill(continue, $ARGUMENTS)` |
| `implement ...` | `Skill(implement, $REST)` |
| `debug` or `trace` | `Skill(implement, debug $REST)` |
| `test` or `tdd` | `Skill(test, $REST)` |
| `verify` or `done` | `Skill(implement, verify $REST)` |
| Explicit scope path | `Skill(implement, $ARGUMENTS)` |
| File path or task description | Execute directly; do not invoke `implement` |
| No argument | Ask which explicit workflow to run |

A checkpoint or active scope is context, not permission to resume or implement. Require an explicit route.

## Menu

When no route is named, use AskUserQuestion:

```text
Header: Dispatch
Question: Which workflow should run?
multiSelect: false
Options:
- Implement: Strict delegated RED → GREEN → review
- Continue: Resume an interrupted implementation scope
- Test: Run explicit RED-GREEN-REFACTOR
- Verify: Verify completion from current evidence
```

With “Other” covering debug or direct execution.

> Protocol: [protocol.md](protocol.md)
