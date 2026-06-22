---
name: scope
description: Unified scope lifecycle. Auto-detects operation from argument or presents selection menu. Routes to create, review, update, done, or list.
argument-hint: "[operation|name] [scope-name]"
allowed-tools: Bash(find *), Bash(git branch *), Bash(git log *), Bash(git status *), Bash(git diff *)
metadata:
  type: domain
---

## Pre-loaded Context

Active scopes:
!`find scopes -maxdepth 3 -name scope.md 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

# Scope Dispatcher

Routes to the appropriate operation based on argument or context.

> **Protocol:** [dispatch/protocol.md](../dispatch/protocol.md)
> **Reference:** See [reference/review.md](reference/review.md) for review workflow, [reference/update.md](reference/update.md) for update workflow, [reference/operations.md](reference/operations.md) for done/list, [reference/issue.md](reference/issue.md) for publishing a scope as a GitHub issue tree.

---

## Auto-Detect Rules

Parse `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| `review [name]` | Review | Multi-agent review, produce review.yaml |
| `issue [name]` | Issue | Publish the scope as a GitHub issue tree via the `issue` skill — see [reference/issue.md](reference/issue.md) |
| `update [name]` | Update | Sync tasks.yaml status from git history |
| `done [name]` | Complete | Set status to `done` |
| `list` | List | Show all scopes with status |
| `<name>` matching existing scope (search `scopes/{draft,active,done}/<name>`) | Resume | Show scope, offer operations; promote `draft`→`active` if work has started |
| `<name>` not matching existing | Create | Create new scope under `scopes/draft/<name>/` |
| No argument, branch-associated scope exists | Resume | Show it; promote `draft`→`active` if work has started |
| No argument, no scope | Create | Ask what to scope |

---

## Menu Fallback

When no argument or unrecognized keyword, use **AskUserQuestion**:

```
Header: Scope
Question: What would you like to do?
multiSelect: false
Options:
- Create: Define a new scope with requirements and tasks
- Review: Multi-agent scope review with parallel reviewers
- Issue: Publish the scope as a GitHub issue tree
- Update: Sync task status from git history
- List: Show all scopes with status
```

| Selection | Action |
|---|---|
| Create | Run creation workflow below |
| Review | See [reference/review.md](reference/review.md) |
| Issue | See [reference/issue.md](reference/issue.md) |
| Update | See [reference/update.md](reference/update.md) |
| List | See [reference/operations.md](reference/operations.md) |

---

# Resume Workflow

When resuming a scope:

1. **Locate scope:** Search across lifecycle dirs — `scopes/{draft,active,done}/<name>/`. A scope name is unique across states.
2. Read `scope.md` frontmatter and `tasks.yaml`
3. **Promote `draft` → `active`** if any of the following are true:
   - Any task has `status: in_progress` or `status: done`
   - Git log shows commits referencing this scope since creation
   - User selects "implement" or "continue" from the operations menu

   Promotion has two steps — both must run together:
   - Update `status: active` in `scope.md` frontmatter
   - `git mv scopes/draft/<name> scopes/active/<name>` (or `mv` if the scope is untracked)
4. Show scope summary and offer operations

---

# Creation Workflow

Creates structured tracking documents for complex development tasks.

**DO use for:** Complex multi-step tasks (3+ phases), non-trivial features, after ExitPlanMode.
**DON'T use for:** Single-file changes, trivial refactorings, tasks completable in < 30 minutes.

> **Reference:**
> - [reference/issue-types.md](reference/issue-types.md) — Initiative/Feature/Task/Exploratory definitions, taxonomy allocation, SDD integration
> - [reference/question-taxonomy.md](reference/question-taxonomy.md) — Question templates per taxonomy area with options
> - [reference/sdd-gates.md](reference/sdd-gates.md) — Pre-implementation gates for Initiatives (Simplicity, Anti-Abstraction, Integration-First)

---

## Validation Depth (Dispatch Gate)

Ask this once, up front — before the numbered steps. It gates the guided decision questions:

