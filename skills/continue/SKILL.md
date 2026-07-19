---
name: continue
description: Resume interrupted work from context. Use when continuing after session break, context limit, or interruption.
argument-hint: "[scope-name]"
allowed-tools: Bash(find *), Bash(ls *), Bash(git *), Bash(peer *)
metadata:
  type: generic
---

## Pre-loaded Context

Active scopes:
!`find scopes -maxdepth 3 -name scope.md 2>/dev/null`

Checkpoints:
!`find scopes -name checkpoint.yaml -maxdepth 3 2>/dev/null`

Git status:
!`git status --short 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

# Continue Skill

Resume interrupted work from context.

---

## When to Use

- After hitting context limit during `/implement`
- Starting a new session to continue a scope
- Recovering from interruption mid-implementation

---

## Workflow

### Step 1: Find Checkpoint

1. Parse scope name from argument (e.g., `/continue auth-system`)
2. If no argument: find most recent checkpoint in `./scopes/*/*/checkpoint.yaml` (lifecycle dirs: `draft`, `active`, `done`)
3. If no checkpoint found: suggest `/implement` instead

```bash
# Find most recent checkpoint across all lifecycle states
ls -t ./scopes/*/*/checkpoint.yaml | head -1
```

### Step 2: Load Context

Read these files (in parallel):

```
./scopes/<state>/<scope>/checkpoint.yaml   # Session state
./scopes/<state>/<scope>/config.yaml       # Live implementation routing
./scopes/<state>/<scope>/scope.md          # Requirements
./scopes/<state>/<scope>/tasks.yaml        # Task definitions
./scopes/<state>/<scope>/dependencies.yaml # Batch structure (absent for Task scopes)
./scopes/<state>/<scope>/validation.yaml   # Pre-implementation review gate only
```

`<state>` ∈ `{draft, active, done}` — typically `active` for in-flight work.

If `dependencies.yaml` is absent (Task scopes), derive batches from `tasks.yaml`'s `depends_on` +
`files` — see `../implement/reference/parallel-detection.md`.

`config.yaml` is the only source of live tester, implementer, and reviewer routing. Never
recover routing from `checkpoint.yaml` or `validation.yaml.review_config`; those files record
session progress and pre-implementation review configuration, respectively.

If `config.yaml` is absent (including for a legacy scope), record that initialization is needed
but do not create it yet: the checkpoint branch has not been checked out. Do not recover routing
from another branch's config.

### Step 3: Verify Branch State

```bash
# Checkout scope branch
git checkout <checkpoint.branch>

# Verify at expected commit
git log -1 --format="%H" | head -c 8

# If mismatch, warn user and ask to proceed or abort
```

**Base-drift preflight (MANDATORY):** Follow `../implement/reference/base-drift-preflight.md` — it fetches `origin/<base>` fresh and measures divergence. If `behind > 0`, intersect the base's changed files with this branch's changes and the next batch's target files, then gate. **Do not resume the pipeline (Step 5) past a non-empty overlap without a user decision.**

After the checkpoint branch/worktree is active and the base-drift gate is clear, re-read
`config.yaml` from that working tree. If Step 2 marked it missing, run the same interactive setup
as `/implement config <scope>` and create it now. Validate explicit aliases with `peer list`.
Do not report progress or dispatch any phase until the live config exists and is valid.

Enforce same-host-family native routing before resuming. On Codex, reject `opus`/`sonnet` and every
peer alias whose live registry harness/family is Codex; use `codex-native`, while Claude-family
`*-cli` may run through peer. On Claude, reject `codex-native` and every peer alias whose registry
harness/family is Claude (including `opus-cli`/`sonnet-cli`); use native `opus`/`sonnet`, while
GPT/Codex-family aliases may run through peer. If an alias is host-incompatible, stop and ask the user to edit
`/implement config <scope>`; never silently convert or substitute. `codex-native` may appear in
`peer list` with `native=true` for discovery but is never peer-dispatched.

### Step 4: Report Progress

Present concise status:

```
## Resuming: <scope_name>

**Progress:** Batch <last_batch>/<total_batches> complete
**Completed:** <N> tasks
**Remaining:** <M> tasks

**Next batch:** #<next_batch.number>
- <task_id>: <task_name>
- <task_id>: <task_name>
[parallel: yes/no]

**Deferred issues:** <count>
[list if any]

**Incomplete mutating stages:** <count>
- Batch <N>, task <id>, phase <tester|implementer|fix>, prior agent <alias>, status <status>

