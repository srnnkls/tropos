# Modern Git Commands

## switch / restore (2.23)

`checkout` was overloaded — branch switching and file restoration in one command.

```bash
# Branch operations → switch
git switch main
git switch -c feat/auth           # Create and switch
git switch -c feat/auth origin/main  # Create from specific ref
git switch -                      # Previous branch
git switch --detach v1.0          # Detached HEAD

# File operations → restore
git restore file.txt              # Discard unstaged changes
git restore --staged file.txt     # Unstage (keep changes)
git restore -s HEAD~1 file.txt    # Restore from specific commit
git restore -s main -- src/       # Restore directory from branch
```

## force-with-lease (2.13)

Prevents overwriting commits pushed by others since your last fetch.

```bash
git push --force-with-lease       # Safe: fails if remote diverged
git push --force                  # Unsafe: overwrites unconditionally
```

Always use `--force-with-lease`. Alias it:

```bash
git config --global alias.fpush "push --force-with-lease"
```

## stash push (2.13)

Named stashes with pathspec support.

```bash
git stash push -m "wip: auth"                    # Named stash
git stash push -m "partial" -- src/auth.rs        # Specific files
git stash push -m "untracked" --include-untracked # Include untracked
git stash list                                    # List stashes
git stash pop                                     # Apply and remove
git stash apply stash@{2}                         # Apply without removing
```

## worktree (2.5+)

Multiple working trees sharing one repo. No stashing, no context switching.

```bash
git worktree add ../feat-auth -b feat/auth    # New worktree + branch
git worktree add ../hotfix main               # Worktree from existing branch
git worktree list                             # List all worktrees
git worktree remove ../feat-auth              # Clean up
```

Each worktree is an independent directory with its own index and working tree, sharing objects and refs.

## sparse-checkout (2.25)

Work with a subset of files in large repos.

```bash
git sparse-checkout init --cone
git sparse-checkout set src/ tests/     # Only these directories
git sparse-checkout add docs/           # Add more
git sparse-checkout list                # Show current set
git sparse-checkout disable             # Back to full checkout
```

## partial clone (2.19)

Clone without downloading all blobs upfront.

```bash
git clone --filter=blob:none <url>      # No blobs (fetch on demand)
git clone --filter=tree:0 <url>         # No blobs or trees
git clone --depth=1 <url>               # Shallow (last commit only)
```

## maintenance (2.29)

Background repository optimization.

```bash
git maintenance start       # Enable: gc, prefetch, commit-graph, loose-objects
git maintenance stop        # Disable
git maintenance run --task=gc              # Run specific task
git maintenance run --task=commit-graph    # Update commit-graph
```

Configures a cron/launchd schedule for automatic optimization.

## blame --ignore-rev (2.23)

Skip bulk formatting commits in blame output.

```bash
git blame --ignore-rev abc123f file.txt
git blame --ignore-revs-file .git-blame-ignore-revs file.txt
```

Create `.git-blame-ignore-revs` at repo root, one SHA per line:

```
# Prettier migration
abc123f
# Black formatting
def456a
```

Configure globally:

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

## diff --color-moved (2.17)

Distinguish moved code from changed code in diffs.

```bash
git diff --color-moved                  # Highlight moved blocks
git diff --color-moved=dimmed-zebra     # Best visual distinction
git config --global diff.colorMoved dimmed-zebra   # Set as default
```

## range-diff (2.19)

Compare two versions of a branch (before/after rebase or amendment).

```bash
git range-diff main..@{1} main..@        # Compare before/after rebase
git range-diff v1..v2 v1..v3             # Compare two update series
```

## log --remerge-diff (2.35)

Show what a merge commit actually resolved (not just "merge branch X").

```bash
git log --remerge-diff -1 <merge-commit>
git log --remerge-diff --merges
```

## rerere (reuse recorded resolution)

Remember conflict resolutions and auto-apply them next time.

```bash
git config rerere.enabled true          # Enable
git rerere status                       # Show recorded resolutions
git rerere diff                         # Show what rerere would apply
git rerere forget <file>                # Forget resolution for file
```

Useful when rebasing cascading branches — the same conflicts recur and rerere handles them automatically.
