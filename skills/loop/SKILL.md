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
!`git status --short 2>/dev/null || true`

Current branch:
!`git branch --show-current 2>/dev/null || true`

Recent commits:
!`git log --oneline -5 2>/dev/null || true`

# Autonomous Implementation Loop

Focus: $ARGUMENTS

**INVARIANT: The orchestrator NEVER writes code or tests.** All implementation MUST be delegated to fresh subagents via the `implement` skill.

---

## Protocol

1. Enumerate — Read scopes relevant to `$ARGUMENTS`, build parallel batches from the batch
   signal (`dependencies.yaml` `batches[*]` if present, else derived from `tasks.yaml`'s
   `depends_on` + `files` — see `../implement/reference/parallel-detection.md`), and create one
   TodoWrite entry per task annotated with its batch number
1a. Review gate — For each enumerated scope, verify `validation.yaml.review_gate.status: passed`.
   If absent or `failed`, the scope has not cleared its mandatory review gate: output
   `LOOP_BLOCKED: <scope> not reviewed — run /scope review` and stop. Do not iterate an
   unreviewed scope (same precondition as `implement/operations/execute.md` Step 2).
1b. Live routing — Read each scope's `config.yaml`. It is the only source of tester,
   implementer, and reviewer routing; never use `checkpoint.yaml` or
   `validation.yaml.review_config` for execution routing. If it is absent, mark that scope as
   needing initialization. Do not create or update config during enumeration because the current
   branch may be unrelated; initialization happens only after the selected scope branch/worktree
   is active.
   Enforce same-host-family native routing from registry metadata. Codex rejects native
   `opus`/`sonnet` and all peer Codex-family aliases in favor of `codex-native`, while Claude-family
   `*-cli` may use peer. Claude rejects `codex-native` and all peer Claude-family aliases in favor
   of native `opus`/`sonnet`, while GPT/Codex-family aliases may use peer. Stop for config editing,
   never silent conversion.
1c. Recovery priority — Read each scope's `checkpoint.yaml` before selecting a new batch. A
   non-empty `incomplete_stages` list has first priority; otherwise an existing `phase_cursor`
   identifies the exact mutating or read-only phase/role to resume. Mark that recovery work ahead
   of every pending batch. Never infer/restart Phase A from task status alone.
2. Iterate — `operations/iterate.md` (one batch per iteration)
3. Complete — When all todos are done, output summary and stop

---

## Related

- `implement` — TDD pipeline delegated per task
- `scope` — Full scope lifecycle with checkpoint management
- `continue` — Resume interrupted loop from checkpoint

---
