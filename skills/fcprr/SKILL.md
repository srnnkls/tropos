---
name: fcprr
description: Close PR review threads you've addressed — fix, commit, push, reply, resolve. Applies the fixes for every addressworthy comment, commits and pushes once, then replies to and resolves each thread referencing the commit. `--resolve-only` closes dismissed threads with a rationale reply and no fix. Use for "fcprr", "close a review thread I fixed", "resolve threads I've addressed", "reply and resolve a dismissed thread".
argument-hint: "--comment <id> [--comment <id>…] [--reply <text>] [-m <msg>] [--pr <n>] [--resolve-only] [paths…]"
allowed-tools: Bash(gh review *), Bash(gh pr *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
metadata:
  type: domain
---

# fcprr — fix + commit + push + reply + resolve

Close the loop on the review threads you've addressed: apply the fixes, commit them, push, then reply to each thread referencing the commit and resolve it.

The five steps are strictly ordered. Each gates the next:

1. **fix** — apply the change that addresses the comment; the reply text describes it.
2. **commit** — fails if pre-commit hooks (lint, typecheck, tests) are red → stop, surface the output, fix, retry.
3. **push** — the reply names the commit SHA, so the SHA must exist on the remote first.
4. **reply** — `gh review reply` posts to the thread.
5. **resolve** — `gh review resolve` marks the thread resolved.

A failure at any step stops the rest. Never reply "Done in `<sha>`" when the fix, commit, or push didn't land.

`reply` and `resolve` both take the comment node id (`PRRC_…`) from `gh review comments <pr> --ids` and map it to the thread internally — no manual id juggling.

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--comment <id>` | — (≥1 required) | Review comment node id to reply to and whose thread to resolve; repeat once per addressed thread. From `gh review comments <pr> --ids`. |
| `--reply <text>` | — | Reply note; the short SHA is prepended automatically (`Done in <sha> — <text>`). If omitted, compose one from the fix. |
| `-m, --message <text>` | derived | Commit message (conventional commit format). |
| `--pr <n>` | branch's PR | Override the PR (otherwise resolved from the current branch). |
| `--resolve-only` | off | Close a **dismissed** thread — skip fix, commit, and push (steps 2–4). Post `--reply` verbatim (no `Done in <sha>` prefix) and resolve. Ignores `-m` and `paths…`. |
| `[paths…]` | already-staged | Files to stage before committing. With none, commits whatever is already staged. |

---

## Workflow

### 1. Parse arguments and resolve the PR

- At least one `--comment <id>` is required (→ `COMMENT_IDS`). Without one there's no thread to reply to or resolve — stop and ask.
- Resolve the PR into `PR`: use `--pr <n>` if given, else the branch's PR. Stop if neither yields one.

```bash
PR="${pr_flag:-$(gh pr view --json number -q .number 2>/dev/null)}"
[ -z "$PR" ] && { echo "no PR for this branch — pass --pr <n>"; exit 1; }
```

### 2. Fix

Apply the fixes for **every addressworthy comment** — each one the `comments` route accepted (valid), not the invalid ones (misreads, already-addressed, convention-contradicting), which are dismissed rather than fixed. Whatever lands in the working tree here is what the commit and per-thread replies describe. If the fixes are already applied, skip to staging.

### 3. Stage and commit

Inspect what's staged, then commit. Confirm it's the addressworthy fixes and nothing unrelated.

```bash
git status --short          # confirm the staged set
git add <paths…>            # skip if already staged
git commit -m "<message>"
```

Message: conventional commit format (`<type>(<scope>): <description> (#<pr-or-issue>)`), imperative and lowercase, describing the fix.

**Hooks gate this step.** If the commit fails (hooks red), stop — report the failing output, fix, and retry. Do not proceed to push.

Capture the short SHA for the reply:

```bash
SHA=$(git rev-parse --short HEAD)
```

### 4. Push

```bash
git push                    # or: git push -u origin <branch> on first push
```

If the push fails (e.g. non-fast-forward), stop and resolve it before replying — the reply must reference a SHA that exists on the remote.

### 5. Reply

Lead with the SHA so the reviewer can trace the fix. Show the body and confirm before posting — this is outward-facing.

```bash
gh review reply "$PR" --comment "$COMMENT_ID" --body "Done in $SHA — <reply text>"
```

`gh review reply` errors if the comment id isn't a thread on this PR — re-check with `gh review comments "$PR" --ids`.

### 6. Resolve

```bash
gh review resolve "$PR" --comment "$COMMENT_ID"
```

Prints `✓ Resolved thread …` on success.

### 7. Report

State the outcome in one line: commit SHA + hook result, push target, the threads replied to and resolved. e.g. `1f8e3a2 pushed (hooks green) → replied + resolved 3 threads`.

**Every addressed thread rides the same commit:** the fix, commit, and push happen once for the batch. Repeat steps 5–6 per `--comment` id, reusing the same `$SHA`.

---

## Resolve-only — dismissed threads

`--resolve-only` closes a thread you're **dismissing**, not fixing (a misread, an already-addressed point, a convention-contradicting suggestion). It skips steps 2–4 — there's no fix to commit — and runs only reply + resolve, the `rr` of `(fcp)rr`:

```bash
gh review reply "$PR" --comment "$COMMENT_ID" --body "<rationale>"
gh review resolve "$PR" --comment "$COMMENT_ID"
```

The reply is the dismissal rationale, posted verbatim — no `Done in <sha>` prefix, since nothing was committed. Rationales differ per thread, so invoke once per dismissed thread with its own `--comment` and `--reply`.

---

## Error Handling

| Condition | Action |
|-----------|--------|
| `--comment` missing | Stop — nothing to reply to or resolve |
| `--resolve-only` with `-m`/`paths…` | Ignore them — resolve-only never commits |
| No PR for branch and no `--pr` | Stop — report `none` |
| Commit fails (hooks red) | Stop, surface hook output, fix, retry; do not push |
| Push rejected (non-fast-forward) | Stop, reconcile (pull/rebase), retry; do not reply yet |
| `reply`/`resolve` reports no thread for the comment | Wrong or already-resolved id — re-check with `gh review comments "$PR" --ids` |
| `gh` not authenticated | Report: run `gh auth login` |
