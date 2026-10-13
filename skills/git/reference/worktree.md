# Git Worktrees

Existing worktrees:
```bash
git worktree list 2>/dev/null
```

## When to Use

Use for feature work needing isolation from the current workspace, parallel work on several branches, or before executing an implementation plan. Not for quick fixes on the current branch or single-file changes. `implement` works in this worktree.

## Directory Selection

First match wins; never assume a location when ambiguous.

1. Existing directory: `.worktrees/` (wins if both exist), else `worktrees/`.
   ```bash
   ls -d .worktrees 2>/dev/null
   ls -d worktrees 2>/dev/null
   ```
2. A worktree directory named in project documentation (CLAUDE.md, README, etc.): use it without asking.
3. Otherwise ask:
   ```
   No worktree directory found. Where should I create worktrees?

   1. .worktrees/ (project-local, hidden)
   2. ~/worktrees/<project-name>/ (global location)

   Which would you prefer?
   ```

A project-local directory must be gitignored before creating a worktree; if it is not, add the line to `.gitignore`, commit, then proceed. A global directory needs no check.

```bash
grep -q "^\.worktrees/$" .gitignore || grep -q "^worktrees/$" .gitignore
```

## Creation

1. Detect the project name:
   ```bash
   project=$(basename "$(git rev-parse --show-toplevel)")
   ```
2. Create from `BASE`, the base resolved by the caller (e.g. `implement` Git Workflow step 3). For a trunk base, fetch and use the remote ref; local `main` or bare HEAD forks from stale state. Resolve `path` against the repository root: a relative path run from inside another worktree silently nests under that worktree's `.worktrees/`.
   ```bash
   cd "$(git rev-parse --show-toplevel)"
   trunk=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@origin/@@')
   case "$BASE" in
     origin/*) git fetch origin "${BASE#origin/}" ;;
     "${trunk:-main}"|main|master) git fetch origin "$BASE" && BASE="origin/$BASE" ;;
     *) ;;  # non-trunk local base (cascading) — local may be ahead of remote; keep as-is
   esac
   git worktree add "$path" -b "$BRANCH_NAME" "$BASE"
   cd "$path"
   ```
   If the branch already exists, omit `-b`/`$BASE` and run the base-drift preflight after entering the worktree.
3. Link ignored repo-root state (`scopes/`, `mise.local.toml`, local resources) from the main worktree; never copy `scopes/`, skill directories or other repo-root state. Each condition fails silently:
   - The path must be gitignored. `git worktreeinclude` skips tracked paths, and `apply` still exits `0` (no output under `--quiet`, which the hook uses).
     ```bash
     git check-ignore -q scopes || echo "scopes/ is tracked — worktreeinclude will skip it"
     ```
     A tracked `scopes/` gets committed onto the feature branch as a frozen copy. Untrack it at the repo root before cutting the branch; afterwards the branch still holds the copy, and amending the base orphans the branch from trunk.
     ```bash
     git rm -r --cached scopes
     printf '/scopes/\n' >> .gitignore
     git commit -m "chore: untrack scopes/"
     ```
   - Each `.worktreeinclude` entry (repo root, one `<path> <mode>` per line) needs an explicit `symlink`; the default mode is `copy`. Symlink wins when a path matches both modes. The file is read from the source worktree (`--from auto`): add entries at the repo root, then re-run `apply`.
     ```
     mise.local.toml  symlink
     scopes/          symlink
     ```
   - Verify the link, not the exit code. `apply` also exits `0` when `.worktreeinclude` is absent from the source worktree or the repo has one worktree. Exit `3` means the target holds differing content: resolve it or pass `--force`.
     ```bash
     git worktreeinclude apply
     [ -L scopes ] || echo "scopes/ is not a symlink"
     ```
   - Re-link after branch switches. With `hk`, add this post-checkout step and run `hk install`; without a hook, run `apply` after `worktree add` (some shells wrap `git worktree add` to run it; check first).
     ```pkl
     ["post-checkout"] {
       steps {
         ["worktreeinclude"] {
           check = "git worktreeinclude apply --quiet"
         }
       }
     }
     ```
4. Run project setup:
   ```bash
   if [ -f package.json ]; then npm install; fi
   if [ -f Cargo.toml ]; then cargo build; fi
   if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
   if [ -f pyproject.toml ]; then pip install -e .; fi
   if [ -f go.mod ]; then go mod download; fi
   ```
5. Run the project's tests (`npm test` / `cargo test` / `pytest` / `go test ./...`). On failure, report and ask whether to proceed or investigate. On pass, report:
   ```
   Worktree ready at <full-path>
   Tests passing (<N> tests, 0 failures)
   Ready to implement <feature-name>
   ```

## Removal

Remove only with `git worktree remove`; deleting the directory by hand leaves stale metadata in `.git/worktrees/`.

1. Leave the worktree:
   ```bash
   cd "$(git rev-parse --path-format=absolute --git-common-dir)/.."
   ```
2. Check for work; any output is work to commit, push or report, never to discard for removal:
   ```bash
   git -C "$path" status --porcelain
   git -C "$path" log --oneline '@{u}..' 2>/dev/null || git -C "$path" log --oneline "origin/$trunk.."
   ```
3. `git worktree remove "$path"`:
   - Modified tracked or untracked files: refuses (exit `128`); `--force` discards them. Do not force past it.
   - Gitignored files, including `.worktreeinclude` symlinks: removed silently; link targets in the main worktree survive.
   - Locked worktree: refuses even with one `--force`; run `git worktree unlock "$path"` first, or `-f -f` after confirming why it was locked.
   - Unpushed commits: not checked; they survive only through the branch.
4. Delete the branch only once its work is merged or pushed: `git branch -d "$BRANCH_NAME"`. A squash-merged branch looks unmerged to `-d`; confirm the merge on the remote before `-D`.
