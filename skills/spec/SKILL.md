---
name: spec
description: Unified spec lifecycle dispatcher. Auto-detects operation from argument or presents selection menu. Routes to spec-create, spec-review, spec-update, spec-promote, spec-archive, or spec-issues-create.
argument-hint: "[operation] [spec-name]"
allowed-tools: Bash(find *), Bash(git branch *)
---

## Pre-loaded Context

Draft specs:
!`find ./specs/draft -maxdepth 1 -mindepth 1 -type d 2>/dev/null`

Active specs:
!`find ./specs/active -maxdepth 1 -mindepth 1 -type d 2>/dev/null`

Archived specs:
!`find ./specs/archive -maxdepth 1 -mindepth 1 -type d 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

# Spec Lifecycle Dispatcher

Routes to the appropriate spec skill based on the operation keyword.

---

## Auto-Detect Rules

Parse `$ARGUMENTS` as `$0 $1` where `$0` is the operation keyword and `$1` is the spec name.

| Keyword (`$0`) | Route | Invocation |
|---|---|---|
| `create` | Create new spec | `Skill(spec-create, $1)` |
| `review` | Review spec | `Skill(spec-review, $1)` |
| `update` | Sync from git | `Skill(spec-update, $1)` |
| `promote` | Draft to active | `Skill(spec-promote, $1)` |
| `archive` | Archive completed | `Skill(spec-archive, $1)` |
| `issues` | Generate GH issues | `Skill(spec-issues-create, $1)` |
| No keyword | Menu fallback | See below |

---

## Menu Fallback

When no argument or unrecognized keyword, use **AskUserQuestion**:

```
Header: Spec
Question: What spec operation would you like to perform?
multiSelect: false
Options:
- Create: Validate requirements and create tracking documents
- Review: Multi-agent spec review with parallel reviewers
- Update: Sync task status from git history
- Promote: Move spec from draft to active stage
```

With "Other" covering: archive, issues (less common operations).

**Routing by selection:**

| Selection | Action |
|---|---|
| Create | `Skill(spec-create)` |
| Review | `Skill(spec-review)` |
| Update | `Skill(spec-update)` |
| Promote | `Skill(spec-promote)` |
| Other: archive | `Skill(spec-archive)` |
| Other: issues | `Skill(spec-issues-create)` |

---

## Delegation Pattern

1. Parse `$ARGUMENTS` into operation keyword and spec name
2. If keyword matches: invoke target skill with spec name
3. If no keyword: present AskUserQuestion menu
4. Based on selection: invoke target skill
5. Target skill handles any further interaction (spec name, options, etc.)

Do NOT duplicate target skill logic. Only route.
