---
allowed-tools: Bash(git status *), Bash(git log *), Bash(git branch *), Bash(git rev-parse *), Bash(git rev-list *), Bash(git merge-base *), Bash(git for-each-ref *), Bash(git reflog *), Bash(git config *), Bash(git fetch *), Bash(git stash *), Bash(test *)
---

## Pre-loaded Git Context

Branch and HEAD:
!`git rev-parse --abbrev-ref HEAD 2>/dev/null && git rev-parse --short HEAD 2>/dev/null`

Default base branch (best guess: upstream HEAD → tracked → main/master):
!`git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || (git show-ref --verify --quiet refs/heads/main && echo main) || (git show-ref --verify --quiet refs/heads/master && echo master)`

Upstream tracking ref:
!`git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo "no upstream"`

Working tree status (must be clean before rebase):
!`git status --porcelain 2>/dev/null | head -20 || echo "clean"`

In-progress rebase / merge / cherry-pick / bisect:
!`for d in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD BISECT_LOG; do test -e "$(git rev-parse --git-path $d 2>/dev/null)" 2>/dev/null && echo "IN_PROGRESS: $d"; done; true`

Stash entries:
!`git stash list 2>/dev/null | head -5 || echo "none"`

Ahead/behind upstream (HEAD vs @{u}):
!`git rev-list --left-right --count 'HEAD...@{upstream}' 2>/dev/null | awk '{printf "ahead=%s behind=%s\n", $1, $2}' || echo "n/a"`

Ahead/behind default base (HEAD vs origin/main, falling back to main):
!`base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git rev-list --left-right --count "HEAD...$base" 2>/dev/null | awk -v b="$base" '{printf "vs %s: ahead=%s behind=%s\n", b, $1, $2}' || echo "n/a"`

Merge-base (common ancestor) with default base:
!`base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git merge-base HEAD "$base" 2>/dev/null | xargs -I{} git --no-pager log -1 --oneline {} 2>/dev/null || echo "no merge-base"`

Fork-point with default base (differs from merge-base ⇒ upstream rewrote history):
!`base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git merge-base --fork-point "$base" HEAD 2>/dev/null | xargs -I{} git --no-pager log -1 --oneline {} 2>/dev/null || echo "no fork-point (upstream may have been rewritten)"`

Commits on this branch since merge-base:
!`base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git --no-pager log --oneline "$(git merge-base HEAD "$base" 2>/dev/null)..HEAD" 2>/dev/null | head -30`

Autosquash candidates (fixup!/squash! commits in branch):
!`base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git --no-pager log --oneline "$(git merge-base HEAD "$base" 2>/dev/null)..HEAD" 2>/dev/null | grep -E '^[a-f0-9]+ (fixup|squash)!' || echo "none"`

Recent reflog of default base (force-pushes / resets):
!`base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git reflog show "$base" -n 8 2>/dev/null || echo "no reflog for $base"`

Branches that descend from current HEAD (potential downstream cascades):
!`git for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null | while read b; do [ "$b" = "$(git rev-parse --abbrev-ref HEAD)" ] && continue; git merge-base --is-ancestor HEAD "$b" 2>/dev/null && echo "$b"; done | head -10 || echo "none"`

Rebase configuration:
!`git config --get-all rebase.autosquash; git config --get-all rebase.updateRefs; git config --get-all rerere.enabled; true`

# Rebase Strategy Operation

Inspect current git state and recommend the right rebase command.

## Workflow

1. **Read pre-loaded context above.** It already collected the signals (HEAD, base, merge-base, fork-point, divergence, fixups, downstream, working tree).
2. **State intent in one line before matching:** "`<branch>` will become a descendant of `<new-base>`; commits `<old-base>..<branch>` get replayed." If the user's prior instruction was "the fix belongs on branch X," the branch under your cursor should usually be X (commit there) or X's *downstream* (rebase onto X) — not X being rebased onto its descendant. Confirm direction with the user when any of these hold: target is an integration/aggregator branch, source is a published PR head, or other branches descend from either.
3. **Match the dominant signal in the decision table below** (top-down — first match wins).
4. **Present the recommendation:**
   - One-line diagnosis (what state the branch is in)
   - The exact command to run (use real refs from context, not placeholders)
   - Any prerequisite (stash, fetch, abort)
   - Risks and reversal command
5. **Ask before executing** anything that rewrites history. The user runs it, or confirms.
6. **Verify topology after running, before any further action.** Run `git log --oneline --graph <expected-base>..HEAD` and check:
   - Parent chain matches the intent stated in step 2
   - No unexpected commits replayed (e.g., commits from the wrong side of the cascade)
   - No expected commits missing
   If the graph diverges from intent, stop. Do not commit, force-push, or merge on top — each of those bakes the misplacement deeper. Reverse with `git reset --hard ORIG_HEAD` and reconsider direction.

---

