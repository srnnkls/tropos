# Branch Management

## Branching from Main vs. Cascading

**Independent work:** Branch from `main`. No rebase coordination needed.

**Dependent work:** Cascade from the branch you depend on. Accept the rebase tax.

**The rebase tax:** Every time an upstream branch's ref changes (force-push during review, squash merge into main), all downstream branches need `rebase --onto`.

## Cascading Workflow

### Setup

```
main ── M1 ── M2
                 \
        A:        A1 ── A2 ── A3
                                 \
        B:                        B1 ── B2
                                         \
        C:                                C1
```

### Merging the Chain

Merge bottom-up, rebase after each merge:

```bash
# 1. Squash merge A into main
git switch main && git merge --squash A && git commit

# 2. Rebase B onto main (skip A's commits)
git switch B
git rebase --onto main A

# 3. Squash merge B into main
git switch main && git merge --squash B && git commit

# 4. Rebase C onto main (skip B's commits)
git switch C
git rebase --onto main B

# 5. Squash merge C into main
git switch main && git merge --squash C && git commit
```

### Handling Force-Pushes During Review

When A gets force-pushed after review feedback:

```bash
# Save A's old tip before pull
old_a=$(git rev-parse A)

# Update A
git switch A && git pull --rebase

# Rebase B onto updated A
git switch B
git rebase --onto A $old_a
```

Or if you didn't save the old tip: `git reflog show A` to find it.

### rebase --onto Explained

```
git rebase --onto <new-base> <old-base> [<branch>]
```

- `<new-base>`: Where to place the commits (target)
- `<old-base>`: Where to cut from (exclusive — commits after this get replayed)
- `<branch>`: Branch to rebase (defaults to current)

The command means: take commits between `<old-base>` and `<branch>`, replay them onto `<new-base>`.

### Magit

1. Checkout the branch to rebase
2. `r` (rebase menu)
3. `o` (rebase onto)
4. **"onto"** prompt → enter target (e.g., `main`)
5. **"start"** prompt → enter the old base branch name (e.g., `A`)

## Branch Naming

```
feat/<name>     # New functionality
fix/<name>      # Bug fix
chore/<name>    # Maintenance, deps, config
refactor/<name> # Restructuring without behavior change
docs/<name>     # Documentation only
```

## Rules

1. Rebase downstream before upstream ref changes identity
2. Merge the chain in order, bottom-up
3. Delete upstream branch only after downstream is rebased
4. Keep branches short-lived — merge often
5. One concern per branch
