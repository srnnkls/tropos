---
name: issue
description: GitHub issue operations. Use when creating PRs from issues, viewing issue details, or linking issues to branches.
argument-hint: "[operation] [args]"
allowed-tools: Bash(gh issue *), Bash(gh pr *), Bash(git branch *), Bash(git push *), Bash(git rev-parse *)
metadata:
  type: domain
---

## Pre-loaded Context

Current branch:
!`git branch --show-current 2>/dev/null`

Issue number (from branch name prefix, e.g. `388-cache-…` → `388`):
!`git branch --show-current 2>/dev/null | grep -oE '^[0-9]+' | head -1 || echo "none"`

Existing PR for this branch:
!`gh pr view --json number,state,url --jq '"#\(.number) [\(.state)] \(.url)"' 2>/dev/null || echo "none"`

# Issue Skill

GitHub issue operations — links issues to branches and PRs.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| `pr` (with or without args) | Create PR | Read and follow [operations/pr.md](operations/pr.md) |
| No argument | Menu | See fallback |

> **Protocol:** [../dispatch/protocol.md](../dispatch/protocol.md)

---

## Menu Fallback

When no argument or ambiguous, use **AskUserQuestion**:

```
Header: Issue
Question: What would you like to do?
multiSelect: false
Options:
- PR: Create a pull request for the current branch
```

| Selection | Action |
|---|---|
| PR | Read and follow [operations/pr.md](operations/pr.md) |

---

## Reference

- [operations/pr.md](operations/pr.md) - Create PR from current branch, optionally linked to an issue