```
Header: Depth
Question: How thorough should requirement validation be?
multiSelect: false
Options:
- Guided: Add decision questions — approach selection, strategy & story prioritization, design-alternatives probing (Recommended for Features/Initiatives)
- Standard: Taxonomy clarification loop only — skip the guided decision questions
```

Set `guided = true` when **Guided** is selected. Steps marked **[guided]** below run only when `guided = true`; otherwise skip them silently. Guided steps carry additional gates (issue type / opt-in) as noted on each.

---

## Steps

### Step 0: Native Plan Context

Before research, check for existing context from Claude's native `/plan`:

1. **Check for context:** If `/plan` was used earlier in the session, or the user references a plan, pull those findings in.
2. **If present:** Extract and seed taxonomy areas:
   - Goal/objective → **Scope**
   - Approach/strategy → **Integration** / **Architecture**
   - Open questions → priority clarification targets in Step 3
3. **If absent:** Proceed to Step 1.

This step bridges native planning with structured validation so the user isn't asked to re-state what `/plan` already established.

### Step 1: Research

Run `gestalt map`, read key files, understand current state. Research comes FIRST — before asking questions.

### Step 2: Issue Type Selection

**FIRST QUESTION (Always)** — Use AskUserQuestion:

```
Header: Work type
Question: What type of work is this?
multiSelect: false
Options:
- Initiative: Strategic coordination (months) - Multiple features toward business goal
- Feature: User-facing capability (weeks) - Deliverable value, multiple tasks
- Task: Implementation item (days) - Single concrete deliverable
- Exploratory: Not sure yet - Gather context first, then classify
```

This determines:
- **Question limit:** Tasks get 3, Features/Initiatives get 5
- **Taxonomy areas:** Tasks get minimal (3), Features/Initiatives get full (7)

**If Exploratory:** Gather context, ask 3 questions, present classification recommendation, restart with correct type.

### Step 3: Validation (Human-in-the-Loop)

Present findings and ask focused questions. Every question must:

- **Provide context:** What was found, what is thought, what is uncertain
- **Make tradeoffs explicit:** "We could do A (faster) or B (cleaner). A fits because X, but B if Y."
- **Never ask without context:** Always "Based on [findings], I recommend [X] over [Y] because [Z]. Does this match your intent?"

**Ambiguity scan:** For each taxonomy area (based on issue type), evaluate status and record in `validation.yaml` under `ambiguity_scan`:

- **clear** — Fully specified, no questions needed
- **partial** — Some information present, gaps remain
- **missing** — Not addressed at all

Per-area evaluation criteria:

| Area | Clear | Partial | Missing |
|------|-------|---------|---------|
| Scope | Goals, boundaries, success criteria defined | Some elements unclear | No scope information |
| Behavior | User flows, system responses specified | Some paths undefined | No behavior described |
| Data Model | Entities, relationships, formats clear | Schema gaps exist | No data model |
| Constraints | Performance, security, compatibility stated | Some constraints unclear | No constraints |
| Edge Cases | Error handling, limits documented | Some cases unaddressed | No edge cases |
| Integration | Dependencies, APIs, interfaces identified | Some touchpoints unclear | No integration info |
| Terminology | Domain terms defined consistently | Some ambiguous terms | No definitions |

Routing:
- **All clear:** Skip the validation loop, proceed silently to Step 3.5.
- **Gaps found:** Areas with `partial` or `missing` status become priority candidates, ordered by (Impact × Uncertainty).

**Constitution check (Initiatives only):** Read `.claude/constitution.md`; flag conflicts and ask user to resolve or document exception. Skip for Features/Tasks.

**Validation loop:** Ask clarifying questions in taxonomy-based batches (see [reference/question-taxonomy.md](reference/question-taxonomy.md) for templates per area):
1. Identify uncovered areas
2. Prioritize by (Impact x Uncertainty)
3. Group questions by taxonomy area
4. Use AskUserQuestion with options
5. Re-evaluate remaining questions for relevance
6. Repeat until limit reached or primary areas covered

**Batch format:**
```
Header: [Area, max 12 chars]
Question: [Clear question ending with ?]
multiSelect: false
Options:
- Option A: [choice] - [implication]
- Option B: [choice] - [implication]
- None: [default/skip]
```

