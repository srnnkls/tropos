---
name: scope
description: Unified scope lifecycle. Auto-detects operation from argument or presents selection menu. Routes to create, review, update, done, or list.
argument-hint: "[operation|name] [scope-name]"
allowed-tools: Bash(find *), Bash(git branch *), Bash(git log *), Bash(git status *), Bash(git diff *)
---

## Pre-loaded Context

Active scopes:
!`find scopes -name scope.md -maxdepth 2 2>/dev/null | sed 's|/scope.md||' | sed 's|scopes/||'`

Current branch:
!`git branch --show-current 2>/dev/null`

# Scope Dispatcher

Routes to the appropriate operation based on argument or context.

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

**Routing by selection:**

| Selection | Action |
|---|---|
| Create | Run creation workflow below |
| Review | Run review sub-operation below |
| Update | Run update sub-operation below |
| List | Show scopes with status |

---

## Delegation Pattern

1. Parse `$ARGUMENTS` against auto-detect rules (in order)
2. If keyword matches: run the corresponding operation
3. If name matches existing scope: show it, offer operations
4. If no match: present AskUserQuestion menu
5. Execute selected operation

---

# Creation Workflow

Creates structured tracking documents for complex development tasks.

---

## When to Use

**DO use for:**
- Complex multi-step tasks (3+ distinct phases)
- Non-trivial features requiring careful planning
- After ExitPlanMode when user accepts a plan
- Multi-phase implementation work

**DON'T use for:**
- Single-file changes
- Trivial refactorings
- Simple bug fixes
- Tasks completable in < 30 minutes

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
- **Make tradeoffs explicit:** "We could do A (faster, less maintainable) or B (slower, cleaner). A fits better because X, but B would be better if Y."
- **Never ask without context:** No "what approach do you prefer?" — always "Based on [findings], I recommend [X] over [Y] because [Z], accepting [tradeoff]. Does this match your intent?"

**Ambiguity scan:** For each taxonomy area (based on issue type), evaluate status (clear/partial/missing). If all clear, skip validation loop.

**Validation loop:** Ask clarifying questions in taxonomy-based batches:
1. Identify uncovered areas
2. Prioritize by (Impact x Uncertainty)
3. Group questions by taxonomy area
4. Use AskUserQuestion with options
5. Re-evaluate remaining questions for relevance
6. Update taxonomy coverage
7. Repeat until limit reached or primary areas covered

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

**If input contains code blocks** (```python, ```rust, etc.):

1. Extract code blocks with language tags
2. Stage extracted content (held in memory until user chooses)
3. Ask user which resources to create (use AskUserQuestion with multiSelect):
   ```
   Header: Resources
   Question: Which implementation artifacts should be preserved?
   multiSelect: true
   Options:
   - implementation: Code sketches/examples - patterns to follow (loqui-validated)
   - schemas: API contracts, data models, type definitions
   - config: Configuration examples
   - patterns: Integration and test patterns
   - assets: Diagrams, screenshots, other media
   - none: Skip resources, spec only
   ```

4. Create selected resources in `scopes/<name>/resources/`

### Step 3.7: Configure Implementation Reviewers

**Only for Initiative/Feature** (skip for Task):

**Question 1:** Select reviewers:
```
Header: Reviewers
Question: Which reviewers should analyze implementation batches?
multiSelect: true
Options:
- claude-opus: Claude Opus - native reviewer, comprehensive (Recommended)
- claude-sonnet: Claude Sonnet - faster native review
- openai-gpt5.2: OpenAI GPT-5.2 - base model
- openai-gpt5.3-codex: OpenAI GPT-5.3 Codex - code-specialized
- openai-gpt5.2-pro: OpenAI GPT-5.2 Pro - extended capabilities (Recommended)
- gemini-3-flash: Google Gemini 3 Flash - fast, efficient
- gemini-3-pro: Google Gemini 3 Pro - advanced reasoning (Recommended)
```

**Default selection:** claude-opus, openai-gpt5.2-pro, gemini-3-pro

**Question 2:** Select reasoning effort (if OpenCode reviewers selected):
```
Header: Reasoning
Question: What reasoning effort level for OpenCode reviewers?
multiSelect: false
Options:
- low: Quick responses, minimal deliberation
- medium: Balanced reasoning (Recommended)
- high: Deep analysis, thorough deliberation
- xhigh: Maximum reasoning (GPT-5.2 only)
```

**Default:** medium

