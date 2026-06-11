# Base-Drift Preflight

**Purpose:** Catch a drifted base *before* dispatching work — not at rebase time. The failure this prevents: a branch forks from `main`, `main` independently ships overlapping functionality, the branch reimplements it fresh, and the collision surfaces only as a multi-commit semantic rebase.

**MANDATORY** before dispatching any phase, on every route that runs on a pre-existing branch:
- `implement` — after checkout, before Phase A (covers existing-branch and worktree routes).
- `continue` — during branch verification, before resuming the pipeline.

Skip ONLY when the working branch was just created from its base in this same invocation (ahead/behind is zero by construction).

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
