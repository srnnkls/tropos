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
!`find scopes -maxdepth 2 -name scope.md 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

# Scope Dispatcher

Routes to the appropriate operation based on argument or context.

> **Protocol:** [dispatch/protocol.md](../dispatch/protocol.md)
> **Reference:** See [reference/review.md](reference/review.md) for review workflow, [reference/update.md](reference/update.md) for update workflow, [reference/operations.md](reference/operations.md) for done/list.

---

## Auto-Detect Rules

Parse `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| `review [name]` | Review | Multi-agent review, produce review.yaml |
| `update [name]` | Update | Sync tasks.yaml status from git history |
| `done [name]` | Complete | Set status to done |
| `list` | List | Show all scopes with status |
| `<name>` matching existing scope | Resume | Show scope, offer operations |
| `<name>` not matching existing | Create | Create new scope |
| No argument, branch-associated scope exists | Resume | Show it |
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
- Update: Sync task status from git history
- List: Show all scopes with status
```

| Selection | Action |
|---|---|
| Create | Run creation workflow below |
| Review | See [reference/review.md](reference/review.md) |
| Update | See [reference/update.md](reference/update.md) |
| List | See [reference/operations.md](reference/operations.md) |

---

# Creation Workflow

Creates structured tracking documents for complex development tasks.

**DO use for:** Complex multi-step tasks (3+ phases), non-trivial features, after ExitPlanMode.
**DON'T use for:** Single-file changes, trivial refactorings, tasks completable in < 30 minutes.

---

## Steps

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

**Ambiguity scan:** For each taxonomy area, evaluate status (clear/partial/missing). If all clear, skip validation loop.

**Validation loop:** Ask clarifying questions in taxonomy-based batches:
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

### Step 3.6: Detect and Extract Code Artifacts

**If input contains code blocks:** Extract, stage, ask user which resources to create via multiSelect (implementation, schemas, config, patterns, assets, none). Create selected in `scopes/<name>/resources/`.

### Step 3.7: Configure Implementation Reviewers

**Only for Initiative/Feature** (skip for Task).

Configure reviewers per `/review` infrastructure. Use the reviewer selection prompts from `/review` SKILL.md "Reviewer Selection (Interactive)". Store selections in `validation.yaml` under `review_config`.

### Step 4: Create Directory and Documents

```bash
mkdir -p ./scopes/[scope-name]/
```

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
- Yes: Run multi-agent review (Claude + OpenCode)
- Later: Skip for now, use /scope review when ready
- Skip: Proceed without review
```

If "Yes": Run review sub-operation with the just-created scope name.

---

## Output Artifacts

**For humans (review these):**
```
scopes/<name>/
├── scope.md     # WHY & WHAT & CONTEXT - Goal, requirements, key files, decisions
├── design.md    # WHY THIS WAY - Alternatives, invariants, complexity (opt-in)
└── resources/   # HOW TO BUILD - Implementation details (when provided)
```

**For tooling (infrastructure):**
```
scopes/<name>/
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
