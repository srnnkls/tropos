---
name: review
description: Unified review dispatcher. Auto-detects review type from argument or presents selection menu. Routes to code-review, pr-review, or spec-review.
argument-hint: "[target]"
allowed-tools: Bash(git status *), Bash(git log *), Bash(git branch *), Bash(find *), Bash(gh pr list *)
---

## Pre-loaded Context

Git status:
!`git status --short 2>/dev/null`

Recent commits:
!`git log --oneline -5 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

Active specs:
!`find ./specs/active -maxdepth 1 -mindepth 1 -type d 2>/dev/null`

Open PRs:
!`gh pr list --limit 5 --json number,title,headRefName --jq '.[] | "#\(.number) \(.title) (\(.headRefName))"' 2>/dev/null`

# Review Dispatcher

Routes to the appropriate review skill based on argument type.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Invocation |
|---|---|---|
| Numeric, `#N`, or GitHub PR URL | PR review | `Skill(pr-review, $ARGUMENTS)` |
| 7+ hex chars (commit SHA) | Commit review | `Skill(code-review, --rev $ARGUMENTS)` |
| Matches `./specs/active/*/` | Spec review | `Skill(spec-review, $ARGUMENTS)` |
| File path that exists | Path review | `Skill(code-review, --path $ARGUMENTS)` |
| No argument | Menu fallback | See below |

---

## Menu Fallback

When no argument or ambiguous, use **AskUserQuestion**:

```
Header: Review
Question: What would you like to review?
multiSelect: false
Options:
- PR: Review a GitHub pull request — inline comments and structured summary
- Commit: Review changes in a specific commit
- Branch diff: Review all changes since diverging from base branch
- Uncommitted: Review staged and unstaged modifications
```

With "Other" covering: spec review, path review, or custom target.

**Routing by selection:**

| Selection | Action |
|---|---|
| PR | `Skill(pr-review)` — target skill asks for PR # |
| Commit | `Skill(code-review, --rev ...)` — ask for SHA first |
| Branch diff | `Skill(code-review, --diff <base>..HEAD)` — ask for base branch first |
| Uncommitted | `Skill(code-review)` — auto-detects staged/unstaged |
| Other: spec | `Skill(spec-review)` — target skill asks for spec |

---

## Delegation Pattern

1. Check `$ARGUMENTS` against auto-detect rules (in order)
2. If match: invoke target skill directly
3. If no match: present AskUserQuestion menu
4. Based on selection: invoke target skill
5. Target skill handles any further interaction (PR number, SHA, etc.)

Do NOT duplicate target skill logic. Only route.