**Model mapping:**
- `claude-opus` → `{type: claude, model: opus}`
- `claude-sonnet` → `{type: claude, model: sonnet}`
- `openai-gpt5.2` → `{type: opencode, model: openai/gpt-5.2}`
- `openai-gpt5.3-codex` → `{type: opencode, model: openai/gpt-5.3-codex}`
- `openai-gpt5.2-pro` → `{type: opencode, model: openai/gpt-5.2}`
- `gemini-3-flash` → `{type: opencode, model: google/gemini-3-flash-preview}`
- `gemini-3-pro` → `{type: opencode, model: google/gemini-3-pro-preview}`

### Step 4: Create Directory and Documents

```bash
mkdir -p ./scopes/[scope-name]/
```

Generate these files:

1. **`scope.md`** — Goal, context, requirements, verification (replaces spec.md + context.md)
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

**design.md trigger:** Created when Design opt-in selected during validation. All sections optional — include only what adds value.

> **Reference:** See [reference/quality-model.md](reference/quality-model.md) for design document quality patterns.

### Step 5: Populate TodoWrite from tasks.yaml

Parse the just-created `tasks.yaml` and populate TodoWrite:

1. Read tasks from `tasks.yaml`
2. Create TodoWrite with up to 10 tasks:
   - status: map from tasks.yaml status
   - content: task content field
   - activeForm: task active_form field

### Step 6: Present Summary

Show user:
- Directory created: `./scopes/[scope-name]/`
- Scope document: scope.md (brief overview)
- Design document: design.md (if created)
- Tooling artifacts: tasks.yaml, dependencies.yaml, validation.yaml
- Validation coverage (taxonomy areas)
- Next action: "Run `/scope review` or start implementation"

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

# Review Sub-Operation

Multi-perspective scope review using parallel subagent dispatch.

> **Reference:** See [reference/review.md](reference/review.md) for reviewer roles, harnesses, report schemas, and edge case handling.

---

## When to Use

- After creation to validate before implementation
- When scope feels incomplete or ambiguous
- Before `task-dispatch` for Initiatives
- Standalone review of existing scopes

---

## Review Workflow

### Step 1: Identify Scope

1. Parse scope name from argument (e.g., `/scope review auth-system`)
2. If no argument: find most recent in `./scopes/`
3. Read scope documents: `scope.md`, `tasks.yaml`, `validation.yaml`, and `design.md` (if present)

### Step 2: Select Reviewers

**Question 1:** Select reviewers:
```
Header: Reviewers
Question: Which reviewers should analyze this scope?
multiSelect: true
Options:
- claude-opus: Claude Opus - native subagent, comprehensive, context-aware
- claude-sonnet: Claude Sonnet - faster native review
- openai-gpt5.2: OpenAI GPT-5.2 - base model
- openai-gpt5.3-codex: OpenAI GPT-5.3 Codex - code-specialized
- openai-gpt5.2-pro: OpenAI GPT-5.2 Pro - extended capabilities
- gemini-3-flash: Google Gemini 3 Flash - fast, efficient
- gemini-3-pro: Google Gemini 3 Pro - advanced reasoning
```

**Default selection:** claude-opus, openai-gpt5.2-pro, gemini-3-pro

**Question 2:** Select provider (if OpenCode reviewers selected):
```
Header: Provider
Question: Which provider for OpenCode reviewers?
multiSelect: false
Options:
- native: Native APIs (openai/google) (Recommended)
- github-copilot: GitHub Copilot
```

**Default:** native

**Question 3:** Select reasoning effort (if OpenCode reviewers selected):
```
Header: Reasoning
Question: What reasoning effort level for OpenCode reviewers?
multiSelect: false
Options:
- low: Quick responses, minimal deliberation
- medium: Balanced reasoning (Recommended)
- high: Deep analysis, thorough deliberation
- xhigh: Maximum reasoning (GPT-5.2 only)
```

**Default:** medium

**Model mapping to commands:**
- `claude-opus` → Task tool with `subagent_type: "general"`
- `claude-sonnet` → Task tool with `subagent_type: "general"`

Provider determines the model path prefix:

| Reviewer | native | github-copilot |
|---|---|---|
| `openai-gpt5.2` | `openai/gpt-5.2` | `github-copilot/gpt-5.2` |
| `openai-gpt5.3-codex` | `openai/gpt-5.3-codex` | `github-copilot/gpt-5.3-codex` |
| `openai-gpt5.2-pro` | `openai/gpt-5.2` | `github-copilot/gpt-5.2` |
| `gemini-3-flash` | `google/gemini-3-flash-preview` | `github-copilot/gemini-3-flash` |
| `gemini-3-pro` | `google/gemini-3-pro-preview` | `github-copilot/gemini-3-pro` |

