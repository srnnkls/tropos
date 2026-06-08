---
allowed-tools: Bash(gh issue *), Bash(gh pr *), Bash(git branch *), Bash(git push *), Bash(git rev-parse *), Bash(git log *), Bash(git merge-base *)
---

## Pre-loaded Context

Current branch:
!`git branch --show-current 2>/dev/null`

Upstream tracking:
!`git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo "no upstream"`

Default branch:
!`gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo "main"`

Issue number (from branch name prefix, e.g. `388-cache-…` → `388`):
!`git branch --show-current 2>/dev/null | grep -oE '^[0-9]+' | head -1 || echo "none"`

Issue metadata (fetched from issue number above; empty if no issue detected):
```!
ISSUE_NUM=$(git branch --show-current 2>/dev/null | grep -oE '^[0-9]+' | head -1)
if [ -n "$ISSUE_NUM" ]; then
  gh issue view "$ISSUE_NUM" --json number,title,body,labels \
    --jq '"#\(.number): \(.title)\n\nBody:\n\(.body)\n\nLabels: \([.labels[].name] | join(", "))"' \
    2>/dev/null || echo "Issue $ISSUE_NUM not found or not accessible"
else
  echo "none"
fi
```

Commits on this branch since it diverged from default branch:
```!
DEFAULT=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo "main")
BASE=$(git merge-base HEAD "origin/$DEFAULT" 2>/dev/null || git merge-base HEAD "$DEFAULT" 2>/dev/null)
if [ -n "$BASE" ]; then
  git log --oneline "$BASE"..HEAD 2>/dev/null | head -15
else
  git log --oneline -10 2>/dev/null
fi
```

Dominant conventional commit type on this branch (ranked by frequency):
```!
DEFAULT=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo "main")
BASE=$(git merge-base HEAD "origin/$DEFAULT" 2>/dev/null || git merge-base HEAD "$DEFAULT" 2>/dev/null)
RANGE="${BASE:+$BASE..HEAD}"
git log --format="%s" ${RANGE:-HEAD} 2>/dev/null \
  | grep -oE '^(feat|fix|refactor|chore|docs|test|perf|ci|style|build)' \
  | sort | uniq -c | sort -rn \
  | head -3 || echo "none detected"
```

Existing PR for this branch:
!`gh pr view --json number,state,url --jq '"#\(.number) [\(.state)] \(.url)"' 2>/dev/null || echo "none"`

# PR Creation Operation

Create a pull request for the current branch, optionally linked to a GitHub issue.

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--state draft\|open` | `draft` | PR visibility state |
| `--issue <n>` | auto-detect | Issue number to link (overrides branch detection) |
| `--title <text>` | from issue / branch | PR title override |
| `--base <branch>` | default branch | Base branch for the PR |

---

## Workflow

### 1. Parse Arguments

Extract from `$ARGUMENTS`:
- `--state <value>` → `STATE` (`draft` or `open`; default: `draft`)
- `--issue <n>` → `ISSUE_NUM` (overrides branch-detected issue number in pre-loaded context)
- `--title <text>` → `TITLE_OVERRIDE`
- `--base <branch>` → `BASE` (overrides default branch in pre-loaded context)

Remaining tokens after flag extraction are ignored.

### 2. Resolve Issue Number and Base Branch

- **Issue number:** Use `--issue <n>` if provided; otherwise use the issue number from pre-loaded context (branch name prefix). If neither yields a number, `ISSUE_NUM` is empty.
- **Base branch:** Use `--base <branch>` if provided; otherwise use the default branch from pre-loaded context.
- **Issue metadata:** Already available in pre-loaded context — no additional `gh` call needed unless `--issue` overrides the detected number.

If `--issue` overrides the branch-detected number, fetch the new issue's title and body:

```bash
gh issue view $ISSUE_NUM --json number,title,body --jq '"#\(.number): \(.title)\n\(.body)"'
```

### 3. Build PR Title

All PR titles MUST follow conventional commit format:

```
<type>(<scope>): <description> (#<ISSUE_NUM>)
```

**`<type>`** — pick from the dominant commit type in pre-loaded context; fall back to this label→type mapping:

| Issue label | Type |
|-------------|------|
| `bug` / `fix` | `fix` |
| `feature` / `enhancement` | `feat` |
| `refactor` | `refactor` |
| `docs` / `documentation` | `docs` |
| `chore` / `maintenance` | `chore` |
| `perf` / `performance` | `perf` |
| `test` | `test` |
| No label / unknown | `feat` |

**`(<scope>)`** — optional but preferred. Derive from the most specific noun in the issue title (e.g. `RfcSchema — back call()…` → `rfcschema`; `Cache TTL expiry` → `cache`). Lowercase, no spaces.

**`<description>`** — imperative, lowercase, no period. Strip the issue number and type prefix if already present in the issue title. Keep under 60 characters after type+scope.

**`(#<ISSUE_NUM>)`** — append when an issue is linked; omit otherwise.

Priority:
1. `--title <text>` if provided — still MUST be conventional commit format; validate and warn if not
2. Derived from issue title + type + scope rules above
3. Branch slug as description, `feat` as type (fallback when no issue linked)

Total title length: ≤ 72 characters. Truncate description if needed (never truncate type/scope/issue ref).

### 4. Build PR Body

**With issue linked:**

```
## Summary

<excerpt from issue body — first paragraph or bullet list>

Closes #<ISSUE_NUM>
```

Use the issue body already present in pre-loaded context. Trim to the first meaningful paragraph or first 5 bullets if the body is long.

**Without issue:**

```
## Summary

<synthesized from commits in pre-loaded context — group by theme, 3–5 bullets>
```

### 5. Push Branch (if not already pushed)

Pre-loaded context shows whether upstream is set:
- `no upstream` → `git push -u origin <branch>`
- Upstream set → `git push` to sync any new commits

### 6. Handle Existing PR

Pre-loaded context shows whether a PR exists:
- **`none`** → proceed to create
- **PR exists + state matches `--state`** → report URL, no action needed
- **PR is `DRAFT`, `--state open`** → `gh pr ready <number>`
- **PR is `OPEN`, `--state draft`** → `gh pr ready --undo <number>`

Do NOT create a duplicate PR.

### 7. Create PR

**If `--state draft` (default):**

```bash
gh pr create \
  --draft \
  --title "<TITLE>" \
  --body "$(cat <<'EOF'
<BODY>
EOF
)" \
  --base <BASE>
```

**If `--state open`:**

```bash
gh pr create \
  --title "<TITLE>" \
  --body "$(cat <<'EOF'
<BODY>
EOF
)" \
  --base <BASE>
```

### 8. Report

Output the PR URL.

If issue was linked: confirm `Closes #<ISSUE_NUM>` is in the body so GitHub auto-closes the issue on merge.

---

## Error Handling

| Condition | Action |
|-----------|--------|
| `gh` not authenticated | Report: run `gh auth login` |
| Issue not found | Warn and proceed without issue metadata; use commit log for body |
| Branch not pushed | Push first (step 5), then create PR |
| PR already exists | Report URL, convert state if mismatch (step 6) |
| `--state` value unrecognized | Default to `draft`, warn |
