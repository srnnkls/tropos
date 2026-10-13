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

::::head

# Intent Router

:::routes{.ordered .protocol}
| Pattern | Action |
|---|---|
| `continue` or `resume` | Invoke `$continue` with `$ARGUMENTS` |
| `implement ...` | Invoke `$implement` with `$REST` |
| `debug` or `trace` | Invoke `$implement` with `debug $REST` |
| `test` or `tdd` | Invoke `$test` with `$REST` |
| `verify` or `done` | Invoke `$implement` with `verify $REST` |
| `issue ...` | Invoke `$issue` with `$REST` |
| `pr ...` | Invoke `$pr` with `$REST` |
| Explicit scope path | Invoke `$implement` with `$ARGUMENTS` |
| File path or task description | Execute directly; do not invoke `implement` |
| No argument | Ask which explicit workflow to run |

A checkpoint or active scope is context, not permission to resume or implement; require an explicit route.
:::

## Menu

When no route is named, use AskUserQuestion:

:::menu{header="Dispatch" question="Which workflow should run?"}
- Implement: Strict delegated RED → GREEN → review
- Continue: Resume an interrupted implementation scope
- Test: Run explicit RED-GREEN-REFACTOR
- Verify: Verify completion from current evidence
:::

“Other” covers debug and direct execution.

::::
