---
name: scope
description: Unified scope lifecycle. Auto-detects operation from argument or presents selection menu. Routes to create, review, update, done, or list. Creation clears a mandatory multi-agent review gate before the scope is implementable.
metadata:
  type: domain
henia:
  slots:
    scope.templates:
  provides:
    scope.templates: {section: templates}
  targets:
    claude:
      frontmatter:
        argument-hint: '[operation|name] [scope-name]'
        allowed-tools: Bash(find *), Bash(git branch *), Bash(git log *), Bash(git status *), Bash(git diff *), Bash(git worktree list *), Bash(peer *)
    codex:
      openai:
        interface:
          display_name: Scope
          short_description: Apply the canonical scope skill workflow
          default_prompt: Use $scope for the requested task.
  variables:
    context_commands:
      - label: Active scopes
        command: find "$(git worktree list --porcelain | awk 'NR==1{print $2}')/scopes" -maxdepth 3 -name scope.md 2>/dev/null || true
      - label: Current branch
        command: git branch --show-current 2>/dev/null || true
      - label: Available peers
        command: peer list 2>/dev/null || true
      - label: Default reviewers
        command: peer defaults reviewers 2>/dev/null || true
---

::::head{context slots="scope.templates"}


# Scope Dispatcher

Operations: [review](reference/review.md), [update](reference/update.md), [done/list](reference/operations.md), [issue tree](reference/issue.md).

## Slots

