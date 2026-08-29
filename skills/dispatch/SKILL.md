---
name: dispatch
description: Intent router. Routes explicit workflow requests and leaves ordinary work in direct execution.
argument-hint: "[target]"
allowed-tools: Bash(find *), Bash(git status *), Bash(git branch *)
metadata:
  type: generic
---

## Pre-loaded Context

Active scopes:
!`find scopes -maxdepth 3 -name scope.md 2>/dev/null || true`

Checkpoints:
!`find scopes -name checkpoint.yaml -maxdepth 3 2>/dev/null || true`

Git status:
!`git status --short 2>/dev/null || true`

Current branch:
!`git branch --show-current 2>/dev/null || true`

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