**Taxonomy areas:**

| Type | Areas to Cover |
|------|----------------|
| Initiative | Scope, Behavior, Data Model, Constraints, Edge Cases, Integration, Terminology |
| Feature | Scope, Behavior, Data Model, Constraints, Edge Cases, Integration, Terminology |
| Task | Scope, Behavior, Integration |

### Step 3.4: Propose Approaches [guided]

After the validation loop, present concrete options — never proceed on an unstated default:

```
Header: Approach
Question: Which approach should we take?
multiSelect: false
Options:
- Approach A: [brief] - Trade-off: [X]
- Approach B: [brief] - Trade-off: [Y]
- Approach C: [brief] - Trade-off: [Z]
```

Lead with your recommendation (mark it). Apply YAGNI ruthlessly — drop options that add cost without clear value. Record the selected approach in `validation.yaml`; seeds the Implementation Strategy / Approach in scope.md.

### Step 3.45: Initiative Strategy & Story Prioritization [guided, Initiatives only]

For Initiatives, probe prioritization and rollout:

```
Header: User Stories
Question: How should user stories be prioritized?
multiSelect: false
Options:
- MVP First: P1 delivers standalone value, P2/P3 incremental (Recommended)
- Parallel Tracks: Stories developed independently by different teams
- Sequential: Strict dependencies, complete in order
```

```
Header: Strategy
Question: What implementation approach fits best?
multiSelect: false
Options:
- MVP First: Ship P1, iterate on P2/P3 from feedback (Recommended)
- Incremental: Each phase adds value, all planned upfront
- Parallel Team: Multiple workstreams, integration points defined
```

Record selections in `validation.yaml`; they populate the User Stories and Implementation Strategy sections of scope.md.

### Step 3.5: SDD Section Opt-ins (Features/Initiatives)

```
Header: Sections
Question: Which detailed sections do you want?
multiSelect: true
Options:
- Tech Decisions: Document technology choices and rationale
- API Contract: Define API endpoints and schemas
- Data Model: Document entities and relationships
- Design: Design document with alternatives, invariants, complexity analysis
- None: Keep scope lightweight
```

### Step 3.55: Design Probing [guided, when Design opt-in selected]

If **Design** was selected in Step 3.5, probe for alternatives context:

```
Header: Alternatives
Question: Were other approaches considered before this one?
multiSelect: false
Options:
- Yes, describe: I can list rejected alternatives and why
- Partially: Some were considered informally
- No: This is the first approach explored
- Skip: I'll fill in design.md directly
```

Record the response in `validation.yaml`; seeds the Alternatives section of `design.md`.

### Step 3.6: Detect and Extract Code Artifacts

**If input contains code blocks:** Extract, stage, ask user which resources to create via multiSelect (implementation, schemas, config, patterns, assets, none). Create selected in `scopes/draft/<name>/resources/`.

### Step 3.7: Configure Implementation Reviewers

Configure reviewers per `/review` infrastructure (see `/review` SKILL.md "Reviewer Selection"). Resolution order:
1. `--reviewers` flag passed to `/scope` — comma-separated aliases from `{opus, sonnet, gpt, gemini}`
2. Interactive AskUserQuestion prompt (fallback)

Store resolved selections in `validation.yaml` under `review_config`.

**All issue types** (Initiative, Feature, Task) require reviewer config — Task scopes also run batch reviews and need Codex harnesses configured.

### Step 4: Create Directory and Documents

New scopes are created under the `draft` lifecycle directory. They are moved to `active` on first work (see Resume Workflow / `update`) and to `done` via `/scope done`.

```bash
mkdir -p ./scopes/draft/[scope-name]/
```

**Lifecycle layout:**

```
scopes/
├── draft/<name>/   # newly created, no work started
├── active/<name>/  # promoted on first task progress or commit
└── done/<name>/    # marked complete via /scope done
```

A scope name is unique across lifecycle states — it lives in exactly one of `draft/`, `active/`, or `done/` at a time.

Generate these files:

