---
allowed-tools: Bash(git status *), Bash(git log *), Bash(git branch *), Bash(git rev-parse *), Bash(git rev-list *), Bash(git merge-base *), Bash(git for-each-ref *), Bash(git reflog *), Bash(git config *), Bash(git fetch *), Bash(git stash *), Bash(test *)
---

## Runtime Git Context

Run these commands before selecting the strategy; the working tree must be clean before rebasing.

Branch and HEAD:
```bash
git rev-parse --abbrev-ref HEAD 2>/dev/null && git rev-parse --short HEAD 2>/dev/null
```

Default base (origin HEAD → upstream → main/master):
```bash
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || (git show-ref --verify --quiet refs/heads/main && echo main) || (git show-ref --verify --quiet refs/heads/master && echo master)
```

Upstream:
```bash
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo "no upstream"
```

Working tree:
```bash
git status --porcelain 2>/dev/null | head -20 || echo "clean"
```

In-progress operations:
```bash
for d in rebase-merge rebase-apply MERGE_HEAD CHERRY_PICK_HEAD BISECT_LOG; do test -e "$(git rev-parse --git-path $d 2>/dev/null)" 2>/dev/null && echo "IN_PROGRESS: $d"; done; true
```

Stashes:
```bash
git stash list 2>/dev/null | head -5 || echo "none"
```

Ahead/behind upstream:
```bash
git rev-list --left-right --count 'HEAD...@{upstream}' 2>/dev/null | awk '{printf "ahead=%s behind=%s\n", $1, $2}' || echo "n/a"
```

Ahead/behind base:
```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git rev-list --left-right --count "HEAD...$base" 2>/dev/null | awk -v b="$base" '{printf "vs %s: ahead=%s behind=%s\n", b, $1, $2}' || echo "n/a"
```

Merge-base:
```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git merge-base HEAD "$base" 2>/dev/null | xargs -I{} git --no-pager log -1 --oneline {} 2>/dev/null || echo "no merge-base"
```

Fork-point (≠ merge-base ⇒ upstream rewrote history):
```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git merge-base --fork-point "$base" HEAD 2>/dev/null | xargs -I{} git --no-pager log -1 --oneline {} 2>/dev/null || echo "no fork-point (upstream may have been rewritten)"
```

Branch commits:
```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git --no-pager log --oneline "$(git merge-base HEAD "$base" 2>/dev/null)..HEAD" 2>/dev/null | head -30
```

Autosquash candidates:
```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git --no-pager log --oneline "$(git merge-base HEAD "$base" 2>/dev/null)..HEAD" 2>/dev/null | grep -E '^[a-f0-9]+ (fixup|squash)!' || echo "none"
```

Base reflog (force-pushes, resets):
```bash
base=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main); git reflog show "$base" -n 8 2>/dev/null || echo "no reflog for $base"
```

Downstream branches (descend from HEAD):
```bash
git for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null | while read b; do [ "$b" = "$(git rev-parse --abbrev-ref HEAD)" ] && continue; git merge-base --is-ancestor HEAD "$b" 2>/dev/null && echo "$b"; done | head -10 || echo "none"
```

Rebase config:
```bash
git config --get-all rebase.autosquash; git config --get-all rebase.updateRefs; git config --get-all rerere.enabled; true
```

# Rebase Strategy Operation

## Workflow

1. Collect the Runtime Git Context signals.
2. State intent in one line: "`<branch>` will become a descendant of `<new-base>`; commits `<old-base>..<branch>` get replayed." `git rebase --onto X Y` moves the current branch onto `X`. When the user said the fix belongs on branch X, commit on X or rebase X's downstream onto X; never rebase X onto its descendant. Confirm direction with the user when the target is an integration/aggregator branch, the source is a published PR head, or other branches descend from either.
3. Match the decision table top-down; first match wins.
4. Present the Output Format with real refs, prerequisites, risks and reversal.
5. Ask before executing anything that rewrites history; the user runs it or confirms.
6. Before any further action, run `git log --oneline --graph <expected-base>..HEAD` and check the parent chain matches step 2, no unexpected commits were replayed, and none are missing. On divergence stop: no edit, commit, force-push or merge on top (a squash-merge into an integration branch carries the error to main). Reverse with `git reset --keep ORIG_HEAD` and reconsider direction.

## Decision Table

| Priority | Signal | Diagnosis | Action |
|---|---|---|---|
| 1 | `IN_PROGRESS: rebase-merge` or `rebase-apply` | Rebase running | Resolve conflicts and `git rebase --continue`, `git rebase --skip` to drop the current commit, or `git rebase --abort`. Do not start a new rebase. |
| 2 | `IN_PROGRESS: MERGE_HEAD` / `CHERRY_PICK_HEAD` / `BISECT_LOG` | Other operation in flight | Finish (`--continue`) or abort it first. |
| 3 | Working tree non-empty | Dirty tree | `git stash push -m "pre-rebase $(date +%FT%T)" --include-untracked`, re-run this operation, `git stash pop` after. Never use `--ignore` flags. |
| 4 | `ahead=0 behind=0` vs base | Up to date | No rebase. |
| 5 | `ahead=0 behind>0` | Behind only | No rebase; `git pull --ff-only` (or `git merge --ff-only <base>`). |
| 6 | `ahead>0 behind=0` | Base unmoved | No rebase; push. |
| 7 | "no fork-point" or fork-point ≠ merge-base, and base reflog shows recent forced moves | Upstream rewrote history; plain rebase replays obsolete commits | `git rebase --onto <base> <old-base> <branch>` with the old upstream tip (from `git reflog show <base>`, the entry before the rewrite) as `<old-base>`. |
| 8 | Autosquash candidates present | Pending fixups | `git rebase -i --autosquash <base>` (or `git config --global rebase.autosquash true` once, then `git rebase -i <base>`). |
| 9 | Downstream branches non-empty and base moved | Downstream branches depend on this one | Order bottom-up; after this branch lands, `git rebase --onto <base> <this-branch-old-tip> <downstream>` for each. See [reference/branching.md](../reference/branching.md). |
| 10 | `ahead>0 behind>0`, fork-point == merge-base | Standard divergence | `git rebase <base>` (or `git pull --rebase` if `<base>` is `@{upstream}`). |
| 11 | `no upstream` and user wants a specific base | No tracking branch | Ask for the target base, then rebase; optionally `git branch --set-upstream-to=<base>`. |

Push rewritten shared branches only with `--force-with-lease`.

## Output Format

```
Diagnosis: <one line>

Command:
  <single shell command, with real refs substituted>

Prereq (if any):
  <stash / fetch / abort command>

Reversal:
  git reset --keep ORIG_HEAD     # undoes the last rebase
  # or: git reflog and `git reset --keep <pre-rebase sha>`

Notes:
  <e.g. "downstream branches X, Y need re-rebasing after this">
```

## Helpful One-Shot Commands

```bash
# Save the upstream tip before pulling, for a later rebase --onto
git rev-parse @{upstream} > /tmp/old-upstream-$(git rev-parse --abbrev-ref HEAD)

# Commits unique to this branch
git log --oneline --no-merges $(git merge-base HEAD <base>)..HEAD

# Is a branch contained in another
git merge-base --is-ancestor <branch> <other> && echo "ancestor" || echo "diverged"
```

## Reference

- [../reference/branching.md](../reference/branching.md) — Cascading branches, `--onto` mechanics
- [../reference/history.md](../reference/history.md) — Fixup workflow, autosquash, range-diff
- [../reference/commands.md](../reference/commands.md) — `force-with-lease`, `range-diff`
