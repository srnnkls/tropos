---
name: git
description: Modern git workflows plus dispatched operations (rebase strategy analysis). Use when managing branches, structuring commits, choosing development strategies, or planning a rebase.
argument-hint: "[operation] [args]"
allowed-tools: Bash(git status *), Bash(git log *), Bash(git branch *), Bash(git rev-parse *)
metadata:
  type: domain
---

## Pre-loaded Context

Current branch:
!`git branch --show-current 2>/dev/null`

Status:
!`git status --short 2>/dev/null | head -10`

# Git Skill

Dispatches operations and provides reference knowledge for modern git workflows.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| `rebase` (with or without args) | Rebase strategy | Read and follow [operations/rebase.md](operations/rebase.md) |
| No argument | Knowledge | Use sections below as reference |

> **Protocol:** [../dispatch/protocol.md](../dispatch/protocol.md)

---

## Menu Fallback

When no argument and the user wants an operation rather than reference, use **AskUserQuestion**:

```
Header: Git
Question: What would you like to do?
multiSelect: false
Options:
- Rebase: Analyze branch state and recommend a rebase strategy (--onto, autosquash, etc.)
- Reference: Show modern git workflow knowledge below
```

| Selection | Action |
|---|---|
| Rebase | Read and follow [operations/rebase.md](operations/rebase.md) |
| Reference | Continue with sections below |

---

# Modern Git Workflows

Trunk-based development with short-lived branches, squash merges, and modern git tooling.

---

## Development Model

**Trunk-based with short-lived branches:**

- `main` is always deployable
- Branch per feature/fix, squash merge back
- Branches live hours to days, not weeks
- Merge often — pain comes from divergence

**Branch naming:** `<type>/<short-description>` (e.g., `feat/auth`, `fix/null-check`, `chore/deps`)

---

## Quick Reference

**Modern command replacements:**

| Legacy | Modern | Why |
|--------|--------|-----|
| `git checkout <branch>` | `git switch <branch>` | Dedicated branch switching |
| `git checkout -b <branch>` | `git switch -c <branch>` | Explicit create-and-switch |
| `git checkout -- <file>` | `git restore <file>` | Dedicated file restoration |
| `git checkout HEAD -- <file>` | `git restore -s HEAD <file>` | Restore from specific ref |
| `git stash` | `git stash push -m "msg"` | Named stashes with pathspec |
| `git push --force` | `git push --force-with-lease` | Prevents overwriting others' work |
| `git log -p` | `git log --remerge-diff` | Shows merge conflict resolutions |

**Commit hygiene:**

```bash
git commit --fixup <sha>         # Mark as fixup for <sha>
git rebase -i --autosquash main  # Auto-fold fixups into targets
```

**Parallel workspaces:**

```bash
git worktree add ../feat-auth -b feat/auth
git worktree list
git worktree remove ../feat-auth
```

**Performance (large repos):**

```bash
git maintenance start            # Background optimization
git sparse-checkout set src/     # Only checkout what you need
git clone --filter=blob:none     # Partial clone (fetch blobs on demand)
```

**Conflict memory:**

```bash
git config rerere.enabled true   # Remember conflict resolutions
```

---

## Cascading Branches

When features build on each other, cascade is natural. The discipline is in the rebase.

```
main:  M1 - M2
                \
A:               A1 - A2 - A3
                              \
B:                             B1 - B2
```

**Rule:** Rebase downstream branches before the upstream ref changes identity (squash merge, force-push, delete).

```bash
# After squash-merging A into main:
git switch B
git rebase --onto main A         # Replays B1-B2 onto main, skipping A's commits

# Then delete A
git branch -d A
```

**Merge the chain bottom-up:** merge A, rebase B onto main, merge B, rebase C onto main.

See [reference/branching.md](reference/branching.md) for details.

---

## Modern Features Worth Knowing

| Feature | Since | Use Case |
|---------|-------|----------|
| `switch` / `restore` | 2.23 | Replace overloaded `checkout` |
| `--force-with-lease` | 2.13 | Safe force push |
| `commit --fixup` | 2.32+ | Amend past commits without interactive rebase |
| `range-diff` | 2.19 | Compare rebase before/after |
| `worktree` | 2.5+ | Parallel branch work without stashing |
| `maintenance` | 2.29 | Background gc, prefetch, commit-graph |
| `sparse-checkout` | 2.25 | Large monorepo subset |
| `--filter=blob:none` | 2.19 | Partial clone |
| `blame --ignore-rev` | 2.23 | Skip formatting commits in blame |
| `diff --color-moved` | 2.17 | Distinguish moved vs changed code |
| `rerere` | old | Reuse recorded merge resolutions |
| `log --remerge-diff` | 2.35 | Show what a merge actually resolved |

See [reference/commands.md](reference/commands.md) and [reference/history.md](reference/history.md) for patterns.

---

## Anti-Patterns

- Squash merging a branch while downstream branches depend on it (rebase first)
- Long-lived feature branches (merge often, keep branches short)
- `git push --force` without `--lease` (overwrites others' work)
- Using `checkout` for both branch switching and file restoration
- Manual fixup of past commits (use `--fixup` + `--autosquash`)
- Deleting upstream branch before rebasing downstream branches
- Inverting `rebase --onto` direction — the checked-out branch becomes a descendant of `<new-base>`, not the other way around. State intent in one sentence ("X will sit on top of Y") before running.
- Committing, force-pushing, or squash-merging on top of a rebase without first verifying topology (`git log --oneline --graph <base>..HEAD`). A misrouted rebase is recoverable; a squash-merge of a misrouted branch into an integration ref is not.

---

## Related Skills

- **bash**: Shell command patterns
- **issue**: GitHub issue operations (create PRs, link issues to branches)

---

## Operations

- [operations/rebase.md](operations/rebase.md) - Branch state analysis and rebase strategy recommendation

## Reference

- [reference/branching.md](reference/branching.md) - Cascading branch patterns
- [reference/commands.md](reference/commands.md) - Command patterns
- [reference/history.md](reference/history.md) - History management
- [reference/worktree.md](reference/worktree.md) - Worktree creation with safety checks
