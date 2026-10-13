---
allowed-tools: Bash(gh issue *), Bash(gh pr *), Bash(git branch *), Bash(git push *), Bash(git rev-parse *), Bash(git log *), Bash(git merge-base *)
---

## Runtime Context

Run before preparing the pull request:

```bash
git branch --show-current 2>/dev/null                                                       # current branch
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo "no upstream"
gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo "main"
gh pr view --json number,state,url --jq '"#\(.number) [\(.state)] \(.url)"' 2>/dev/null || echo "none"
```

Issue number (branch name prefix, e.g. `388-cache-…` → `388`) and metadata:
```bash
ISSUE_NUM=$(git branch --show-current 2>/dev/null | grep -oE '^[0-9]+' | head -1)
if [ -n "$ISSUE_NUM" ]; then
  gh issue view "$ISSUE_NUM" --json number,title,body,labels \
    --jq '"#\(.number): \(.title)\n\nBody:\n\(.body)\n\nLabels: \([.labels[].name] | join(", "))"' \
    2>/dev/null || echo "Issue $ISSUE_NUM not found or not accessible"
else
  echo "none"
fi
```

Branch commits since the default branch, and the dominant conventional commit types:
```bash
DEFAULT=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null || echo "main")
BASE=$(git merge-base HEAD "origin/$DEFAULT" 2>/dev/null || git merge-base HEAD "$DEFAULT" 2>/dev/null)
if [ -n "$BASE" ]; then
  git log --oneline "$BASE"..HEAD 2>/dev/null | head -15
else
  git log --oneline -10 2>/dev/null
fi
RANGE="${BASE:+$BASE..HEAD}"
git log --format="%s" ${RANGE:-HEAD} 2>/dev/null \
  | grep -oE '^[a-z]+(\(|!|:)' | tr -d '(!:' \
  | sort | uniq -c | sort -rn \
  | head -3 || echo "none detected"
```

# PR Creation Operation

## Flags

Parse from `$ARGUMENTS`; ignore other tokens. Without `--issue` or a branch prefix, `ISSUE_NUM` is empty.

| Flag | Default | Sets |
|------|---------|------|
| `--state draft\|open` | `draft` | `STATE` |
| `--issue <n>` | issue number from context | `ISSUE_NUM`; when it overrides the context, fetch with `gh issue view $ISSUE_NUM --json number,title,body --jq '"#\(.number): \(.title)\n\(.body)"'` |
| `--title <text>` | derived | `TITLE_OVERRIDE` |
| `--base <branch>` | default branch from context | `BASE` |

## Workflow

### 1. Build PR Title

Commit-message format and type vocabulary from the `git.commits` providers ([Commits](../../git/SKILL.md#commits)), suffixed ` (#<ISSUE_NUM>)` when an issue is linked.

- Type: dominant commit type from context; else by issue label: `bug`/`fix` → `fix`, `feature`/`enhancement` → `feat`, `refactor` → `refactor`, `docs`/`documentation` → `docs`, `chore`/`maintenance` → `chore`, `perf`/`performance` → `perf`, `test` → `test`; else `feat`.
- Scope: when derivable, the most specific issue-title noun, lowercase without spaces.
- Description: without the issue number, type prefix, or trailing period.

Source: `--title` (warn if not conventional), else issue title, else branch slug with `feat`. Total ≤ 72 characters; truncate only the description.

### 2. Build PR Body

With issue (first paragraph or first 5 bullets):

```
## Summary

<excerpt from issue body — first paragraph or bullet list>

Closes #<ISSUE_NUM>
```

Without issue:

```
## Summary

<synthesized from commits in pre-loaded context — group by theme, 3–5 bullets>
```

### 3. Push Branch

- `no upstream` → `git push -u origin <branch>`
- Upstream set → `git push`

### 4. Handle Existing PR

- `none` → create (step 5)
- State matches `--state` → report URL, stop
- `DRAFT`, `--state open` → `gh pr ready <number>`
- `OPEN`, `--state draft` → `gh pr ready --undo <number>`

Never create a second PR for the branch.

### 5. Create PR

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

Omit `--draft` for `--state open`.

### 6. Report

Output the PR URL; with a linked issue, confirm the body has `Closes #<ISSUE_NUM>`.

## Error Handling

| Condition | Action |
|-----------|--------|
| `gh` not authenticated | Report: run `gh auth login` |
| Issue not found | Warn and proceed without issue metadata; use commit log for body |
| `--state` value unrecognized | Default to `draft`, warn |
