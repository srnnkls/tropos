# Commit and History Management

## Commit Hygiene

One logical change per commit. The commit message explains why, the diff explains what.

```bash
git add -p                        # Stage hunks interactively
git commit -m "feat: add auth"    # Conventional commit format
```

### Conventional Commits

```
<type>(<scope>): <description>

feat:     New functionality
fix:      Bug fix
refactor: Restructuring without behavior change
chore:    Maintenance, deps, config
docs:     Documentation
test:     Test additions/changes
perf:     Performance improvement
```

## Fixup Workflow

Fix past commits without manual interactive rebase.

```bash
# 1. Make the fix
vim src/auth.rs

# 2. Stage and mark as fixup for a specific commit
git add src/auth.rs
git commit --fixup <sha>          # Creates "fixup! <original message>"

# 3. Autosquash folds fixups into their targets
git rebase -i --autosquash main
```

Auto-enable autosquash globally:

```bash
git config --global rebase.autosquash true
```

Then `git rebase -i main` automatically reorders fixup commits.

### --fixup variants

```bash
git commit --fixup <sha>          # Silently fold into target
git commit --squash <sha>         # Fold and open editor to combine messages
git commit --fixup=amend:<sha>    # Replace target's message entirely
```

## git absorb (third-party)

Automatically distributes staged changes to the correct past commits.

```bash
cargo install git-absorb          # Install
# or: brew install git-absorb

git add -p                        # Stage changes
git absorb                        # Auto-create fixup commits
git rebase -i --autosquash main   # Fold them in
```

## Inspecting History

```bash
# Compact log
git log --oneline --graph -20

# What changed between branches
git log --oneline main..HEAD
git diff main...HEAD              # Three dots = merge base diff

# Compare branch versions (before/after rebase)
git range-diff main..@{1} main..@

# Search commit messages
git log --grep="auth" --oneline

# Search code changes
git log -S "function_name"        # Commits that add/remove this string
git log -G "regex_pattern"        # Commits matching regex in diff

# Who last touched each line
git blame -w file.txt             # Ignore whitespace changes
git blame --ignore-rev abc123f    # Skip formatting commits
```

## Squash Merge

Collapse a feature branch into a single commit on main.

```bash
git switch main
git merge --squash feat/auth
git commit                        # Single commit with all changes
```

### When to squash vs. regular merge

| Strategy | Use when |
|----------|----------|
| Squash merge | Feature branches, PRs — clean main history |
| Regular merge | Long-running branches where individual commits matter |
| Rebase + fast-forward | You want linear history with individual commits preserved |

## Interactive Rebase

Clean up before pushing.

```bash
git rebase -i main                # Rebase onto main
git rebase -i HEAD~5              # Last 5 commits
```

Actions: `pick`, `reword`, `edit`, `squash`, `fixup`, `drop`, `reorder`

### Magit

- `r i` — interactive rebase
- `r o` — rebase onto (for cascading branches)
- `r e` — rebase interactively from a specific commit

## Undo Patterns

```bash
# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# Undo last commit (keep changes unstaged)
git reset HEAD~1

# Undo a public commit (creates new reverse commit)
git revert <sha>

# Recover deleted branch or lost commit
git reflog                        # Find the SHA
git switch -c recovered <sha>     # Recreate
```

Reflog entries expire after 90 days (default).