## Decision Table

| Priority | Signal in pre-loaded context | Diagnosis | Recommended action |
|---|---|---|---|
| 1 | `IN_PROGRESS: rebase-merge` or `rebase-apply` | A rebase is already running | Resolve conflicts then `git rebase --continue`, or `git rebase --skip` to drop the current commit, or `git rebase --abort` to bail out. Do NOT start a new rebase. |
| 2 | `IN_PROGRESS: MERGE_HEAD` / `CHERRY_PICK_HEAD` / `BISECT_LOG` | Different operation in flight | Finish (`--continue`) or abort that operation first. Don't rebase on top. |
| 3 | Working tree status non-empty | Dirty working tree — rebase would refuse or stomp changes | `git stash push -m "pre-rebase $(date +%FT%T)" --include-untracked`, then re-run this skill. Restore with `git stash pop` after. |
| 4 | `ahead=0 behind=0` vs base | Already up to date | No rebase needed. |
| 5 | `ahead=0 behind>0` vs base | Behind only — fast-forward case | `git pull --ff-only` (or `git merge --ff-only <base>`). No rebase needed. |
| 6 | `ahead>0 behind=0` vs base | Ahead only — base hasn't moved | No rebase needed. Just push. |
| 7 | Fork-point line says "no fork-point" or fork-point ≠ merge-base, AND base reflog shows recent forced moves | Upstream rewrote history (squash-merge / force-push). Naive rebase will replay obsolete commits. | `git rebase --onto <base> <old-base> <branch>` — use the *old upstream tip* as `<old-base>`. Find it via `git reflog show <base>` (the entry just before the rewrite) or save it preemptively next time. |
| 8 | Autosquash candidates list contains `fixup!` or `squash!` commits | Branch has pending fixups to fold | `git rebase -i --autosquash <base>` (or set `git config --global rebase.autosquash true` once and use `git rebase -i <base>`). |
| 9 | Downstream branches list non-empty AND base has moved | Cascading branches depend on this one — rebasing here will leave them stranded | Plan order before acting: rebase/merge bottom-up. After this branch lands on base, each downstream needs `git rebase --onto <base> <this-branch-old-tip> <downstream>`. See [reference/branching.md](../reference/branching.md). |
| 10 | `ahead>0 behind>0` vs base, fork-point == merge-base | Standard divergence, upstream linear | `git rebase <base>` (or `git pull --rebase` if `<base>` is `@{upstream}`). |
| 11 | `no upstream` AND user wants to rebase onto something specific | No tracking branch | Ask user for target base, then rebase. Optionally set tracking with `git branch --set-upstream-to=<base>`. |

---

## Output Format

After matching, return:

```
Diagnosis: <one line>

Command:
  <single shell command, with real refs substituted>

Prereq (if any):
  <stash / fetch / abort command>

Reversal:
  git reset --hard ORIG_HEAD     # undoes the last rebase
  # or: git reflog and `git reset --hard <pre-rebase sha>`

Notes:
  <e.g. "downstream branches X, Y need re-rebasing after this">
```

---

## Helpful One-Shot Commands

```bash
# Save the current upstream tip BEFORE pulling — needed for rebase --onto later
git rev-parse @{upstream} > /tmp/old-upstream-$(git rev-parse --abbrev-ref HEAD)

# Compare branch versions (after a rebase, see what really changed)
git range-diff <base>..@{1} <base>..@

# Inspect commits unique to this branch
git log --oneline --no-merges $(git merge-base HEAD <base>)..HEAD

# See whether a branch is fully contained in another
git merge-base --is-ancestor <branch> <other> && echo "ancestor" || echo "diverged"
```

---

## Anti-Patterns (refuse / warn)

- Rebasing a branch that is already pushed and shared without `--force-with-lease`.
- Plain `git rebase <base>` when fork-point and merge-base disagree — silently replays obsolete commits.
- Rebasing while a merge / cherry-pick / bisect is in progress.
- Rebasing with a dirty index (use stash, never `--ignore` flags).
- Using `git push --force` instead of `git push --force-with-lease`.
- Inverting `rebase --onto` direction. `git rebase --onto X Y` makes the *current* branch a descendant of `X`. If the user's intent is "work belongs on branch B," check the branch under your cursor before running — you usually want to commit on B, or rebase B's downstreams onto B, not the reverse.
- Continuing past a rebase without a topology check. Edits, commits, force-pushes, and especially squash-merges on top of a misrouted rebase are a one-way ratchet: each step embeds the mistake further, and a squash-merge into an integration branch will propagate it to main.

---

## Reference

- [../reference/branching.md](../reference/branching.md) — Cascading branches, `--onto` mechanics
- [../reference/history.md](../reference/history.md) — Fixup workflow, autosquash, range-diff
- [../reference/commands.md](../reference/commands.md) — `force-with-lease`, `rerere`, `range-diff`
