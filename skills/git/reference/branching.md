# Branch Management

## Branching from Main vs. Cascading

Branch independent work from `main`. Cascade dependent work from the branch it depends on; every change to an upstream ref (force-push during review, squash merge into main) then requires `rebase --onto` for each downstream branch. Rebase downstream branches before the upstream ref changes identity, and delete an upstream branch only after its downstream branches are rebased.

## Cascading Workflow

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

Bottom-up, rebasing after each merge:

```bash
git switch main && git merge --squash A && git commit
git switch B && git rebase --onto main A      # skip A's commits
git switch main && git merge --squash B && git commit
git switch C && git rebase --onto main B
git switch main && git merge --squash C && git commit
```

### Handling Force-Pushes During Review

```bash
old_a=$(git rev-parse A)          # save A's old tip before pulling
git switch A && git pull --rebase
git switch B && git rebase --onto A $old_a
```

Without a saved tip, find it with `git reflog show A`.

### rebase --onto Explained

```
git rebase --onto <new-base> <old-base> [<branch>]
```

- `<new-base>`: where the commits land
- `<old-base>`: exclusive cut point; commits after it are replayed
- `<branch>`: branch to move (default: current)

#### Direction trap

`<branch>` moves and becomes a descendant of `<new-base>`. When work belongs on branch B, commit directly on B, or move a downstream onto B with `git switch <downstream> && git rebase --onto B <old-tip>`. After any `--onto` rebase, confirm the parent chain with `git log --oneline --graph <expected-base>..HEAD` before anything else.

### Magit

Check out the branch to rebase, then `r` `o`; at "onto" enter the target (e.g. `main`), at "start" the old base branch (e.g. `A`).

## Branch Naming

```
feat/<name>     # New functionality
fix/<name>      # Bug fix
chore/<name>    # Maintenance, deps, config
refactor/<name> # Restructuring without behavior change
docs/<name>     # Documentation only
```

One concern per branch.
