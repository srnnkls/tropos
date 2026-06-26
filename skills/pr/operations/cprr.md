---
allowed-tools: Bash(gh review *), Bash(gh pr *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
---

# cprr — commit + push + reply + resolve

Close the loop on **one** review thread you've just fixed locally: commit the fix, push it, reply to the thread referencing the commit, and resolve the thread.

The four steps are strictly ordered. Each gates the next:

1. **commit** — fails if pre-commit hooks (lint, typecheck, tests) are red → stop, surface the output, fix, retry.
2. **push** — the reply names the commit SHA, so the SHA must exist on the remote first.
3. **reply** — `gh review reply` posts to the thread.
4. **resolve** — `gh review resolve` marks the thread resolved.

A failure at any step stops the rest. Never reply "Done in `<sha>`" when the commit or push didn't land.

`reply` and `resolve` both take the comment node id (`PRRC_…`) from `gh review comments <pr> --ids` and map it to the thread internally — no manual id juggling.

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--comment <id>` | — (required) | Review comment node id to reply to and whose thread to resolve. From `gh review comments <pr> --ids`. |
| `--reply <text>` | — | Reply note; the short SHA is prepended automatically (`Done in <sha> — <text>`). If omitted, compose one from the fix. |
| `-m, --message <text>` | derived | Commit message (conventional commit format). |
| `--pr <n>` | branch's PR | Override the PR (otherwise resolved from the current branch). |
| `[paths…]` | already-staged | Files to stage before committing. With none, commits whatever is already staged. |

---

## Workflow

### 1. Parse arguments and resolve the PR

- `--comment <id>` is required (→ `COMMENT_ID`). Without it there's no thread to reply to or resolve — stop and ask.
- Resolve the PR into `PR`: use `--pr <n>` if given, else the branch's PR. Stop if neither yields one.

```bash
PR="${pr_flag:-$(gh pr view --json number -q .number 2>/dev/null)}"
[ -z "$PR" ] && { echo "no PR for this branch — pass --pr <n>"; exit 1; }
```

### 2. Stage and commit

Inspect what's staged, then commit. Confirm it's only the fix for this thread, not unrelated work.

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

### 3. Push

```bash
git push                    # or: git push -u origin <branch> on first push
```

If the push fails (e.g. non-fast-forward), stop and resolve it before replying — the reply must reference a SHA that exists on the remote.

### 4. Reply

Lead with the SHA so the reviewer can trace the fix. Show the body and confirm before posting — this is outward-facing.

```bash
gh review reply "$PR" --comment "$COMMENT_ID" --body "Done in $SHA — <reply text>"
```

`gh review reply` errors if the comment id isn't a thread on this PR — re-check with `gh review comments "$PR" --ids`.

### 5. Resolve

```bash
gh review resolve "$PR" --comment "$COMMENT_ID"
```

Prints `✓ Resolved thread …` on success.

### 6. Report

State the outcome in one line: commit SHA + hook result, push target, the thread replied to and resolved. e.g. `1f8e3a2 pushed (hooks green) → replied + resolved thread on src/foo.ts:42`.

**Sibling threads fixed by the same commit:** the commit and push happen once. Repeat steps 4–5 per additional `--comment` id, reusing the same `$SHA`.

---

## Error Handling

| Condition | Action |
|-----------|--------|
| `--comment` missing | Stop — nothing to reply to or resolve |
| No PR for branch and no `--pr` | Stop — report `none` |
| Commit fails (hooks red) | Stop, surface hook output, fix, retry; do not push |
| Push rejected (non-fast-forward) | Stop, reconcile (pull/rebase), retry; do not reply yet |
| `reply`/`resolve` reports no thread for the comment | Wrong or already-resolved id — re-check with `gh review comments "$PR" --ids` |
| `gh` not authenticated | Report: run `gh auth login` |
