# Subagent-Driven Task Execution

Execute scopes with proper TDD: tester writes failing tests, implementer makes them pass, reviewers validate.

**Core principle:** Three-phase batches with fresh subagents. No batch completes without review.

---

## The Four-Phase Pipeline

Each batch executes four phases. **A batch is NOT complete until all four phases finish.**

```
┌─────────────────────────────────────────────────────────────────┐
│                         BATCH N                                 │
├─────────────────────────────────────────────────────────────────┤
│  Phase A: TESTERS (parallel)                                    │
│  ├── Dispatch N tester subagents                                 │
│  ├── Each writes failing tests (RED)                            │
│  └── Wait for ALL testers                                       │
│                          ↓                                      │
│  Phase A.5: TEST REVIEW (Claude Task + one peer)            │
│  ├── Claude Task (opus) [required]                              │
│  ├── peer → codex + gemini (review_config/defaults) [req]   │
│  ├── Check: oracle mirroring, mock tautologies, assertion-free  │
│  └── Gate: clean → Phase B | issues → re-dispatch tester(s)     │
│                          ↓                                      │
│  Phase B: IMPLEMENTERS (parallel)                               │
│  ├── Dispatch N implementer subagents                            │
│  ├── Each receives its tester's report                          │
│  ├── Each makes tests pass (GREEN)                              │
│  └── Wait for ALL implementers                                  │
│                          ↓                                      │
│  Phase C: REVIEWERS (per role: Claude Task + one peer)       │
│  ├── General      — Claude Task + peer [required]           │
│  ├── Architecture — Claude Task + peer (gestalt) [required] │
│  ├── Compliance   — Claude Task + peer (loqui) [required]   │
│  ├── peer fans out to all configured external harnesses     │
│  ├── Each role reviews own gates only; wait for ALL              │
│  └── Synthesize by role, then aggregate                          │
│                          ↓                                      │
│  Gate: Issues found?                                            │
│  ├── Critical/High → Fix before proceeding                      │
│  └── None/Medium → Commit and continue                          │
└─────────────────────────────────────────────────────────────────┘
```

**CRITICAL:** All four phases are mandatory. Test review (Phase A.5) and code review (Phase C) each dispatch, per role, a Claude `Task` **plus one `peer`** that fans out to the configured external harnesses (codex + gemini) — **never shell out to codex/gemini directly; never dispatch Claude alone.** Read `peer`'s manifest: require ≥1 external reviewer `ok`; if only Claude reported (peer skipped/failed), treat the phase as partial and note it. Dispatch contract: [peer skill](../../peer/SKILL.md).

---

## Workflow

### 1. Load Scope and Populate TodoWrite

1. Find most recent scope in `./scopes/*/*/` (lifecycle dirs: `draft`, `active`, `done` — prefer `active` for in-flight work)
2. Read `tasks.yaml` from that directory. Also read `dependencies.yaml` **if it exists** — it carries the precomputed `batches[*]` used in Step 3 (absent for Task scopes, which derive batches from `tasks.yaml`).
3. Parse tasks with `status: pending` or `status: in_progress`
4. Create TodoWrite with ALL uncompleted tasks:
   - First uncompleted task: "in_progress"
   - Others: "pending"
   - content: task text
   - activeForm: present continuous form

**CRITICAL:** Always populate TodoWrite before dispatching any subagents.

5. **Create/checkout branch** per SKILL.md "Git Workflow" → "Branch Determination":
   - Scope-driven execution → `feat/<scope-directory-name>`
   - GitHub issue (if `$ARGUMENTS` carries `gh:<n>`, `#<n>`, or an issue URL) → `<issue#>-<issue-title-in-kebab-case>`
   - Ambiguous → AskUserQuestion (see SKILL.md procedure)
   - MANDATORY: verify current branch matches before Phase A. Never dispatch on `main`/`master`.

6. **Promote scope status `draft` → `active`:**
   - Read `scope.md` frontmatter
   - If `status: draft`, edit frontmatter to `status: active`
   - Skip if already `active` or `done`

### 2. Pre-Implementation Gate Check

Before dispatching any tasks, verify validation.yaml gates:

1. Read `validation.yaml` from scope directory

