---
name: review
description: Unified review dispatcher. Auto-detects review type from argument or presents selection menu. Routes to code review, PR review, or scope review.
argument-hint: "[target]"
allowed-tools: Bash(git status *), Bash(git log *), Bash(git branch *), Bash(find *), Bash(gh pr list *)
metadata:
  type: generic
---

## Pre-loaded Context

Git status:
!`git status --short 2>/dev/null`

Recent commits:
!`git log --oneline -5 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

Active scopes:
!`find scopes -maxdepth 2 -name scope.md 2>/dev/null`

Open PRs:
!`gh pr list --limit 5 --json number,title,headRefName --jq '.[] | "#\(.number) \(.title) (\(.headRefName))"' 2>/dev/null`

# Review Dispatcher

Routes to the appropriate review skill based on argument type.

---

## Auto-Detect Rules

Apply these rules to `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| Numeric, `#N`, or GitHub PR URL | PR review | Read and follow `operations/pr.md` |
| 7+ hex chars (commit SHA) | Commit review | `Skill(code, review --rev $ARGUMENTS)` |
| `--final <name>` | Final scope review | `Skill(code, review --final $NAME)` |
| Matches `scopes/*/scope.md` or scope name | Scope review | `Skill(scope, review $SCOPE_NAME)` |
| `gestalt` or `--structural` | Structural review | `Skill(gestalt, review $REST)` |
| `--test-audit [path]` or path whose first component is `test` or `tests` | Test quality audit | Read and follow `operations/test-audit.md` with `$TARGET` = path or `tests` |
| File path that exists | Path review | `Skill(code, review --path $ARGUMENTS)` |
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
- Structural: Gestalt-driven structural review — topology, blast radius, targeted questions
- Test quality: Audit tests for oracle mirroring, mock tautologies, framework tests, trivial assertions
```

With "Other" covering: scope review, path review, or custom target.

**Routing by selection:**

| Selection | Action |
|---|---|
| PR | Read and follow `operations/pr.md` — ask for PR # |
| Commit | `Skill(code, review --rev ...)` — ask for SHA first |
| Branch diff | `Skill(code, review --diff <base>..HEAD)` — ask for base branch first |
| Uncommitted | `Skill(code, review)` — auto-detects staged/unstaged |
| Structural | `Skill(gestalt, review)` — ask for base..target range first |
| Other: scope | `Skill(scope, review)` — scope skill asks for name |
| Test quality | Read and follow `operations/test-audit.md` — ask for path (default: `tests`) |

> **Protocol:** [dispatch/protocol.md](../dispatch/protocol.md)

---

## Reviewer Infrastructure

Canonical configuration for multi-agent review. Domain skills compose on this.

> **Reference:** See [reference/models.md](reference/models.md) for models,
> [reference/harnesses.md](reference/harnesses.md) for dispatch templates,
> [reference/report.md](reference/report.md) for YAML schemas,
> [reference/synthesis.md](reference/synthesis.md) for merge algorithm.

### Models

| Harness | Models |
|---|---|
| Claude | opus, sonnet |
| Pi | openai-codex/gpt-5.4, google-gemini-cli/gemini-3-flash-preview, google-gemini-cli/gemini-3.1-pro-preview |

Full details: [reference/models.md](reference/models.md)

### Harnesses

| Harness | Type | Dispatch |
|---|---|---|
| Claude | Native subagent | `Task(subagent_type="general")` |
| Pi | External subprocess | `pi -p --model --thinking` |

Full details: [reference/harnesses.md](reference/harnesses.md)

### Dispatch Pattern

Cartesian product: roles × harnesses, all in single message.
Domain skill defines roles. This skill defines harnesses.

### Reviewer Selection (Interactive)

**Question 1:** Select reviewers (multiSelect):
- claude-opus (Recommended), claude-sonnet, openai-gpt5.4 (Recommended), gemini-3-flash, gemini-3.1-pro (Recommended)

**Default:** claude-opus, openai-gpt5.4, gemini-3.1-pro

**Question 2:** Provider (if Pi selected): native (Recommended) or github-copilot

**Question 3:** Thinking level (if Pi selected): low, medium, high (Recommended), xhigh

**Model mapping:**
- `claude-opus` → `{type: claude, model: opus}`
- `claude-sonnet` → `{type: claude, model: sonnet}`
- `openai-gpt5.4` → `{type: pi, model: openai-codex/gpt-5.4}`
- `gemini-3-flash` → `{type: pi, model: google-gemini-cli/gemini-3-flash-preview}`
- `gemini-3.1-pro` → `{type: pi, model: google-gemini-cli/gemini-3.1-pro-preview}`

Store selections in `validation.yaml` under `review_config`.

### Report Schema

Base YAML structures for reviewer and synthesized reports.
Full details: [reference/report.md](reference/report.md)

### Synthesis

Merge, dedup, gate aggregation, severity aggregation.
Full details: [reference/synthesis.md](reference/synthesis.md)