Command: `opencode run --model "{model_path}" --variant {reasoning}-medium`

### Step 3: Dispatch Reviewers in Parallel

**CRITICAL:** Dispatch all selected reviewers in the same message for true parallelism.

**Review Prompt Template:**

```
You are reviewing a scope for completeness and feasibility.

## Scope Documents
[Include scope.md content]
[Include tasks.yaml content]
[Include design.md content if present]

## Review Focus
Evaluate against these gates:

1. **Completeness** - Are all requirements specified? Missing behaviors?
2. **Consistency** - Do documents contradict each other? Ambiguous terms?
3. **Feasibility** - Can tasks be implemented as described? Missing dependencies?
4. **Clarity** - Would a fresh developer understand what to build?
5. **Design Depth** - Are alternatives substantiated, invariants testable, complexity claims evidenced? (n/a if no design.md)

## Output Format
Return a YAML report:

```yaml
reviewer_report:
  reviewer: {REVIEWER_ID}
  gates:
    completeness:
      status: pass | fail
      issues: []
    consistency:
      status: pass | fail
      issues: []
    feasibility:
      status: pass | fail
      issues: []
    clarity:
      status: pass | fail
      issues: []
    design_depth:
      status: pass | fail | n/a
      issues: []
  issues:
    - severity: critical | high | medium
      gate: completeness
      area: ${TAXONOMY_AREA}
      description: "Clear description"
      suggestion: "How to fix"
  clarifying_questions:
    - area: ${TAXONOMY_AREA}
      question: "What needs clarification?"
  strengths:
    - "Positive observation"
```

**Dispatch by Type:**

**Claude reviewers (Task tool):**
```python
Task(
  subagent_type="general",
  prompt=review_prompt
)
```

**OpenCode reviewers (Bash tool, background):**
```bash
timeout 1200 opencode run --model "{MODEL_PATH}" --variant {reasoning}-medium "{review_prompt}"
```

### Step 4: Synthesize Reviews

After all reviewers complete:

1. **Parse reports** — Extract YAML from all outputs
2. **Merge issues:**
   - Deduplicate by description similarity
   - Combine issues flagged by multiple reviewers (higher confidence)
   - Note which reviewer(s) found each issue
3. **Aggregate gates:**
   - Gate fails if ANY reviewer fails it
   - Record which reviewer(s) failed each gate
4. **Prioritize questions:**
   - Group by taxonomy area
   - Rank: Scope > Behavior > Data Model > Constraints > Edge Cases > Integration > Terminology

### Step 5: Present Review

**Gate Summary Table:**

```
| Gate         | Status | Claude | GPT-5.2 Pro | Gemini-3 Pro |
|--------------|--------|--------|-------------|--------------|
| Completeness | FAIL   | fail   | pass        | fail         |
| Consistency  | PASS   | pass   | pass        | pass         |
| Feasibility  | FAIL   | fail   | fail        | pass         |
| Clarity      | PASS   | pass   | pass        | pass         |
| Design Depth | n/a    | n/a    | n/a         | n/a          |
```

**Issues by Severity:**

```
## Critical (must fix before implementation)
- [C1] Missing error handling for auth timeout (Completeness)
  Found by: claude-opus, opencode-gemini3-pro
  Suggestion: Add error case to scope.md#requirements

## High (should fix)
- [H1] Task T003 depends on undefined API contract (Feasibility)
  Found by: claude-opus, opencode-gpt5.2-pro
  Suggestion: Define API in scope.md#context or defer task
```

### Step 6: Clarifying Questions

Use **AskUserQuestion** with questions grouped by taxonomy area.

Record answers for validation.yaml update.

### Step 7: Update Validation

Add clarification session to `validation.yaml`:

```yaml
clarification_sessions:
  - id: S00${N}
    timestamp: ${ISO_TIMESTAMP}
    source: scope-review
    reviewers: [claude-opus, opencode-gpt5.2]
    questions:
      - id: Q001
        question: "${QUESTION}"
        answer: "${ANSWER}"
        area: ${TAXONOMY_AREA}
        doc_updates:
          - file: scope.md
            section: ${SECTION}
            action: modified
