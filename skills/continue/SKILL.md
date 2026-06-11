---
name: continue
description: Resume interrupted work from context. Use when continuing after session break, context limit, or interruption.
argument-hint: "[scope-name]"
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

Base drift (behind-count + overlapping files vs trunk):
!`b=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@.*/@@'); b=${b:-main}; git fetch origin "$b" --quiet 2>/dev/null; mb=$(git merge-base "origin/$b" HEAD 2>/dev/null); behind=$(git rev-list --count "HEAD..origin/$b" 2>/dev/null); echo "base=$b behind=${behind:-?}"; if [ "${behind:-0}" -gt 0 ]; then echo "-- base changed since fork --"; git diff --name-only "HEAD...origin/$b" 2>/dev/null; echo "-- this branch changed --"; git diff --name-only "$mb" HEAD 2>/dev/null; fi`

# Continue Skill

Resume interrupted work from context. Picks up where `implement` (execute operation) left off.

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
./scopes/<state>/<scope>/scope.md          # Requirements
./scopes/<state>/<scope>/tasks.yaml        # Task definitions
./scopes/<state>/<scope>/dependencies.yaml # Batch structure
./scopes/<state>/<scope>/validation.yaml   # Review config
```

`<state>` ∈ `{draft, active, done}` — typically `active` for in-flight work.

### Step 3: Verify Branch State

```bash
# Checkout scope branch
git checkout <checkpoint.branch>

# Verify at expected commit
git log -1 --format="%H" | head -c 8
# Should match checkpoint.last_commit

# If mismatch, warn user and ask to proceed or abort
```

**Base-drift preflight (MANDATORY):** Read the `Base drift` block in Pre-loaded Context. If `behind > 0`, follow `../implement/reference/base-drift-preflight.md`: intersect the base's changed files with this branch's changes and the next batch's target files, then gate. **Do not resume the pipeline (Step 5) past a non-empty overlap without a user decision** — the base may already ship what the next batch would build.

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

Continuing with three-phase pipeline...
```

### Step 5: Resume Three-Phase Pipeline

Execute the next batch using the same pipeline as `implement` (execute operation):

```
Phase A: TESTERS
├── Dispatch tester(s) for next_batch.tasks
└── Wait for completion

Phase B: IMPLEMENTERS
├── Dispatch implementer(s) with tester reports
└── Wait for completion

Phase C: REVIEWERS
├── Dispatch 1 Claude + N OpenCode reviewers (from review_config)
└── Wait for completion + synthesize
```

**CRITICAL:** Follow all `implement` execute operation rules:
- Always use `subagent_type: "general"` for subagents
- Dispatch parallel subagents in single message
- Never skip reviewer phase
- Fix Critical/High issues before proceeding

### Step 6: Update Checkpoint

After batch completes:

1. Update tasks.yaml statuses
2. Write new checkpoint.yaml
3. Commit with batch info
4. Continue to next batch or report completion

---

## Quick Resume Template

When resuming, use this condensed context for subagents:

**For Tester:**
```
Task: <task_id> - <task_name>
From: <scope_name> (batch <N>)
Requirements: [from tasks.yaml]
Test hints: [from tasks.yaml]

Invoke `test` skill. Write failing tests (RED).
Report tester_report YAML.
```

**For Implementer:**
```
Task: <task_id> - <task_name>
From: <scope_name> (batch <N>)
Tester report: [paste tester_report]

Invoke `implement` skill. Make tests pass (GREEN).
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

**Checkpoint not found:**
```
No checkpoint found for <scope>.
Run /implement <scope> to start fresh.
```

**Branch mismatch:**
```
Warning: Current branch differs from checkpoint.
Expected: feat/<scope> at <sha>
Actual: <current_branch> at <current_sha>

Options:
1. Checkout checkpoint branch and continue
2. Abort and investigate
```

**Checkpoint stale (tasks.yaml modified):**
```
Warning: tasks.yaml modified since checkpoint.
Checkpoint: <timestamp>
tasks.yaml: <modified_time>

Regenerating next batch from current state...
```

**All tasks complete:**
```
All tasks complete for <scope>.
Run final review? [Y/n]
```

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

Continuing with three-phase pipeline...

[Dispatches 2 testers in parallel]
[Dispatches 2 implementers in parallel]
[Dispatches 1 Claude + 2 OpenCode reviewers in parallel]
[Synthesizes review, no critical issues]
[Writes checkpoint, commits batch 3]

Batch 3 complete. 1 batch remaining.
Continue in this session or /continue later.
```
