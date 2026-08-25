# Git Worktrees

Existing worktrees:
!`git worktree list 2>/dev/null`

Git worktrees create isolated workspaces sharing the same repository. Systematic directory selection + safety verification = reliable isolation.

---

## When to Use

**Use for:**
- Feature work needing isolation from current workspace
- Parallel work on multiple branches
- Before executing implementation plans

**Don't use for:**
- Quick fixes on current branch
- Single-file changes
- When isolation isn't needed

---

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories

```bash
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```

**If found:** Use that directory. If both exist, `.worktrees` wins.

### 2. Check Project Config

Look for worktree directory preference in project documentation (CLAUDE.md, README, etc.).

**If preference specified:** Use it without asking.

### 3. Ask User

If no directory exists and no preference found:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/worktrees/<project-name>/ (global location)

Which would you prefer?
```

---

## Safety Verification

### For Project-Local Directories

**MUST verify .gitignore before creating worktree:**

```bash
grep -q "^\.worktrees/$" .gitignore || grep -q "^worktrees/$" .gitignore
```

**If NOT in .gitignore:**
1. Add appropriate line to .gitignore
2. Commit the change
3. Proceed with worktree creation

### For Global Directory

No .gitignore verification needed - outside project entirely.

---

## Creation Steps

### 1. Detect Project Name

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Create Worktree

`BASE` is the resolved base from the caller (e.g. `implement` Git Workflow step 3). When the base is the trunk, fetch and use the remote ref — a worktree created from local `main` or bare HEAD forks from whatever stale state the checkout happens to be in.

```bash
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

### 3. Link Ignored Repo-Root State

Ignored files the worktree needs — `scopes/`, `mise.local.toml`, local resources — are linked from the main worktree, never copied. Three things have to hold, and each fails quietly when it doesn't.

#### 3a. The path must be gitignored

`git worktreeinclude` never touches tracked files. A tracked path listed in `.worktreeinclude` resolves to zero leaves and produces nothing at the target — `apply` still exits `0`, and under `--quiet` (what the hook runs) you see no trace at all.

```bash
git check-ignore -q scopes || echo "scopes/ is tracked — worktreeinclude will skip it"
```

A tracked `scopes/` gets committed onto the feature branch, and from then on the branch carries a frozen copy while the main worktree keeps editing the live one. Fix it at the repo root *before* cutting the branch:

```bash
git rm -r --cached scopes
printf '/scopes/\n' >> .gitignore
git commit -m "chore: untrack scopes/"
```

Doing it afterwards is worse than useless — the branch still points at a commit containing the copy, and amending the base to remove it orphans the branch from trunk.

#### 3b. The entry needs an explicit `symlink`

Entries live in `.worktreeinclude` at the repo root, one `<path> <mode>` pair per line:

```
mise.local.toml  symlink
scopes/          symlink
```

`copy` is the default mode. A bare `scopes/` line duplicates the tree instead of linking it — the drift this whole section exists to prevent. When a path matches both a copy-mode and a symlink-mode pattern, symlink wins.

The include file is read from the *source* worktree, the one `--from auto` picks. Adding an entry inside the linked worktree does nothing; add it at the repo root, then re-run `apply`.

#### 3c. Verify the result, not the exit code

```bash
git worktreeinclude apply
[ -L scopes ] || echo "scopes/ is not a symlink"
```

Exit `0` does not mean anything was linked. `apply` is a no-op success when `.worktreeinclude` is absent from the source worktree, and when the repo has only one worktree. Exit `3` means conflicts — the target already holds differing content; resolve it or pass `--force`.

#### 3d. Keep it linked across branch switches

`apply` runs only when something runs it. In a repo using `hk`, a post-checkout hook re-links after every switch:

```pkl
["post-checkout"] {
  steps {
    ["worktreeinclude"] {
      check = "git worktreeinclude apply --quiet"
    }
  }
}
```

Then `hk install`. Without a hook, `apply` by hand after `worktree add` — some shells wrap `git worktree add` to do this automatically, so check before assuming it didn't run.

### 4. Run Project Setup

Auto-detect and run appropriate setup:

```bash
# Detect project type and install dependencies
if [ -f package.json ]; then npm install; fi
if [ -f Cargo.toml ]; then cargo build; fi
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then pip install -e .; fi
if [ -f go.mod ]; then go mod download; fi
```

### 5. Verify Clean Baseline

Run tests to ensure worktree starts clean:

```bash
# Use project-appropriate command
npm test / cargo test / pytest / go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### 6. Report Location

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify .gitignore) |
| `worktrees/` exists | Use it (verify .gitignore) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check config then ask user |
| Not in .gitignore | Add it immediately + commit |
| Worktree needs `scopes/` or other ignored state | `git worktreeinclude apply` (symlink, never copy) |
| `scopes/` is tracked | Untrack + ignore at the root **before** cutting the branch |
| `.worktreeinclude` entry has no mode | Add `symlink` — bare entries copy |
| `apply` exits 0 | Prove nothing: check `[ -L scopes ]` |
| `apply` exits 3 | Conflict — resolve target, or `--force` |
| Repo uses `hk` | Add the post-checkout `worktreeinclude` step |
| Tests fail | Report failures + ask |

---

## Red Flags

**Never:**
- Copy `scopes/`, skill directories, or any repo-root state into a worktree — symlink via `.worktreeinclude`
- Write a `.worktreeinclude` entry without a mode — the default is `copy`
- Read `git worktreeinclude apply` exiting 0 as proof the link exists
- Cut a feature branch while `scopes/` is still tracked
- Create worktree without .gitignore verification (project-local)
- Skip baseline test verification
- Proceed with failing tests without asking
- Assume directory location when ambiguous

**Always:**
- Follow directory priority: existing > config > ask
- Verify .gitignore for project-local
- Auto-detect and run project setup
- Verify clean test baseline

---

## Integration

**Use with:**
- `implement` - Work happens in this worktree
