# Base-Drift Preflight

**Purpose:** Catch a drifted base *before* dispatching work — not at rebase time. The failure this prevents: a branch forks from `main`, `main` independently ships overlapping functionality, the branch reimplements it fresh, and the collision surfaces only as a multi-commit semantic rebase.

**Drift is not a one-time event — it accumulates.** A check at dispatch start is necessary but NOT sufficient: on a long multi-batch run the *remote* trunk keeps advancing while you work, so a branch that was current at batch 1 can be 11 commits behind by the time its PR is opened. Always compare against a **freshly fetched** `origin/<trunk>`, and re-run at every checkpoint below — not just at the start.

**MANDATORY checkpoints — run this at ALL of them:**
- `implement` — after checkout, before Phase A (existing-branch and worktree routes).
- `implement` — **after each batch commit, before the next batch** (Step 7). The remote may have moved since the last batch; a small rebase now prevents a giant one later.
- `implement` / `continue` — **before final review and before opening/merging a PR** (Step 8/10). The branch MUST be rebased current on `origin/<trunk>` so the PR is born mergeable. This is the gate that stops a `CONFLICTING`/`DIRTY` PR.
- `continue` — during branch verification, before resuming the pipeline.
- `loop` — at the loop boundary (see `loop/operations/iterate.md`), since it runs unattended.

Skip the *start* check ONLY when the working branch was just created in this same invocation from a **freshly fetched remote ref** (`origin/<trunk>`) — only then is ahead/behind zero by construction. A branch created from a *local* ref (`main`, `master`, current HEAD) or by an outside tool (`workon`, `gh issue develop`, manual checkout) can be born already behind a stale local trunk — run the check. The per-batch and pre-PR checks are never skipped.

---

## Procedure

### 1. Determine the base

- `continue` → `checkpoint.base` if present, else the branch's merge-base parent, else `main`.
- `implement` → `--base` if passed, else the trunk the branch forked from (`main`/`master`).

### 2. Refresh the base ref

```bash
git fetch origin <base> --quiet
```

Use `origin/<base>` for the comparison when it exists, else the local `<base>`.

### 3. Measure divergence

```bash
# behind  ahead   (commits on base not on HEAD, then HEAD not on base)
git rev-list --left-right --count origin/<base>...HEAD
```

`behind == 0` → no drift. Proceed silently.

`behind > 0` → the base moved after the fork. Continue to overlap detection — do NOT dispatch yet.

### 4. Detect overlap (the part that matters)

A drifted base is only dangerous when it touched the same surface the upcoming work will. Compare the two change sets:

```bash
# Files the base changed since the fork
git diff --name-only HEAD...origin/<base>

# Files this branch already changed
git diff --name-only $(git merge-base origin/<base> HEAD) HEAD

# Files the *upcoming* work will touch:
#   - implement: target files from tasks.yaml / the task description
#   - continue:  files named in the next batch's tasks
```

Intersect the base's changed files with (this branch's changed files ∪ upcoming targets). Any intersection is a **semantic collision risk** — the base may have already implemented, moved, or renamed what the next phase is about to (re)build.

### 5. Gate

Present findings and STOP for a decision — never auto-proceed past a non-empty overlap:

```
Base drift detected: <base> is <behind> commit(s) ahead of this branch.

Overlapping surface:
  <file>  — base: <commit subject>   | upcoming: <task id/desc>
  ...

Risk: the base may already ship what the next phase would build (duplicate-work / rebase collision).
```

Then **AskUserQuestion**:

```
Header: Base drift
Question: <base> advanced with overlapping changes. How should I proceed?
multiSelect: false
Options:
- Rebase onto <base> first: integrate base changes, re-assess targets, then dispatch (recommended when overlap is non-empty)
- Proceed knowingly: dispatch anyway — I accept the collision will surface at merge/rebase
- Abort: stop so I can reconcile manually
```

For rebase, hand off to `/git rebase` (strategy analysis) rather than grinding commit-by-commit.

When `behind > 0` but the overlap is empty, report the drift in one line and proceed without blocking — divergence without shared surface is usually a clean rebase, not a collision.

---

## Pre-PR / pre-merge sync (the gate that stops conflicting PRs)

Before final review and before opening or merging a PR, the branch MUST be rebased current on the freshly fetched trunk — regardless of overlap. A PR opened while behind is born `CONFLICTING`/`DIRTY` and the conflict surfaces at merge time, which is exactly the failure this guard exists to prevent.

```bash
git fetch origin <trunk> --quiet
behind=$(git rev-list --count "HEAD..origin/<trunk>")
[ "$behind" -eq 0 ] && echo "current — proceed" || git rebase "origin/<trunk>"
```

- `behind == 0` → proceed to final review / PR.
- `behind > 0` → rebase now. Clean rebase → continue. Conflicts → resolve (hand to `/git rebase` for strategy), re-run the batch's tests GREEN, then continue. **Do not open or merge the PR until `behind == 0` post-rebase.**
- After any rebase that touched code, the final review (Step 8) runs on the integrated tree, not the pre-rebase one.

Never call `gh pr merge` on a branch reporting `mergeStateStatus: DIRTY` / `mergeable: CONFLICTING` — sync first.