**Mandatory review gate (all issue types).** Check `review_gate.status`:
- `passed` → proceed.
- absent or `failed` → the scope has not cleared its mandatory review gate. **Do not dispatch tasks.** Report that the scope is not implementable and run `/scope review <name>` (which writes `review_gate.status` on a clean pass). Only proceed once the gate is `passed`. This is the scope-level analog of the `issue` skill's pre-publish gate; it is blocking and is not skippable per issue type.

2. Check `metadata.issue_type`
3. **If Initiative:**
   - Check all gates in `gates` section
   - If any gate has `status: fail`:
     - Report which gates failed with reasons
     - Prompt: "Resolve via /clarify or proceed anyway?"
     - If user chooses to proceed: document override in validation.yaml
   - Check `markers` section for `status: open`
   - If blocking markers exist:
     - Report marker count and summaries
     - Prompt: "Resolve markers first or proceed?"
4. **If Feature/Task:** Skip gate check (gates marked n/a)

### 3. Analyze Task Dependencies → Build Batches

Determine execution batches from the batch signal. **Two sources, in order:**

1. **`dependencies.yaml` present** (Feature/Initiative) → use its precomputed `batches[*].tasks`
   directly. Each `batch` entry is one parallel group, in order.
2. **`dependencies.yaml` absent** (Task scopes) → derive batches from `tasks.yaml` using the
   `depends_on` + `files` fields per task.

**Derivation rules** (identical to the rules documented in `dependencies.yaml`):
- Tasks with no unmet `depends_on` go in the earliest batch.
- A task joins the earliest batch where **all** its `depends_on` are already complete.
- Tasks sharing any `files` entry **cannot** be in the same batch (same-file → sequential).
- A task with no `files` declared defaults to its own single-task batch (safe fallback).

The result is an ordered list of batches; each batch's tasks dispatch in parallel (Phase A/B
below), and batches run sequentially.

### 4. Execute Batches (Four-Phase Pipeline)

**For each batch, execute ALL FOUR phases:**

#### Phase A: Dispatch Testers

**Single task:**
```
Dispatch 1 tester → wait for completion
```

**Parallel batch (N tasks):**
```
Dispatch N testers in SINGLE message → wait for ALL
```

Each tester:
- Invokes `test` skill
- Writes failing tests (RED)
- Reports: test paths, failure output

**GATE:** Wait for ALL testers to complete before proceeding to Phase B.
- If any tester reports `status: gap` → handle gap (consult scope, ask user, re-dispatch). Do NOT proceed to Phase B.
- If all testers report `status: success` → verify RED state, then proceed to Phase B with their reports.

**RED verification (MANDATORY — never skip):**

**Structural checks** — verify the tests actually fail:
- `failure_output` is non-empty (not null, not blank)
- Output shows test **failures**, not compilation errors or import errors
- Tests fail because the **feature is missing**, not due to typos or broken test setup
- If `failure_output` is empty, shows only errors (not failures), or tests passed → re-dispatch that tester

**Failure mode checks** — read the test code and verify it is not:
- **Oracle mirroring:** Tests that assert what the current code does rather than what it should do.
- **Mock tautologies:** Tests where everything is mocked, leaving nothing real under test.
- **Testing dependencies:** Tests that exercise framework or library behavior rather than application logic.
- **Assertion-free coverage:** Tests that execute code paths but verify nothing meaningful — no assertions, or assertions on trivial properties.

**Verification technique:** Pick one test. Trace what it would do if a key behavior were wrong (e.g., wrong field mapping, wrong transformation). If it would still pass, the test is not testing intent — re-dispatch the tester with specific feedback about what the test must actually verify.

If any failure mode is detected → re-dispatch the tester with feedback identifying the specific problem. Do NOT proceed to Phase A.5 with contaminated tests.

#### Phase A.5: Test Review Gate

**PRECONDITION:** All Phase A testers completed with `status: success` and RED verified.

Dispatch a Claude `Task` **plus one `peer`** (which fans out to all configured external harnesses) on the test files from the batch — same shape as Phase C. Never shell out to codex/gemini directly. Read `peer`'s manifest; require ≥1 external reviewer `ok` before proceeding to Phase B (if only Claude reported, treat as partial).

**Collect inputs:**
- All `test_files[*].path` from all `tester_report`s in this batch
- Tester task descriptions (what behavior each test should verify)

