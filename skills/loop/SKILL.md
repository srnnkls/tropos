---
name: loop
description: Autonomous implementation loop over a focus topic. Reads active scopes, builds parallel task batches, then iterates the TDD pipeline one batch per iteration (parallel testers → test review gate → parallel implementers → review) until all tasks are complete. Use when autonomously implementing all pending work for a scope or topic without manual step-by-step oversight.
argument-hint: "<focus topic>"
allowed-tools: Bash(find *), Bash(git *), Bash(peer *)
context: fork
hooks:
  Stop:
    - command: |
        echo "$HOOK_INPUT" | jq -e '.stop_hook_active' 2>/dev/null | grep -q true && exit 0
        hk check --all --fix 2>&1 || exit 2
---

## Pre-loaded Context

Pending tasks:
!`find scopes -maxdepth 3 -name "tasks.yaml" -type f 2>/dev/null | xargs -I{} sh -c 'echo "=== {} ===" && grep -A1 "status: pending" {} 2>/dev/null'`

Active todos:
!`cat .claude/todos.json 2>/dev/null | jq -r '.[] | "[" + .status + "] " + .content' 2>/dev/null`

Git status:
!`git status --short 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

Recent commits:
!`git log --oneline -5 2>/dev/null`

# Autonomous Implementation Loop

Focus: $ARGUMENTS

**INVARIANT: The orchestrator NEVER writes code or tests.** All implementation MUST be delegated to fresh subagents via the `implement` skill.

---

## Protocol

1. **Enumerate** — Read scopes relevant to `$ARGUMENTS`, build parallel batches from the batch
   signal (`dependencies.yaml` `batches[*]` if present, else derived from `tasks.yaml`'s
   `depends_on` + `files` — see `../implement/reference/parallel-detection.md`), and create one
   TodoWrite entry per task annotated with its batch number
2. **Iterate** — Read and follow `operations/iterate.md` (one batch per iteration)
3. **Complete** — When all todos are done, output summary and stop

---

## Related

- `implement` — TDD pipeline delegated per task
- `scope` — Full scope lifecycle with checkpoint management
- `continue` — Resume interrupted loop from checkpoint

---