```

Update `markers` section:
- Close resolved markers (`status: resolved`)
- Add new markers for deferred questions (`status: open`)

### Step 8: Recommend Action

**All gates pass:**
```
Review complete. All gates passed.
Recommendation: Ready for implementation.
```

**Issues found:**
```
Review complete. 2 gates failed.
Recommendation:
1. Address critical/high issues
2. Re-run /scope review
```

---

## Gates

| Gate | What It Checks |
|------|----------------|
| **Completeness** | All requirements specified, no missing behaviors |
| **Consistency** | Documents align, no contradictions, terms used consistently |
| **Feasibility** | Tasks implementable, dependencies available, no blockers |
| **Clarity** | Unambiguous, fresh developer can understand scope |
| **Design Depth** | Alternatives substantiated, invariants testable, complexity evidenced (n/a when no design.md) |

---

## Edge Cases

**OpenCode timeout (> 20 minutes):**
- Continue with completed reviews
- Note in output: "[Reviewer] timed out, partial results"

**One reviewer fails:**
- Parse what you can
- Report partial results with clear indication

**No reviewers selected:**
- Default to claude-opus only
- Warn: "Consider adding external reviewers for diverse perspectives"

**Scope not found:**
- List available scopes
- Ask user to specify

---

# Update Sub-Operation

Synchronize scope documents with actual project state by analyzing git commits.

---

## Pre-loaded Context for Update

Working directory:
!`git status --short`

Recent commits:
!`git log --oneline -20`

---

## Update Workflow

### Step 1: Locate and Parse Scope

1. **Find scope:** If name provided, use that. Else, find most recent in `./scopes/`
2. **Parse structure:** Extract tasks with current status from tasks.yaml
3. **Determine baseline:** Use file creation time or first commit mentioning scope

### Step 2: Analyze Current State

```bash
git log --oneline --since="<scope-creation-time>" --all
git log --stat --since="<scope-creation-time>" --all
git status --short
git diff <baseline>..HEAD --name-status
```

### Step 2.5: Sync TodoWrite to tasks.yaml

If TodoWrite has entries matching scope tasks:
1. For each "completed" todo, update corresponding task to `status: completed`
2. For each "in_progress" todo, update to `status: in_progress`
3. Update `meta.last_updated` and `meta.progress` fields

### Step 3: Map Evidence to Tasks

For each task:
1. Search for evidence (commit messages, file modifications, test existence)
2. Determine status: `completed`, `in_progress`, `pending`, `blocked`
3. Collect evidence notes (commits, files, test results)

### Step 4: Update tasks.yaml

Update task statuses and add evidence:

```yaml
tasks:
  - id: PROJ-001
    content: Set up project structure
    status: completed
    active_form: Setting up project structure
    evidence:
      commits: [c228fea, 2f069d7]
      files: [src/feature.py, tests/test_feature.py]
```

### Step 5: Present Summary

```
## Scope Update Summary

Scope: ./scopes/refactor/
Tasks: tasks.yaml (progress: 5/10)

Status:
  Completed: 5 tasks
  In Progress: 2 tasks
  Pending: 3 tasks

Next actions:
  1. REFAC-006: Implement validation (ready)
  2. REFAC-007: Add error handling (ready)
```

---

## Matching Heuristics

**Strong evidence (auto-mark complete):**
- Commit message explicitly references task
- Commit modifies exact files mentioned
- All acceptance criteria met

**Weak evidence (mark in-progress):**
- Commit touches related files
- Working directory has related changes

**Conservative approach:** When uncertain, prefer in-progress over completed

---

# Done Sub-Operation

When `/scope done <name>` is invoked:

1. Read `tasks.yaml` and check all tasks completed
2. If tasks remain: warn and ask to proceed or update first
3. Set `status: done` in scope.md frontmatter
4. Present completion summary
5. Offer: "Delete scope directory? Git history preserves everything."

---

# List Sub-Operation

When `/scope list` is invoked:

1. Find all `scopes/*/scope.md` files
2. Read frontmatter from each (status, created, issue_type)
3. Present table:

```
| Scope | Status | Type | Created |
|-------|--------|------|---------|
| auth-system | active | Feature | 2026-03-01 |
| api-refactor | draft | Initiative | 2026-03-10 |
```

---

## Integration

**Command:** `/scope [operation] [name]`

**Related skills:**
- `clarify` — Resolve ambiguities in scope context
- `task-dispatch` — Execute tasks from scope
- `task-continue` — Resume from checkpoint
- `review` — Routes to `/scope review` for scope targets