**Resolve reviewer config (in order):** `--reviewers` flag → `validation.yaml` `review_config` → defaults (the reviewers configured in `peer list`, selected via --reviewers / interactive).

**Dispatch template:** See `reference/subagent-workflow.md` — Test Review Dispatch Template (Claude `Task` + one `peer`).

**Gate outcome:**

| Result | Action |
|--------|--------|
| Clean (no issues found) | Proceed to Phase B |
| Oracle mirroring | Re-dispatch affected tester(s) with specific finding |
| Mock tautologies | Re-dispatch affected tester(s) with specific finding |
| Framework tests | Re-dispatch affected tester(s) with specific finding |
| Trivial assertions | Re-dispatch affected tester(s) with specific finding |

After re-dispatch, tester output must pass Phase A.5 again before Phase B.

**INVARIANT:** Implementers NEVER receive tests that failed the test review gate.

#### Phase B: Dispatch Implementers

**PRECONDITION:** Phase A complete. Every implementer MUST receive its corresponding tester_report.
If you have no tester_report for a task, you have not run Phase A — go back and dispatch the tester first.

**Single task:**
```
Dispatch 1 implementer with tester report → wait for completion
```

**Parallel batch (N tasks):**
```
Dispatch N implementers in SINGLE message → wait for ALL
Each receives its corresponding tester's report
```

Each implementer:
- Invokes `implement` skill
- Makes tests pass (GREEN)
- Reports: impl files, test pass output

#### Phase C: Dispatch Reviewers

**CRITICAL:** Reviewers are mandatory. Every batch gets reviewed.

**Resolve batch diff before dispatching:**
```bash
# last_batch_commit from checkpoint.yaml (or initial branch point for first batch)
# diff_cmd: "git diff <last_batch_commit>..HEAD"
# range: <last_batch_commit>..HEAD   (for gestalt diff)
```

**Per role, dispatch in a SINGLE message: a Claude `Task` + one `peer` (which fans out to all configured external harnesses). Never shell out to codex/gemini directly.**

```
Per role (General / Architecture / Compliance), in one message:
  Task(subagent_type="task-reviewer", prompt={role_prompt})              # Claude
  peer -d {role_outdir} --reviewers {externals} "{role_prompt}"      # codex + gemini (fans out)
→ Wait for ALL; read each peer manifest, skip stalled/error rows
```

**Reviewer cascade (each role owns distinct gates):**

| Role | Primary Gates | Skill | Harnesses |
|------|---------------|-------|-----------|
| General | Correctness, Security, Performance | `code review` | Claude `Task` + `peer` |
| Architecture | Architecture | `gestalt` | Claude `Task` + `peer` |
| Compliance | Style | `loqui` | Claude `Task` + `peer` |

**Reviewers receive pointers and load code themselves:**
1. `{diff_cmd}` (e.g., `git diff <last_batch_commit>..HEAD`) — reviewer runs the command
2. Scope directory path — reviewer reads `tasks.yaml` for requirements
3. Workdir — reviewer runs all commands from this directory

**Architecture role additionally runs:**
- `gestalt analyze` — current hotspots, seams, coupling
- `gestalt diff {range}` — definition-level changes
- `gestalt diff {range} --verbose` — impact propagation

**Compliance role additionally reads:**
- Loqui guidelines for each language in the diff (`./skills/loqui/reference/loqui/languages/{lang}/`)

**Dispatch configuration:**

Dispatch reviewers per `/review` infrastructure and `code review` role definitions.

**Resolve harness config (in order):**
1. Explicit `--reviewers` flag passed to `/implement execute` (aliases from `peer list` — see `/review` SKILL.md "Reviewer Selection")
2. `validation.yaml` `review_config` for the active scope → use those reviewers and reasoning effort
3. Defaults: the reviewers configured in `peer list` (selected via --reviewers / interactive)
4. External reviewers are mandatory — never Claude alone. Pass them to `peer`; read its manifest and require ≥1 external `ok` before synthesizing Phase C (if only Claude reported, treat as partial). Models/flags/effort: [peer skill](../../peer/SKILL.md).

Apply the resolved config to all three roles (General, Architecture, Compliance).

See `/review` [reference/harnesses.md](../../review/reference/harnesses.md) for dispatch templates.
Review prompts per role: see `code review` skill Step 4.

