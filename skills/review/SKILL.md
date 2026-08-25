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
!`git status --short 2>/dev/null || true`

Recent commits:
!`git log --oneline -5 2>/dev/null || true`

Current branch:
!`git branch --show-current 2>/dev/null || true`

Active scopes:
!`find scopes -maxdepth 3 -name scope.md 2>/dev/null || true`

Open PRs:
!`gh pr list --limit 5 --json number,title,headRefName --jq '.[] | "#\(.number) \(.title) (\(.headRefName))"' 2>/dev/null || true`

# Review Dispatcher

Routes to the appropriate review skill based on argument type.

---

## Auto-Detect Rules

**Pre-parse:** Extract `--reviewers <aliases>` from `$ARGUMENTS` before pattern matching. The value
is a comma-separated list of live aliases from `peer list`, including native aliases. Resolve to
models per the Reviewer Selection section. Unknown alias → show the live table and ask the user to
pick a valid alias. The flag is inherited by all downstream routes (Skill/code, Skill/scope,
Skill/gestalt).

Apply these rules to remaining `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| Numeric, `#N`, or GitHub PR URL | PR review | Read and follow `operations/pr.md` |
| 7+ hex chars (commit SHA) | Commit review | `Skill(code, review --rev $ARGUMENTS)` |
| `--final <name>` | Standalone final scope review | `Skill(code, review --final $NAME)` |
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
- Test quality: Audit tests for oracle mirroring, mock tautologies, framework tests, trivial assertions, defective oracles
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
> [reference/finding-bar.md](reference/finding-bar.md) for the admission bar every role prompt carries,
> [reference/report.md](reference/report.md) for YAML schemas,
> [reference/synthesis.md](reference/synthesis.md) for merge algorithm.

### Models & Harnesses

- Codex native subagent: `codex-native` — dispatched through Codex delegation with inherited
  session model/reasoning; never through peer.
- Claude native subagent: `opus`, `sonnet` — dispatched via Claude-host Task.
- External peers (for example Codex and Pi): defined and dispatched by the generic
  **[peer skill](../peer/SKILL.md)** — run `peer list` for the canonical registry
  (id ↔ harness ↔ model ↔ alias), including `opus-peer`/`sonnet-peer` when registered.

Full details: [reference/models.md](reference/models.md), [reference/harnesses.md](reference/harnesses.md), [peer skill](../peer/SKILL.md)

### Dispatch Pattern

Per role, in a single message: Codex delegation for `codex-native`, Claude Tasks for
`opus`/`sonnet`, plus one `peer --agent reviewer` only when external aliases are configured.
**Never send a host-native token through peer or invoke an external harness directly.** Domain skill defines roles; see
[reference/harnesses.md](reference/harnesses.md) and the [peer skill](../peer/SKILL.md).

Materialize the reviewed content, requirements/context, exact report schema, and the verbatim
[finding bar](reference/finding-bar.md) into the shared prompt before dispatch. Git commands and workdirs are supplemental; a shell-less read-only peer
must never receive only a command to run.

### Report Output Directory