| Slot | Covers |
|---|---|
| `scope.templates` | Scope document templates; replaces the files under [Templates](#templates) it covers |

## Scope Location

Scopes live only in the main worktree at `<repo-root>/scopes/<state>/<name>/`, `<state>` ∈ {draft, active, done}, each name in one state. Linked worktrees never hold a copy of `scopes/` or the skill files. Resolve the root before touching any scope file:

```bash
root=$(git worktree list --porcelain | awk 'NR==1{print $2}')
```

To reach `./scopes/` from a worktree, add `scopes/  symlink` to `.worktreeinclude` at the repo root and run `git worktreeinclude apply` in the worktree ([worktree](../git/reference/worktree.md)). Never copy.

Locate `<name>` by searching `scopes/{draft,active,done}/<name>/`; without a name, take the most recent `scopes/*/*/scope.md`.

Promote `draft` → `active` by setting `status: active` in `scope.md` frontmatter and running `git mv scopes/draft/<name> scopes/active/<name>` (`mv` if untracked), always together.

:::routes{ordered protocol}
| Pattern | Route | Action |
|---|---|---|
| `review [name]` | Review | Multi-agent review; record the result in `validation.yaml.review_gate` |
| `issue [name]` | Issue | Publish the scope as a GitHub issue tree via the `issue` skill — see [reference/issue.md](reference/issue.md) |
| `update [name]` | Update | Sync tasks.yaml status from git history |
| `done [name]` | Complete | Set status to `done` |
| `list` | List | Show all scopes with status |
| `<name>` matching existing scope (search `scopes/{draft,active,done}/<name>`) | Resume | Show scope, offer operations; promote `draft`→`active` if work has started |
| `<name>` not matching existing | Create | Create new scope under `scopes/draft/<name>/` |
| No argument, branch-associated scope exists | Resume | Show it; promote `draft`→`active` if work has started |
| No argument, no scope | Create | Ask what to scope |
:::

## Menu Fallback

With no argument or an unrecognized keyword, ask via AskUserQuestion and run the selected route:

:::user-question{header="Scope" question="What would you like to do?"}
- Create: Define a new scope with requirements and tasks
- Review: Multi-agent scope review with parallel reviewers
- Issue: Publish the scope as a GitHub issue tree
- Update: Sync task status from git history
- List: Show all scopes with status
:::

# Resume Workflow

1. Locate the scope; read `scope.md` frontmatter and `tasks.yaml`.
2. Promote it if any task is `in_progress` or `done`, git log shows commits referencing the scope since creation, or the user selects "implement" or "continue".
3. Show a scope summary and offer operations.

::::

# Creation Workflow

Use for tasks with 3+ phases, non-trivial features, or after ExitPlanMode; not for single-file changes, trivial refactorings, or work under 30 minutes.

## Validation Depth (Dispatch Gate)

Ask once, before Step 0:

:::user-question{header="Depth" question="How thorough should requirement validation be?"}
- Guided: Add decision questions — approach selection, strategy & story prioritization, design-alternatives probing (Recommended for Features/Initiatives)
- Standard: Taxonomy clarification loop only — skip the guided decision questions
:::

Run [guided] steps only under Guided and when their heading's condition holds; otherwise skip silently.

## Steps

### Step 0: Native Plan Context

If `/plan` ran earlier in the session or the user references a plan, seed from it: goal → Scope; approach → Integration / Architecture; open questions → priority targets in Step 3.

### Step 1: Research

Apply the repository-orientation contract in [AGENTS.md](../../instructions/AGENTS.md#tools-and-context) and read key files before asking questions.

### Step 2: Issue Type Selection

Ask first, always:

:::user-question{header="Work type" question="What type of work is this?"}
- Initiative: Strategic coordination (months) - Multiple features toward business goal
- Feature: User-facing capability (weeks) - Deliverable value, multiple tasks
- Task: Implementation item (days) - Single concrete deliverable
- Exploratory: Not sure yet - Gather context first, then classify
:::

Question limits, taxonomy areas, and the Exploratory path: [issue types](reference/issue-types.md).

### Step 3: Validation (Human-in-the-Loop)

Every question states what was found and what is uncertain, names the tradeoffs, and recommends: "Based on [findings], I recommend [X] over [Y] because [Z]. Does this match your intent?"

Ambiguity scan: rate each of the type's taxonomy areas and record it in `validation.yaml` under `ambiguity_scan`: `clear` (criteria below fully specified), `partial` (some present, gaps remain), or `missing` (not addressed).

| Area | Clear when |
|------|------------|
| Scope | Goals, boundaries, success criteria defined |
| Behavior | User flows, system responses specified |
| Data Model | Entities, relationships, formats clear |
| Constraints | Performance, security, compatibility stated |
| Edge Cases | Error handling, limits documented |
| Integration | Dependencies, APIs, interfaces identified |
| Terminology | Domain terms defined consistently |

All clear: skip to Step 3.5. Otherwise run the validation loop in [question taxonomy](reference/question-taxonomy.md) over the `partial`/`missing` areas, in batches of this form:

:::user-question{header="[Area, max 12 chars]" question="[Clear question ending with ?]"}
- Option A: [choice] - [implication]
- Option B: [choice] - [implication]
- None: [default/skip]
:::

Initiatives only: read `.claude/constitution.md`, flag conflicts, and ask the user to resolve or document an exception; [SDD gates](reference/sdd-gates.md) apply.

### Step 3.4: Propose Approaches [guided]

Never proceed on an unstated default:

:::user-question{header="Approach" question="Which approach should we take?"}
- Approach A: [brief] - Trade-off: [X]
- Approach B: [brief] - Trade-off: [Y]
- Approach C: [brief] - Trade-off: [Z]
:::

Mark your recommendation first. Drop options that add cost without clear value. Record the choice in `validation.yaml`; it seeds Implementation Strategy / Approach in scope.md.

### Step 3.45: Initiative Strategy & Story Prioritization [guided, Initiatives only]

:::user-question{header="User Stories" question="How should user stories be prioritized?"}
- MVP First: P1 delivers standalone value, P2/P3 incremental (Recommended)
- Parallel Tracks: Stories developed independently by different teams
- Sequential: Strict dependencies, complete in order
:::

:::user-question{header="Strategy" question="What implementation approach fits best?"}
- MVP First: Ship P1, iterate on P2/P3 from feedback (Recommended)
- Incremental: Each phase adds value, all planned upfront
- Parallel Team: Multiple workstreams, integration points defined
:::

Record both in `validation.yaml`; they populate User Stories and Implementation Strategy in scope.md.

### Step 3.5: SDD Section Opt-ins (Features/Initiatives)

:::user-question{header="Sections" question="Which detailed sections do you want?" multi}
- Tech Decisions: Document technology choices and rationale
- API Contract: Define API endpoints and schemas
- Data Model: Document entities and relationships
- Design: Design document with alternatives, invariants, complexity analysis
- None: Keep scope lightweight
:::

### Step 3.55: Design Probing [guided, when Design opt-in selected]

:::user-question{header="Alternatives" question="Were other approaches considered before this one?"}
- Yes, describe: I can list rejected alternatives and why
- Partially: Some were considered informally
- No: This is the first approach explored
- Skip: I'll fill in design.md directly
:::

Record the answer in `validation.yaml`; it seeds Alternatives in `design.md`.

### Step 3.6: Detect and Extract Code Artifacts

If the input contains code blocks: extract and stage them, ask via multiSelect which resources to create (implementation, schemas, config, patterns, assets, none), and create them in `scopes/draft/<name>/resources/`.

### Step 3.7: Configure Scope Reviewers

Required for every issue type. Select reviewers per [reviewer selection](../review/SKILL.md#reviewer-selection), with `--reviewers` passed to `$scope`. Persist only the resolved selection and effort in `validation.yaml.review_config`, never routing metadata.

### Step 4: Create Directory and Documents

Create under `draft` (later moves: Resume / `update` → `active`; `done` → `done`).

```bash
mkdir -p "$root/scopes/draft/[scope-name]/"
```

| Document | Content | Initiative | Feature | Task |
|----------|---------|-----------|---------|------|
| scope.md | Goal, context, requirements, key files, decisions, verification | Full | Standard | Lightweight |
| design.md | Alternatives, invariants, complexity, per [quality model](reference/quality-model.md) | Opt-in (complex) | Opt-in | Skip |
| tasks.yaml | Authoritative task status, dependencies, mutation paths | Feature breakdown + phases | Task breakdown | Single task |
| dependencies.yaml | Task dependency DAG for parallel dispatch | Full DAG | Phase-based | Skip |
| validation.yaml | Audit trail, gate checks, reviewer config, code style validation | Full (6 areas + gates) | Full (7 areas) | Skip |
| resources/ | Implementation details (Step 3.6) | When provided | When provided | When provided |

scope.md frontmatter:

```yaml
---
created: [Date]
status: draft
issue_type: [Initiative|Feature|Task]
---
```

Conditional sections in scope.md:

| Section | Initiative | Feature | Task |
|---------|------------|---------|------|
| User Stories (P1/P2/P3) | Include | Skip | Skip |
| Given/When/Then Acceptance | Full | Standard | Simple |
| API Contract | If API work | Opt-in | Skip |
| Implementation Strategy | Include | Skip | Skip |
| Tech Decisions | Include | Opt-in | Skip |
| Data Model | Include | Opt-in | Skip |

### Step 5: Validate Execution Metadata

Before the scope is implementable, every task names explicit `depends_on` and `files` (expected mutation paths); these drive parallel dispatch. Set optional `domain` where the work belongs to one; it keys the approach providers its subagents receive ([implement slots](../implement/SKILL.md#slots)). Resolve missing paths with one bounded discovery wave, else record a scope gap; never force one serial pipeline per task. Executors use `dependencies.yaml` `batches[*]` after validating current task state. TodoWrite may mirror tasks for display; `tasks.yaml` stays authoritative, with no reverse sync.

### Step 6: Present Summary

Show the directory, scope.md overview, design.md (if created), tooling artifacts, validation coverage, and next action.

### Step 7: Gate

Ask "ready to implement or revise?"

### Step 8: Review Gate (Mandatory)

Run [review](reference/review.md) on the scope until `review_gate.status: passed`. Dispatch the reviewers from `validation.yaml.review_config` using the unified host matrix and prompt-file contract. Before each run, revalidate host compatibility and peer effort against the live registry; on incompatibility, stop for explicit config editing. Dispatch and auth contracts: `$review`, `$peer`. Apply the [canonical review result gate](../review/reference/harnesses.md#results).

`implement`/`loop` refuse a scope whose `review_gate.status` is absent or `failed` (`implement/operations/execute.md` Step 2).

## Templates

- [scope.md](templates/scope.md)
- [design.md](templates/design.md)
- [tasks.yaml](templates/tasks.yaml)
- [dependencies.yaml](templates/dependencies.yaml)
- [validation.yaml](templates/validation.yaml)

:::related
- `clarify` — resolve ambiguities in scope context
- `implement` — execute tasks from a scope
- `continue` — resume from a checkpoint
- `review` — routes scope targets to `$scope` with `review`
:::