**Pipeline cursor:** Batch <N>, phase <phase>, status <status>
[for review phases: each role/agent status and report directory]
```

If `checkpoint.incomplete_stages` is non-empty, report those entries as the immediate recovery
target instead of presenting `next_batch` as the next action.

### Step 5: Resume Four-Phase Pipeline

First inspect `checkpoint.incomplete_stages`:

1. For each entry, read its report directory and compare its pre/post git evidence with the live
   worktree. If a valid saved role report exists and the corresponding RED/GREEN/fix gate now
   passes, accept it and clear that entry.
2. Otherwise reload the live config and deliberately redispatch **that exact batch/task/phase**,
   supplying the saved evidence and existing partial edits as context. `/continue` itself is the
   deliberate redispatch authorization; do not restart Phase A, other tasks, or the whole batch.
3. Before redispatch, update the same entry with the currently configured agent, a new attempt
   report directory beneath the recorded stage directory, current baseline evidence, and
   `status: in_progress`. A mid-flight config edit therefore affects the new attempt without
   changing which stage is recovered.
4. On a valid report and gate success, save the report and remove the entry. On failure, retain it
   as `failed` with new git status/diff evidence and pause again.

Only when `incomplete_stages` is empty, resume `checkpoint.phase_cursor` exactly:

- `tester`, `implementer`, or `fix`: validate saved reports/gates, then dispatch only cursor tasks
  still lacking success; never restart earlier phases.
- `test_review` or `targeted_review`: read saved reports and redispatch only non-`ok` configured
  agent entries using their report/prompt directories. Do not rerun testers/implementers.
- `code_review` or `final_review`: preserve completed roles and `ok` agent reports; redispatch only
  pending/failed agents in the current role, then continue with the next pending role.
- `complete`: report completion without dispatch.

Before and after every recovery dispatch/gate, persist the cursor status/report directories per
`implement/reference/checkpoint-format.md`. If a legacy checkpoint lacks a cursor, reconstruct it
from saved reports, `review.yaml`, task state, and checkpoint progress; if more than one phase is
plausible, ask rather than defaulting to Phase A.

**CRITICAL:** Follow all `implement` execute operation rules:
- Immediately before **every** Phase A, A.5, B, and C dispatch, re-read and validate the
  scope's `config.yaml`; a mid-flight edit applies to the next dispatch, not work already running
- Route `codex-native` through Codex native delegation with inherited session model/reasoning,
  explicit native aliases through the matching Task agent, and configured external aliases
  through generic `peer --agent <role> --peers ...`
- For every review gate, require one success from each execution class actually configured; do not
  require peer success for an all-native route or native success for an all-external route
- If `config.yaml` is removed between phases, stop and recreate it through the interactive
  setup; never fall back to checkpoint or validation routing
- Write an `incomplete_stages` entry immediately before each mutating dispatch and clear it only
  after a valid report passes its stage gate, per `implement/reference/checkpoint-format.md`
- Advance `phase_cursor` around every phase/gate and each Phase C/final role; read-only failures
  remain on that cursor for exact redispatch
- Dispatch parallel subagents in single message
- Never skip reviewer phase
- Fix Critical/High issues before proceeding

### Step 6: Update Checkpoint

After batch completes and `incomplete_stages` is empty:

1. Update tasks.yaml statuses
2. Write new checkpoint.yaml
3. Commit with batch info
4. Continue to next batch or report completion

---

## Quick Resume Template

**For Tester:**
```
Task: <task_id> - <task_name>
From: <scope_name> (batch <N>)
Requirements: [from tasks.yaml]
Test hints: [from tasks.yaml]

Invoke `test` skill. Write failing tests.
Report tester_report YAML.
```

**For Implementer:**
```
Task: <task_id> - <task_name>
From: <scope_name> (batch <N>)
Tester report: [paste tester_report]

Invoke `implement` skill. Make tests pass.
Report implementer_report YAML.
```

**For Reviewer:**
```
Batch <N> review for <scope_name>
Tasks: <task_ids>
Implementer reports: [paste all]
Scope requirements: [from tasks.yaml]

Invoke `code` review. Evaluate gates.
Report reviewer_report YAML.
```

---

## Handling Edge Cases

### Checkpoint not found
```
No checkpoint found for <scope>.
Run /implement <scope> to start fresh.
```

### Branch mismatch
```
Warning: Current branch differs from checkpoint.
Expected: feat/<scope> at <sha>
Actual: <current_branch> at <current_sha>

Options:
1. Checkout checkpoint branch and continue
2. Abort and investigate
```

### Checkpoint stale (tasks.yaml modified)
```
Warning: tasks.yaml modified since checkpoint.
Checkpoint: <timestamp>
tasks.yaml: <modified_time>

Regenerating next batch from current state...
```

### Live config changed

If `config.yaml` changes while agents are running, let those agents finish with the routing they
started with. Reload the file before the next dispatch and record the agents actually used in the
stage report. Do not copy the new routing into `checkpoint.yaml`.

### Incomplete mutating stage

Do not infer that `next_batch` means Phase A should restart. The `incomplete_stages` list has
priority and identifies the only tasks/phases eligible for recovery. Preserve partial edits and
use its evidence to distinguish an interrupted successful report from work that needs deliberate
redispatch.

### Incomplete read-only gate

When `incomplete_stages` is empty but the cursor names a review gate, do not infer a batch start.
Use its per-agent/per-role statuses and report directories, accept valid saved reports, and rerun
only missing/failed entries. Advance the cursor only after that exact gate passes.

### All tasks complete
```
All tasks complete for <scope>.
Reloading config.yaml reviewer aliases + effort for final review.
```

Run the implementation final-review procedure directly with those aliases and effort, writing
external reports beneath `.peer/<scope>/<epoch>/final-review/`. Do not hand off to standalone
`/review --final`, read `validation.yaml.review_config`, or prompt for reviewer selection.

---

## Integration

**Command:** `/continue [scope-name]`

**Related skills:**
- `implement` (execute operation) - Initial execution (writes checkpoints)
- `scope update` - Sync task status via /scope update
- `scope done` - Mark scope as done

---

## Example Session

```
User: /continue

Claude: Found checkpoint for auth-system

## Resuming: auth-system

**Progress:** Batch 2/4 complete
**Completed:** 4 tasks (T001-T004)
**Remaining:** 3 tasks

**Next batch:** #3
- T005: Add session management
- T006: Add token refresh
[parallel: yes]

**Deferred issues:** 1
- [M1] Variable naming in auth.py:45 (batch 2)

Batch 3 complete. 1 batch remaining.
```
