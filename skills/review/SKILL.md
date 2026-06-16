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
!`find scopes -maxdepth 3 -name scope.md 2>/dev/null`

Open PRs:
!`gh pr list --limit 5 --json number,title,headRefName --jq '.[] | "#\(.number) \(.title) (\(.headRefName))"' 2>/dev/null`

# Review Dispatcher

Routes to the appropriate review skill based on argument type.

---

## Auto-Detect Rules

**Pre-parse:** Extract `--reviewers <aliases>` from `$ARGUMENTS` before pattern matching. Value is a comma-separated list from `{opus, sonnet, gpt, gemini}`. Resolve to models per the Reviewer Selection section. Unknown alias → ask user to pick from the table. Flag is inherited by all downstream routes (Skill/code, Skill/scope, Skill/gestalt).

Apply these rules to remaining `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| Numeric, `#N`, or GitHub PR URL | PR review | Read and follow `operations/pr.md` |
| 7+ hex chars (commit SHA) | Commit review | `Skill(code, review --rev $ARGUMENTS)` |
| `--final <name>` | Final scope review | `Skill(code, review --final $NAME)` |
| Matches `scopes/*/*/scope.md` or scope name | Scope review | `Skill(scope, review $SCOPE_NAME)` |
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

### Models & Harnesses

- **Claude** (native subagent): `opus`, `sonnet` — dispatched by the agent via `Task`.
- **External** (codex, gemini): defined and dispatched by the **[peer skill](../peer/SKILL.md)**
  — run `peer list` for the canonical registry (id ↔ harness ↔ model ↔ alias). Don't
  restate model strings here.

Full details: [reference/models.md](reference/models.md), [reference/harnesses.md](reference/harnesses.md), [peer skill](../peer/SKILL.md)

### Dispatch Pattern

Per role, in a single message: one Claude `Task` + one `peer run` that fans the role
prompt out to all configured external reviewers. **Never shell out to codex/gemini
directly** — `peer` owns external dispatch. Domain skill defines roles; see
[reference/harnesses.md](reference/harnesses.md) and the [peer skill](../peer/SKILL.md).

### Reviewer Selection

Reviewers can be specified three ways, resolved in this order:

1. **`--reviewers` flag** (non-interactive) — comma-separated aliases
2. **`validation.yaml` `review_config`** — persisted per-scope selection
3. **AskUserQuestion** — interactive fallback when neither is present

#### `--reviewers` Flag

Accepts a comma-separated list of short aliases:

| Alias | Harness | Reviewer-id |
|---|---|---|
| `opus` | claude | claude-opus |
| `sonnet` | claude | claude-sonnet |
| `gpt` | codex | codex-gpt5.5 |
| `gemini` | gemini | gemini-3.5-flash |

(Model per reviewer-id: `peer list`.)

**Examples:**
- `/review --reviewers opus,gpt` → claude-opus + codex-gpt5.5
- `/review --reviewers opus,gpt,gemini` → claude-opus + codex-gpt5.5 + gemini-3.5-flash
- `/implement execute --reviewers opus,gpt` → same two reviewers used for Phase A.5 + Phase C

**Invalid alias:** Report unknown alias and ask user to pick from the table.

#### Interactive Fallback (no flag, no review_config)

**Question 1:** Select reviewers (multiSelect):
- claude-opus (Recommended), claude-sonnet, codex-gpt5.5 (Recommended), gemini-3.5-flash (Recommended)

**Default:** claude-opus, codex-gpt5.5, gemini-3.5-flash

**Question 2:** Reasoning effort (if Codex selected): low, medium, high (Recommended)

#### Full Model Mapping

Reviewer-id ↔ harness ↔ model is the **[peer skill](../peer/SKILL.md)** registry (`peer list`).
`claude-opus`/`claude-sonnet` map to the Claude `Task` harness; `codex-gpt5.5`/
`gemini-3.5-flash` to the external harnesses peer dispatches.

Store resolved selections in `validation.yaml` under `review_config` (whether from flag, prior config, or interactive prompt).

### Report Schema

Base YAML structures for reviewer and synthesized reports.
Full details: [reference/report.md](reference/report.md)

### Synthesis

Merge, dedup, gate aggregation, severity aggregation.
Full details: [reference/synthesis.md](reference/synthesis.md)