1. **`scope.md`** — Goal, context, requirements, verification
2. **`design.md`** — Design reasoning (optional, when Design opt-in selected)
3. **`tasks.yaml`** — Work checklist (TodoWrite sync)
4. **`dependencies.yaml`** — Task dependency graph (parallel dispatch)
5. **`validation.yaml`** — Audit trail and gate checks

**Document scaling by issue type:**

| Document | Initiative | Feature | Task |
|----------|-----------|---------|------|
| scope.md | Full | Standard | Lightweight |
| design.md | Opt-in (complex) | Opt-in | Skip |
| tasks.yaml | Feature breakdown + phases | Task breakdown | Single task |
| dependencies.yaml | Full DAG | Phase-based | Skip |
| validation.yaml | Full (7 areas + gates) | Full (7 areas) | Skip |

**Task output = 2 files:** scope.md (lightweight) + tasks.yaml

**Batch signal lives in `tasks.yaml`.** Each task's `depends_on` + `files` fields are the
source of truth for parallel dispatch, so Task scopes parallelize from `tasks.yaml` alone — no
`dependencies.yaml` required. `dependencies.yaml` is the Feature/Initiative precomputed DAG
(a fast-path); when present, executors use its `batches[*]` directly, otherwise they derive
batches from `tasks.yaml`.

**scope.md frontmatter:**

```yaml
---
created: [Date]
status: draft
issue_type: [Initiative|Feature|Task]
---
```

**Conditional sections in scope.md:**

| Section | Initiative | Feature | Task |
|---------|------------|---------|------|
| User Stories (P1/P2/P3) | Include | Skip | Skip |
| Given/When/Then Acceptance | Full | Standard | Simple |
| API Contract | If API work | Opt-in | Skip |
| Implementation Strategy | Include | Skip | Skip |
| Tech Decisions | Include | Opt-in | Skip |
| Data Model | Include | Opt-in | Skip |

**design.md trigger:** Created when Design opt-in selected. All sections optional — include only what adds value.

> **Reference:** See [reference/quality-model.md](reference/quality-model.md) for design document quality patterns.

### Step 5: Populate TodoWrite from tasks.yaml

Parse `tasks.yaml`, create TodoWrite with up to 10 tasks (status, content, activeForm mapped from tasks.yaml).

### Step 6: Present Summary

Show: directory created, scope.md overview, design.md (if created), tooling artifacts, validation coverage, next action.

### Step 7: Gate

Present scope, ask "ready to implement or revise?"

### Step 8: Offer Review (Optional)

```
Header: Review
Question: Would you like a comprehensive scope review before implementation?
multiSelect: false
Options:
- Yes: Run multi-agent review (Claude + external reviewers via peer)
- Later: Skip for now, use /scope review when ready
- Skip: Proceed without review
```

If "Yes": Run review sub-operation with the just-created scope name.

---

## Output Artifacts

**For humans (review these):**
```
scopes/<state>/<name>/   # <state> ∈ {draft, active, done}
├── scope.md     # WHY & WHAT & CONTEXT - Goal, requirements, key files, decisions
├── design.md    # WHY THIS WAY - Alternatives, invariants, complexity (opt-in)
└── resources/   # HOW TO BUILD - Implementation details (when provided)
```

**For tooling (infrastructure):**
```
scopes/<state>/<name>/
├── tasks.yaml        # Progress tracking, TodoWrite sync
├── dependencies.yaml # Parallel dispatch DAG
└── validation.yaml   # Audit trail, gate checks, reviewer config, loqui validation
```

---

## Templates

Located in `templates/` directory:
- [scope.md](templates/scope.md)
- [design.md](templates/design.md)
- [tasks.yaml](templates/tasks.yaml)
- [dependencies.yaml](templates/dependencies.yaml)
- [validation.yaml](templates/validation.yaml)

---

## Integration

**Command:** `/scope [operation] [name]`

**Related skills:**
- `clarify` — Resolve ambiguities in scope context
- `implement` — Execute tasks from scope
- `continue` — Resume from checkpoint
- `review` — Routes to `/scope review` for scope targets