### 5. Synthesize Review Feedback and Write review.yaml

After ALL reviewers complete:

1. **Parse reports** - Extract YAML from all reviewer outputs
2. **Merge issues:**
   - Deduplicate by description similarity
   - Combine issues flagged by multiple reviewers (higher confidence)
   - Note which reviewer(s) found each issue
3. **Aggregate severity:**
   - Issue severity is the HIGHEST across all reviewers
   - Critical by any reviewer = Critical overall
4. **Write review.yaml** (append batch review):
   ```yaml
   # ./scopes/<state>/<scope>/review.yaml  (<state> ∈ {draft, active, done})
   batch_reviews:
     - batch: <N>
       timestamp: <ISO_TIMESTAMP>
       commit: <SHA>
       tasks: [T001, T002]
        reviewers:
          # one entry per configured reviewer (see `peer list`)
          - id: {role}-{reviewer-id}
            status: success | timeout | failed
            gates: { correctness: pass, style: pass, ... }
       synthesized:
         gates: { correctness: pass, style: fail, ... }
         critical_issues: <N>
         high_issues: <N>
         medium_issues: <N>
       outcome: approved | changes_requested
   issues:
     critical: [...]
     high: [...]
     medium: [...]
   deferred_issues: [...]  # medium severity
   ```
5. **Present unified feedback:**
   - Gate summary table
   - Issues grouped by severity
   - Show which reviewers found each issue

**Gate Summary Table (by role):**

```
| Gate         | Status | General              | Architecture | Compliance |
|--------------|--------|----------------------|--------------|------------|
| Correctness  | FAIL   | fail (Codex)          | —            | —          |
| Style        | PASS   | —                     | —            | pass       |
| Performance  | PASS   | pass                  | pass         | —          |
| Security     | FAIL   | fail (Claude, Gemini) | —            | —          |
| Architecture | PASS   | —                     | pass         | —          |
```

`—` = not in scope for this role. On failure, parenthetical = which harness(es) failed.

### 6. Apply Review Feedback

**If Critical/High issues found:**
1. Dispatch fix subagent(s)
2. Verify fixes with targeted review
3. Update review.yaml with resolution
4. Only proceed when issues resolved

**If only Medium issues:**
1. Add to review.yaml deferred_issues
2. Proceed to commit

### 7. Commit, Checkpoint, and Continue

When batch completes successfully (all phases, review passed):

1. Update TodoWrite (mark tasks as "completed")
2. Edit tasks.yaml: Change `status: in_progress` to `status: done`
3. **Write checkpoint.yaml** (enables session recovery):
   ```yaml
   checkpoint:
     scope_name: <scope>
     scope_path: ./scopes/<state>/<scope>
     branch: feat/<scope>
     timestamp: <ISO_TIMESTAMP>
     last_batch: <N>
     last_commit: <SHA>
     tasks:
       done: [...]
       pending: [...]
     next_batch:
       number: <N+1>
       tasks: [...]
     deferred_issues: [...]  # medium severity, noted for later
     review_config:
       reviewers: [...]  # from validation.yaml
   ```
4. **Commit the batch changes:**
   - Stage: implementation + tests + tasks.yaml + checkpoint.yaml + review.yaml
   - Commit message format:
     ```
     <type>(<scope>): <description>

     Tasks: <task-ids>
     Batch: <N>/<total>
     ```
   - Example: `feat(cache): add TTL expiry\n\nTasks: PH2-003, PH2-004\nBatch: 2/5`
5. **Base-drift re-check (per batch).** Fetch the trunk and measure drift before starting the next batch — the remote may have advanced since the last batch:
   ```bash
   git fetch origin <trunk> --quiet
   git rev-list --count "HEAD..origin/<trunk>"   # behind-count
   ```
   If `behind > 0`, follow `reference/base-drift-preflight.md` (overlap detection + gate). Rebasing a small drift now prevents a giant conflict at PR time. Record the post-rebase SHA in the next checkpoint's `last_commit`.
6. Move to next batch (or use `/continue` in new session)

### 8. Final Review

**PRECONDITION — sync with trunk first.** Before final review, the branch MUST be rebased current on a freshly fetched `origin/<trunk>` so the review runs on the tree that will actually merge:

