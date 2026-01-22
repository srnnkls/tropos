---
name: task-dispatch
description: Subagent-driven task execution with TDD workflow. Dispatches tester subagent (writes failing tests) then implementer subagent (makes tests pass), with batch review.
---

# Subagent-Driven Task Execution

Execute specs with proper TDD: tester writes failing tests, implementer makes them pass, reviewers validate.

**Core principle:** Three-phase batches with fresh subagents. No batch completes without review.

---

## When to Use

**Use when:**
- Executing an implementation spec (created with `spec-create`)
- Tasks are mostly independent
- Want TDD enforcement with quality gates

**Don't use when:**
- No spec exists yet (use `spec-validate` → `spec-create` first)
- Tasks are tightly coupled (manual execution better)
- Single small task (just do it directly)
- Initiative spec has failed gates (resolve first via /spec.clarify)

---

## The Three-Phase Pipeline

Each batch executes three phases. **A batch is NOT complete until all three phases finish.**

```
┌─────────────────────────────────────────────────────────────────┐
│                         BATCH N                                 │
├─────────────────────────────────────────────────────────────────┤
│  Phase A: TESTERS (parallel)                                    │
│  ├── Dispatch N task-tester subagents (opus)                    │
│  ├── Each writes failing tests (RED)                            │
│  └── Wait for ALL testers                                       │
│                          ↓                                      │
│  Phase B: IMPLEMENTERS (parallel)                               │
│  ├── Dispatch N task-implementer subagents (opus)               │
│  ├── Each receives its tester's report                          │
│  ├── Each makes tests pass (GREEN)                              │
│  └── Wait for ALL implementers                                  │
│                          ↓                                      │
│  Phase C: REVIEWERS (parallel)                                  │
│  ├── Dispatch 1 native Claude reviewer (opus) [required]        │
│  ├── Dispatch 0-N OpenCode reviewers (from validation.yaml)     │
│  ├── Each reviews ALL changes from batch                        │
│  ├── Wait for ALL reviewers                                     │
│  └── Synthesize feedback                                        │
│                          ↓                                      │
│  Gate: Issues found?                                            │
│  ├── Critical/High → Fix before proceeding                      │
│  └── None/Medium → Commit and continue                          │
└─────────────────────────────────────────────────────────────────┘
```

**CRITICAL:** All three phases are mandatory. Reviewers are not optional.

---

## Workflow

### 1. Load Spec and Populate TodoWrite

1. Find most recent spec in `./specs/active/*/`
2. Read `tasks.yaml` from that directory
3. Parse tasks with `status: pending` or `status: in_progress`
4. Create TodoWrite with ALL uncompleted tasks:
   - First uncompleted task: "in_progress"
   - Others: "pending"
   - content: task text
   - activeForm: present continuous form

**CRITICAL:** Always populate TodoWrite before dispatching any subagents.

5. **Create/checkout spec branch:**
   - Branch name: `feat/<spec-directory-name>`
   - If branch exists, checkout and pull
   - If not, create from main/master

### 2. Pre-Implementation Gate Check

Before dispatching any tasks, verify validation.yaml gates:

1. Read `validation.yaml` from spec directory
2. Check `metadata.issue_type`
3. **If Initiative:**
   - Check all gates in `gates` section
   - If any gate has `status: failed`:
     - Report which gates failed with reasons
     - Prompt: "Resolve via /spec.clarify or proceed anyway?"
     - If user chooses to proceed: document override in validation.yaml
   - Check `markers` section for `status: open`
   - If blocking markers exist:
     - Report marker count and summaries
     - Prompt: "Resolve markers first or proceed?"
4. **If Feature/Task:** Skip gate check (gates marked n/a)

### 3. Analyze Task Dependencies

Parse `dependencies.yaml` to identify execution batches:

**Dependency rules:**
- Tasks in Phase N depend on Phase N-1 completion
- Tasks with `[P]` marker AND different file paths can run in parallel
- Tasks with same file path must run sequentially
- Phase boundaries force batch breaks

### 4. Execute Batches (Three-Phase Pipeline)

**For each batch, execute ALL THREE phases:**

#### Phase A: Dispatch Testers

**Single task:**
```
Dispatch 1 task-tester (opus) → wait for completion
```

**Parallel batch (N tasks):**
```
Dispatch N task-testers in SINGLE message → wait for ALL
```

Each tester:
- Invokes `code-test` skill
- Writes failing tests (RED)
- Reports: test paths, failure output

#### Phase B: Dispatch Implementers

**Single task:**
```
Dispatch 1 task-implementer (opus) with tester report → wait for completion
```

**Parallel batch (N tasks):**
```
Dispatch N task-implementers in SINGLE message → wait for ALL
Each receives its corresponding tester's report
```

Each implementer:
- Invokes `code-implement` skill
- Makes tests pass (GREEN)
- Reports: impl files, test pass output

#### Phase C: Dispatch Reviewers

**CRITICAL:** Reviewers are mandatory. Every batch gets reviewed.

**Always dispatch ALL reviewers in a SINGLE message for true parallelism:**

```
Dispatch:
  - 1 native Claude reviewer (task-reviewer, opus) [required]
  - 0-N OpenCode reviewers (models from validation.yaml)
→ Wait for ALL reviewers
```

Each reviewer:
- Invokes `code-review` skill
- Reviews ALL changes from the batch together
- Checks against spec requirements
- Produces YAML report with issues by severity

**Reviewer dispatch configuration:**

Native Claude reviewer:
```python
Task(
  subagent_type="task-reviewer",
  model="opus",
  prompt=review_prompt  # includes all implementer reports + task specs
)
```