Every review — standalone or implementation-owned — writes into `.peer/`, under the canonical
[report layout](../peer/SKILL.md#report-layout--peer). Never assemble the path by hand; `peer path`
constructs it, creates it, and keeps `.peer/` gitignored.

For a standalone `/review` run the route determines `<subject>` and the stage is `review`, or
`review-<role>` when several roles fan out in one run:

| Route | `<subject>` | `{outdir}` |
|---|---|---|
| PR | `pr-<number>` | `$(peer path pr-<number> review)` |
| Commit | `commit-<sha7>` | `$(peer path commit-<sha7> review)` |
| Branch diff | `diff-<base>..<target>` (sanitised) | `$(peer path diff-<base>..<target> review)` |
| Uncommitted | `working` | `$(peer path working review)` |
| Path | `path-<basename>` | `$(peer path path-<basename> review)` |
| Scope | `scope-<name>` | `$(peer path scope-<name> review)` |

Each run mints a fresh `<run>`, so re-reviewing the same subject never overwrites the previous
round's evidence. `peer --agent reviewer --peers <aliases>` writes `{outdir}/{reviewer-id}.yaml`
per external reviewer beside the materialized `{outdir}/prompt.md`.

Implementation-owned Phase A.5, Phase C, and final reviews are not standalone `/review` runs:
they reload the scope's `config.yaml` and use the scope name as `<subject>` with one `<run>`
shared across the round.

### Reviewer Selection

Reviewers can be specified three ways, resolved in this order:

1. **`--reviewers` flag** (non-interactive) — comma-separated aliases
2. **`validation.yaml` `review_config`** — persisted per-scope selection
3. **AskUserQuestion** — interactive fallback when neither is present

#### `--reviewers` Flag

Accepts a comma-separated list of short aliases. The alias ↔ harness ↔ reviewer-id ↔
model mapping is injected live from the peer registry (single source of truth, cannot drift):

```!
peer list
```

**Examples (Claude host):**
- `/review --reviewers opus,gpt` → claude-opus + !`peer get id gpt`
- `/review --reviewers opus,gpt,gemini` → claude-opus + !`peer get id gpt` + !`peer get id gemini`

**Invalid alias:** Report unknown alias and ask user to pick from the table.

**Host-incompatible alias:** Reject known same-host-family loopback too. On Codex, direct every
registry Codex-family alias to `codex-native`; on Claude, direct every registry Claude-family peer
alias to native `opus`/`sonnet`. Ask for an explicit corrected selection and never rewrite it.

#### Interactive Fallback (no flag, no review_config)

**Question 1:** Select reviewers (multiSelect) from the live `peer list` table:
- Codex host: label `codex-native` as native and `opus-peer`/`sonnet-peer` as via peer; reject
  host-native `opus`/`sonnet` and every registry Codex-family peer alias (`gpt`, `terra`, `luna`,
  etc.) in favor of `codex-native`
- Claude host: label `opus`/`sonnet` as native and GPT/Codex aliases as via peer; reject
  `codex-native` and every registry Claude-family peer alias (including `opus-peer`/`sonnet-peer`)
  in favor of native Claude Tasks
- Include other external aliases from the live table according to their capabilities

**Default:** Codex host → `codex-native`; Claude host → `opus+gpt+gemini`; otherwise require an
explicit available selection.

**Question 2:** `inherit` for any all-native selection; a peer-supported explicit effort when any
external alias is selected. In mixed sets the effort applies only to peer entries.

#### Full Model Mapping

Reviewer-id ↔ harness ↔ model is the **[peer skill](../peer/SKILL.md)** registry (`peer list`).
Entries with `RUN-BY-PEER=no` map to their host-native mechanism (`codex-native` delegation or
Claude Task); entries with `RUN-BY-PEER=yes` are passed by alias to
`peer --agent reviewer --peers`. If the required host-native mechanism is unavailable, stop and
ask for a new selection rather than substituting.

This host matrix is strict for persisted selections: never silently convert `opus` to `opus-peer`
or `codex-native` to `gpt` when resuming on a different host. Classify peer aliases dynamically
from registry harness/family metadata so new same-family aliases are rejected automatically.

For scope-review routes, store resolved selections in `validation.yaml` under `review_config`
(whether from flag, prior config, or interactive prompt). This remains review-specific metadata;
`/implement`, `/continue`, and `/loop` use the scope's live `config.yaml` instead.

Likewise, standalone `/review --final <scope>` follows this review-specific selection flow. The
implementation pipeline must dispatch its final roles directly with `config.yaml`'s reviewer
aliases and effort (or an explicit non-interactive handoff carrying both); it must not call the
standalone route and accidentally reselect reviewers.

### Report Schema

Full details: [reference/report.md](reference/report.md)

### Synthesis

Full details: [reference/synthesis.md](reference/synthesis.md)

### Landing the Outcome

The confirmed `issues:` of a synthesized report land through the [`tfcp` skill](../tfcp/SKILL.md) —
triage, fix, commit, push in one pass, `--report` pointing at the run's report directory. Synthesis
already dispositioned those findings (step 4.5), so `tfcp`'s triage carries the verdicts through
rather than re-opening them. On a PR,
[`tfcprr`](../tfcprr/SKILL.md) extends that chain with the per-thread reply and resolve.