```bash
git fetch origin <trunk> --quiet
behind=$(git rev-list --count "HEAD..origin/<trunk>")
[ "$behind" -eq 0 ] || git rebase "origin/<trunk>"   # resolve conflicts; re-run tests GREEN
```

See `reference/base-drift-preflight.md` → "Pre-PR / pre-merge sync". Do not proceed to final review while `behind > 0`.

After ALL batches complete, invoke `code review` skill in **final mode**:

```
/review --final <scope-name>
```

Or dispatch all roles directly (per role: Claude `Task` + one `peer`):

```
Per role (General / Architecture / Compliance), in one message:
  Task(subagent_type="task-reviewer", prompt={role_prompt})         # Claude
  peer -d {role_outdir} --reviewers {externals} "{role_prompt}"  # codex + gemini (fans out)
```

**Final review checks:**
- All scope requirements met (cross-reference scope.md)
- All tasks complete (verify tasks.yaml)
- Acceptance criteria satisfied
- Overall architecture sound
- Deferred issues addressed or documented
- Tests passing

**Write final_review section in review.yaml:**
```yaml
final_review:
  status: completed
  timestamp: <ISO_TIMESTAMP>
  reviewers: [{role}-{reviewer-id}, …]  # from `peer list`
  gates: { correctness: pass, style: pass, ... }
  scope_compliance:
    all_tasks_complete: true
    acceptance_criteria_met: true
    edge_cases_handled: true
  issues: [...]
  strengths: [...]
  overall_assessment: "Implementation complete and verified"
  recommendation: ready_to_merge | changes_requested
readiness:
  all_batches_reviewed: true
  critical_issues_resolved: true
  high_issues_resolved: true
  final_review_passed: true
  tests_passing: true
```

### 9. Prompt to Mark Scope Done

After final review passes (recommendation: `ready_to_merge`), prompt the user via **AskUserQuestion**:

```
Header: Scope complete
Question: All tasks finished and final review passed. Mark scope as done?
multiSelect: false
Options:
- Yes: Run `/scope done <name>` — sets status to done
- No: Leave status as active (you can run `/scope done` later)
```

If user selects Yes, invoke the `scope` skill with `done <name>`. Do NOT set `status: done` directly — that is the `done` operation's job (it also runs final validation).

Skip this prompt if final review recommendation is `changes_requested` — the scope is not ready.

### 10. Auto-Create PR (issue-sourced runs only)

**Trigger:** `$ARGUMENTS` contained a GitHub issue reference (`gh:<n>`, `#<n>`, or a GitHub issue URL) when `/implement` was first invoked.