OpenCode reviewers:
```bash
timeout 300 opencode run --model "{MODEL}" "{review_prompt}"
```

Models are configured in `validation.yaml` under `review_config.reviewers`.

### 5. Synthesize Review Feedback

After ALL reviewers complete:

1. **Parse reports** - Extract YAML from all reviewer outputs
2. **Merge issues:**
   - Deduplicate by description similarity
   - Combine issues flagged by multiple reviewers (higher confidence)
   - Note which reviewer(s) found each issue
3. **Aggregate severity:**
   - Issue severity is the HIGHEST across all reviewers
   - Critical by any reviewer = Critical overall
4. **Present unified feedback:**
   - Group by severity
   - Show which reviewers found each issue

**Gate Summary Table:**

```
| Gate         | Claude | Codex  | Gemini |
|--------------|--------|--------|--------|
| Correctness  | pass   | fail   | pass   |
| Style        | pass   | pass   | pass   |
| Performance  | pass   | pass   | pass   |
| Security     | fail   | pass   | fail   |
| Architecture | pass   | pass   | pass   |
```

### 6. Apply Review Feedback

**If Critical/High issues found:**
1. Dispatch fix subagent(s) (task-implementer, opus)
2. Verify fixes with targeted review
3. Only proceed when issues resolved

**If only Medium issues:**
1. Note for later
2. Proceed to commit

### 7. Commit and Continue

When batch completes successfully (all phases, review passed):

1. Update TodoWrite (mark tasks as "completed")
2. Edit tasks.yaml: Change `status: in_progress` to `status: completed`
3. **Commit the batch changes:**
   - Stage relevant files (implementation + tests)
   - Commit message format:
     ```
     <type>(<scope>): <description>

     Tasks: <task-ids>
     ```
   - Example: `feat(cache): add TTL expiry support\n\nTasks: PH2-003, PH2-004`
4. Move to next batch

### 8. Final Review

After ALL batches complete, dispatch final multi-reviewer pass:

```
Dispatch (in same message):
  - 1 native Claude reviewer (opus) [required]
  - 0-N OpenCode reviewers (from validation.yaml)
```

Reviews entire implementation:
- Check all spec requirements met
- Validate overall architecture
- Identify any remaining gaps

---

## Subagent Configuration

| Role | Subagent Type | Model | Skill |
|------|---------------|-------|-------|
| Tester | task-tester | opus | code-test |
| Implementer | task-implementer | opus | code-implement |
| Reviewer | task-reviewer | opus | code-review |

**CRITICAL:** Always specify `model: opus` in Task tool calls.

---

## Quality Gates

| Gate | When | Action if Failed |
|------|------|------------------|
| Pre-impl gate | Before any dispatch | Block if Initiative gates failed |
| RED verification | After tester | Verify tests actually fail |
| GREEN verification | After implementer | Verify tests pass |
| **Batch review** | **After all implementers** | **Fix before next batch** |
| Final review | After all batches | Address gaps |

---

## Red Flags

**Never:**
- Skip the tester phase (implementer must receive failing tests)
- **Skip the reviewer phase (every batch must be reviewed)**
- Use sonnet for subagents (always opus)
- Dispatch parallel subagents on same file
- Let implementer write tests (tester's job)
- Ignore failed pre-impl gates for Initiatives
- Batch commits across multiple batches

**If tester can't write tests:**
- Don't skip to implementer
- Handle the gap (consult spec, ask user)
- Re-dispatch tester with clarification

**If reviewers timeout:**
- Continue with available reviews (minimum 1)
- Note partial results in output
- Consider re-running batch

---

## Example Workflow

```
[Load spec, create TodoWrite, checkout branch]

Batch 1: Task 1 (single task)
├── Phase A: Dispatch tester (opus)
│   └── Tester: Wrote 3 tests, all failing (RED)
├── Phase B: Dispatch implementer (opus) + tester report
│   └── Implementer: Made tests pass (GREEN)
├── Phase C: Dispatch reviewers (3 in parallel)
│   ├── Claude: approved, no issues
│   ├── Codex: approved, 1 minor issue
│   └── Gemini: approved, no issues
├── Synthesize: 1 minor issue (note for later)
└── Commit: feat(cache): add caching layer

Batch 2: Tasks 2, 3, 4 ([P] parallel batch)
├── Phase A: Dispatch 3 testers (single message)
│   └── All testers complete with failing tests
├── Phase B: Dispatch 3 implementers (single message)
│   └── All implementers complete, tests passing
├── Phase C: Dispatch reviewers (3 in parallel)
│   ├── Claude: changes_requested, 1 critical
│   ├── Codex: changes_requested, 1 critical (same issue)
│   └── Gemini: approved
├── Synthesize: 1 critical issue (found by 2 reviewers)
├── Fix: Dispatch fix subagent → verify
└── Commit: feat(api): add endpoints for tasks 2, 3, 4

...

[Final review - 3 reviewers in parallel]
All requirements met
```

---

## Integration

**Use with:**
- `spec-validate` → `spec-create` - Create spec before dispatch
- `spec-clarify` - Resolve markers/gates before dispatch
- `code-test` - Tester invokes for TDD methodology
- `code-implement` - Implementer invokes for language guidelines
- `code-review` - Reviewer invokes for review methodology
- `task-completion-verify` - Verify before claiming done

---

## Reference

- [subagent-workflow.md](reference/subagent-workflow.md) - Dispatch templates and YAML reports
- [report-format.md](reference/report-format.md) - YAML report schemas
- [roles/tester.md](reference/roles/tester.md) - Test-writing subagent
- [roles/implementer.md](reference/roles/implementer.md) - Implementation subagent
- [roles/reviewer.md](reference/roles/reviewer.md) - Review subagent
