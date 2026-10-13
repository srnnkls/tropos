# Commit and History Management

## Commit Hygiene

The commit message explains why; the diff explains what. To split a dirty tree into separate commits, see [commands.md](commands.md#hunk-level-staging).

### Commit Format

The `git.commits` providers set the message format; the default is [Commits](../SKILL.md#commits).

## Fixup Workflow

```bash
git add src/auth.rs
git commit --fixup <sha>          # "fixup! <original message>": fold silently
git commit --squash <sha>         # fold and combine messages in the editor
git commit --fixup=amend:<sha>    # replace the target's message
git rebase -i --autosquash main   # fold fixups into their targets
git config --global rebase.autosquash true   # then plain `git rebase -i main` folds them
```

`git absorb` (third-party; `cargo install git-absorb` or `brew install git-absorb`) creates the fixup commits for staged changes:

```bash
git add -p
git absorb
git rebase -i --autosquash main
```

## Inspecting History

```bash
git log --oneline --graph -20
git log --oneline main..HEAD
git diff main...HEAD              # three dots: diff from merge base
git log --grep="auth" --oneline   # search messages
git log -S "function_name"        # commits adding/removing this string
git log -G "regex_pattern"        # commits whose diff matches
git blame -w file.txt             # ignore whitespace
```

Branch-version comparison: [commands.md](commands.md#command-reference).

## Squash Merge

```bash
git switch main
git merge --squash feat/auth
git commit
```

| Strategy | Use when |
|----------|----------|
| Squash merge | Feature branches, PRs |
| Regular merge | Long-running branches where individual commits matter |
| Rebase + fast-forward | Linear history with individual commits preserved |

## Interactive Rebase

Clean up before pushing: `git rebase -i main` or `git rebase -i HEAD~5`. Actions: `pick`, `reword`, `edit`, `squash`, `fixup`, `drop`, reorder lines. Script the todo list with `GIT_SEQUENCE_EDITOR`: [commands.md](commands.md#scripted-rebase).

### Magit

- `r i` — interactive rebase
- `r o` — rebase onto (cascading branches)
- `r e` — rebase interactively from a specific commit

## Undo Patterns

```bash
git reset --soft HEAD~1           # undo last commit, keep changes staged
git reset HEAD~1                  # undo last commit, keep changes unstaged
git revert <sha>                  # undo a public commit with a reverse commit
git reflog                        # find a lost commit or deleted branch (entries expire after 90 days)
git switch -c recovered <sha>
```