**When:** After Step 9 scope-done prompt (regardless of the user's answer), once final review recommendation is `ready_to_merge`.

**Action:**

**First, re-confirm trunk sync.** Step 8 rebased current, but time may have passed during review. Re-fetch and verify `behind == 0` before pushing; rebase again if the remote moved. A PR pushed while behind is born `CONFLICTING`/`DIRTY`. See `reference/base-drift-preflight.md` → "Pre-PR / pre-merge sync".

```
Skill(issue, pr --state <STATE> --issue <ISSUE_NUM>)
```

Where:
- `<ISSUE_NUM>` — the issue number extracted during pre-parse
- `<STATE>` — value of `--state` flag from pre-parse (default: `draft`)

The `issue pr` operation handles pushing the branch, building the PR title/body from the issue, and calling `gh pr create`. No additional push or title logic is needed here.

**Do not create a PR** if:
- No issue reference was present in the original `$ARGUMENTS`
- Final review recommendation is `changes_requested`
- A PR already exists for this branch (the `issue pr` operation handles this gracefully)

---

## Subagent Configuration

| Role | Claude Task subagent_type | Skill |
|------|--------------------------|-------|
| Tester | task-tester | test |
| Implementer | task-implementer | implement |
| General Reviewer | task-reviewer | code review |
| Architecture Reviewer | task-reviewer | gestalt |
| Compliance Reviewer | task-reviewer | loqui |

**External reviewers:** the `subagent_type` column applies to Claude native `Task` calls only. codex/gemini are dispatched via **`peer`** (no subagent type), which carries the role via the prompt and fans out to all configured external harnesses.

---

## Quality Gates

| Gate | When | Action if Failed |
|------|------|------------------|
| Pre-impl gate | Before any dispatch | Block if Initiative gates failed |
| RED verification | After Phase A | Structural: `failure_output` non-empty, shows failures (not errors), fails because feature missing |
| **Test review** | **After Phase A, before Phase B** | **Re-dispatch tester(s) with finding; repeat until clean** |
| GREEN verification | After Phase B | `test_output` non-empty, all tests pass, no errors/warnings |
| **Batch review** | **After Phase B (all implementers)** | **Fix before next batch** |
| Final review | After all batches | Address gaps |

---

## Red Flags

**Never:**
- Skip the tester phase (implementer must receive failing tests)
- **Skip the test review gate (Phase A.5 — every batch's tests must be reviewed)**
- **Skip the code reviewer phase (Phase C — every batch must be reviewed)**
- Pass tests to the implementer without first clearing Phase A.5
- Use sonnet/explore for task subagents (always general)
- Dispatch parallel subagents on same file
- Let implementer write tests (tester's job)
- Ignore failed pre-impl gates for Initiatives
- Batch commits across multiple batches
- **Let subagents return prose around YAML reports (context explosion risk)**

**If tester can't write tests:**
- Don't skip to implementer
- Handle the gap (consult scope, ask user)
- Re-dispatch tester with clarification

**If reviewers timeout:**
- Continue with available reviews (minimum 1)
- Note partial results in output
- Consider re-running batch

---

## Example Workflow

```
[Load scope, create TodoWrite, checkout branch]

Batch 1: Task 1 (single task)
├── Phase A: Dispatch tester
│   └── Tester: Wrote 3 tests, all failing (RED)
├── Phase A.5: Dispatch reviewers (Claude Task + peer → configured harnesses in parallel)
│   ├── Claude: Clean
│   ├── Codex: Clean
│   └── Gemini: Clean — no oracle mirroring or tautologies
├── Phase B: Dispatch implementer + tester report
│   └── Implementer: Made tests pass (GREEN)
├── Phase C: Dispatch reviewers (3 in parallel)
│   ├── Claude: approved, no issues
│   ├── Codex: approved, 1 minor issue
│   └── Gemini: approved, no issues
├── Synthesize: 1 minor issue (note for later)
└── Commit: feat(cache): add caching layer

Batch 2: Tasks 2, 3, 4 (parallel batch — independent, different files)
├── Phase A: Dispatch 3 testers (single message)
│   └── All testers complete with failing tests
├── Phase A.5: Dispatch reviewers (Claude Task + peer → configured harnesses in parallel, all 3 test files)
│   ├── Synthesized: Task 2 tests — oracle mirroring detected (flagged by Codex)
│   ├── Re-dispatch Task 2 tester with finding
│   └── Task 2 re-tester: Clean on second attempt
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

## Context Budget

Subagent outputs are the primary source of context consumption. Each `TaskOutput` result
embeds the full subagent conversation into the parent session (duplicated across `.output`
and `.result` fields — a platform bug). Mitigations:

1. **YAML-only final messages** — All dispatch templates instruct subagents to return ONLY the YAML report. No prose, no explanation, no summary.
2. **Truncated output fields** — `failure_output` and `test_output` limited to last 20 lines (summary + counts).
3. **Batch size awareness** — With N parallel subagents, context grows by ~N × (subagent conversation size). Limit parallel batch size when context is above 50%.

---

## Integration

**Use with:**
- `scope` - Create scope before execution
- `clarify` - Resolve markers/gates before execution
- `test` - Tester invokes for TDD methodology
- `implement` - Implementer invokes for language guidelines
- `code review` - General reviewer invokes for review methodology
- `gestalt` - Architecture reviewer invokes for structural analysis
- `loqui` - Compliance reviewer invokes for language guidelines
- `implement` (verify operation) - Verify before claiming done

---

## Reference

- [subagent-workflow.md](../reference/subagent-workflow.md) - Dispatch templates and YAML reports
- [report.md](../reference/report.md) - YAML report schemas
- [checkpoint-format.md](../reference/checkpoint-format.md) - Session checkpoint schema
- [review.md](../reference/review.md) - Implementation review schema (review.yaml)
- [roles/tester.md](../reference/roles/tester.md) - Test-writing subagent
- [roles/implementer.md](../reference/roles/implementer.md) - Implementation subagent
- [roles/reviewer.md](../reference/roles/reviewer.md) - Review subagent
