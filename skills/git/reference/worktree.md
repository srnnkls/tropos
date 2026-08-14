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

Ignored files the worktree needs — `scopes/`, `mise.local.toml`, local resources — are linked from the main worktree, never copied:

```bash
git worktreeinclude apply
```

Entries live in `.worktreeinclude` at the repo root, one `<path> <mode>` pair per line:

```
mise.local.toml  symlink
scopes/          symlink
```

If the file is missing or lacks an entry the worktree needs, add the entry at the repo root, then re-run `apply`.

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
| Tests fail | Report failures + ask |

---

## Red Flags

**Never:**
- Copy `scopes/`, skill directories, or any repo-root state into a worktree — symlink via `.worktreeinclude`
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
