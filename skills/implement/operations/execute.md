# Subagent-Driven Task Execution

Execute scopes with proper TDD: tester writes failing tests, implementer makes them pass, reviewers validate. Any role may be native or external according to the live implementation configuration.

**Core principle:** Four-phase batches with fresh agents. No batch completes without review.

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
│  Phase A.5: TEST REVIEW (configured host-native / external)     │
│  ├── Configured native reviewer dispatches [if configured]      │
│  ├── Configured external reviewers via peer [if configured]     │
│  ├── Check: oracle mirroring, mock tautologies, assertion-free  │
│  └── Gate: clean → Phase B | issues → re-dispatch tester(s)     │
│                          ↓                                      │
│  Phase B: IMPLEMENTERS (parallel)                               │
│  ├── Dispatch N implementer subagents                            │
│  ├── Each receives its tester's report                          │
│  ├── Each makes tests pass (GREEN)                              │
│  └── Wait for ALL implementers                                  │
│                          ↓                                      │
│  Phase C: REVIEWERS (configured host-native / external)         │
│  ├── General      — configured reviewer set [required]          │
│  ├── Architecture — configured reviewer set (gestalt) [required]│
│  ├── Compliance   — configured reviewer set (loqui) [required]  │
│  ├── peer fans out to all configured external harnesses     │
│  ├── Each role reviews own gates only; wait for ALL              │
│  └── Synthesize by role, then aggregate                          │
│                          ↓                                      │
│  Gate: Issues found?                                            │
│  ├── Critical/High → Fix before proceeding                      │
│  └── None/Medium → Commit and continue                          │
└─────────────────────────────────────────────────────────────────┘
```

**CRITICAL:** All four phases are mandatory. Reload `config.yaml` immediately before each
dispatch. Test review (Phase A.5) and code review (Phase C) dispatch configured native aliases
through their host-native mechanism and external aliases through one `peer --agent reviewer`
fan-out per role. Require at least one success from every execution class actually configured
(native and/or external); never require an absent class. Dispatch contract:
[peer skill](../../peer/SKILL.md).

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

7. **Resolve implementation-agent configuration:**
   - Follow [reference/configuration.md](../reference/configuration.md).
   - A top-level execution creates a new epoch in `<scope>/config.yaml`.
   - Merge built-in defaults, the current scope config, then any inline `--config` assignments.
   - If `--config` was supplied, validate and persist without prompting. Otherwise run interactive
     setup, using the merged values as recommendations, then persist the selections.
   - Under Codex with native delegation available, recommend the `codex-native`/`inherit` defaults;
     otherwise recommend the explicit-host defaults from `reference/configuration.md`.
   - Enforce same-host-family native routing from registry metadata: Codex rejects `opus`/`sonnet`
     and every peer Codex-family alias (use `codex-native`; Claude family may use `*-cli`); Claude
     rejects `codex-native` and every peer Claude-family alias (use native `opus`/`sonnet`; GPT
     family may use peer). Apply this to interactive and inline config, stopping for edits rather
     than silently converting.
   - Do not use `validation.yaml.review_config`; it belongs only to pre-implementation scope review.

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

**Scope-backed mutating-stage checkpoint invariant:** Immediately before every tester,
implementer, or fix dispatch, write one `checkpoint.incomplete_stages` entry per task using
`reference/checkpoint-format.md`. This applies to native Tasks and external peers. Assign every
entry a `.peer/<scope>/<run>/b<batch>-<stage>-<task>/` report directory and capture baseline git
status/diff evidence. After a valid stage report passes its RED/GREEN/fix gate, save the normalized
report there and remove only that task's entry. On failure or interruption, update that entry with
post-failure evidence and pause; never clear it merely because the dispatch process exited.
If the first batch has no checkpoint yet, create its progress skeleton with
`incomplete_stages: []` before adding the first marker.

Also persist and advance `checkpoint.phase_cursor` before and after every phase/gate, including
per-agent test/targeted reviews and per-role Phase C/final reviews. `incomplete_stages` has priority;
otherwise the cursor is the authoritative resume position. Direct tasks do not create a checkpoint:
keep the same cursor/marker state in memory and store prompts, reports, and git evidence under
`.peer/direct/<run>/<stage>/`.

#### Phase A: Dispatch Testers

For a scope run, set `phase_cursor` to `tester: in_progress` before dispatch. After all required
tester entries clear and RED is verified, write `tester: completed`, then
`test_review: pending`.

Immediately before dispatch, reload `config.yaml.routing.tester`. Route the configured singular
agent as described in `reference/subagent-workflow.md`:

- `codex-native` → Codex native tester delegation, inheriting session model/reasoning.
- Explicit native alias → `Task(subagent_type="tester", model="<alias>", prompt=...)`.
- External alias → write `<stage-outdir>/prompt.md`, then run `peer -C <workdir>
  -d <stage-outdir> --agent tester --peers <alias> --effort <effort>
  --prompt-file <stage-outdir>/prompt.md`.

**Single task:**
```
Dispatch 1 configured tester → wait for completion
```

**Parallel batch (N tasks):**
```
Dispatch N configured testers in SINGLE message → wait for ALL
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

If an external tester fails, stalls, or produces no valid report, preserve any partial test edits,
capture `git status --short` and the relevant `git diff`, mark Phase A incomplete, and pause for
deliberate redispatch or `/continue`. Never retry, roll back, or advance automatically.

Native tester interruption or invalid output follows the same checkpoint recovery rule. A
parallel batch may clear successful tester entries while retaining only the failed/in-flight task
entries.

#### Phase A.5: Test Review Gate

**PRECONDITION:** All Phase A testers completed with `status: success` and RED verified.

Reload `config.yaml.routing.reviewer`. Dispatch `codex-native` through Codex native delegation,
explicit native aliases through `Task(subagent_type="reviewer", model="<alias>")`, and configured
external aliases through one `peer --agent reviewer --peers <aliases>` call. Require at least one
success from each configured execution class before proceeding; skip peer entirely for all-native
configuration.

Set `phase_cursor` to `test_review: in_progress` and persist each configured agent's report
directory/status before dispatch. Update results independently. On interruption, leave this cursor
in place so recovery reruns only non-`ok` reports, not Phase A. On a clean gate write completed and
advance to `implementer: pending`; findings advance to `tester: pending` for affected tasks only.

**Collect inputs:**
- All `test_files[*].path` from all `tester_report`s in this batch
- Tester task descriptions (what behavior each test should verify)

**Dispatch template:** See `reference/subagent-workflow.md` — Test Review Dispatch Template.

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

Set `phase_cursor` to `implementer: in_progress` before dispatch. After every task clears its
mutating marker and GREEN is verified, write completed and create `code_review: pending` with all
three roles pending.

Immediately before dispatch, reload `config.yaml.routing.implementer`. Route the configured
singular agent through Codex native delegation for `codex-native`, native
`Task(subagent_type="implementer", model="<alias>")` for explicit native aliases, or external
`peer --agent implementer` as described in `reference/subagent-workflow.md`.

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

If an external implementer fails, stalls, or produces no valid report, preserve all partial edits,
capture `git status --short` and the relevant `git diff`, mark Phase B incomplete, and pause for
deliberate redispatch or `/continue`. Never retry, roll back, or advance automatically.

Native implementer interruption or invalid output follows the same checkpoint recovery rule.

#### Phase C: Dispatch Reviewers

**CRITICAL:** Reviewers are mandatory. Every batch gets reviewed.

**Resolve batch diff before dispatching:**
```bash
# last_batch_commit from checkpoint.yaml (or initial branch point for first batch)
# diff_cmd: "git diff <last_batch_commit>..HEAD"
# range: <last_batch_commit>..HEAD   (for gestalt diff)
```

Run `diff_cmd` before dispatch and embed its materialized output in every role prompt. The command
itself is optional supplemental context for shell-capable reviewers, never the primary input.

Immediately before **each role**, reload `config.yaml.routing.reviewer`. Dispatch every configured
native alias through its host-native mechanism and fan configured external aliases through one
`peer --agent reviewer` call. Never invoke peer when no external class is configured, and never
pass `codex-native` to peer.

Set the Phase C cursor/role to `in_progress` before each dispatch, including per-agent report
statuses/directories. Preserve completed roles. An interruption reruns only non-`ok` agents in the
current role; after all roles pass, advance to the next batch's tester or to fix handling.

```
Per role (General / Architecture / Compliance), in one message:
  Codex native delegation(role=reviewer, prompt={role_prompt})     # codex-native, if configured
  Task(subagent_type="reviewer", model={native_alias}, prompt={role_prompt})  # opus/sonnet
  peer -C {workdir} -d {role_outdir} --agent reviewer \           # only if externals configured
    --peers {external_aliases} --effort {reviewer_effort} \
    --prompt-file {role_outdir}/prompt.md
→ Wait for ALL; require ≥1 success from each configured execution class
```

**Reviewer cascade (each role owns distinct gates):**

| Role | Primary Gates | Skill | Harnesses |
|------|---------------|-------|-----------|
| General | Correctness, Security, Performance | `code review` | Configured native and/or external class |
| Architecture | Architecture | `gestalt` | Configured native and/or external class |
| Compliance | Style | `loqui` | Configured native and/or external class |

**Every reviewer prompt is self-contained:**
1. Embed the materialized batch diff, not only `{diff_cmd}`.
2. Embed the applicable task requirements and acceptance criteria from `tasks.yaml`.
3. Embed the exact reviewer YAML output schema.
4. Shell-capable reviewers may also receive `{diff_cmd}`, scope path, and workdir for exploration;
   shell-less external reviewers must be able to complete from prompt contents alone.

**Architecture role additionally runs:**
- `gestalt analyze` — current hotspots, seams, coupling
- `gestalt diff {range}` — definition-level changes
- `gestalt diff {range} --verbose` — impact propagation

Materialize these outputs into the architecture prompt for shell-less reviewers; shell-capable
reviewers may also rerun the commands.

**Compliance role additionally reads:**
- Loqui guidelines for each language in the diff (`./skills/loqui/reference/loqui/languages/{lang}/`)

Embed the applicable guideline excerpts in the compliance prompt for shell-less reviewers.

**Dispatch configuration:**

Dispatch reviewers per `/review` infrastructure and `code review` role definitions.

The live implementation config is the only routing source. Apply its reviewer route to all three
roles. `validation.yaml.review_config` remains unchanged and is never consulted here.

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
            execution_class: native | external
            effort: inherit | <configured-peer-effort>
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
| Correctness  | FAIL   | fail (gpt)            | —            | —          |
| Style        | PASS   | —                     | —            | pass       |
| Performance  | PASS   | pass                  | pass         | —          |
| Security     | FAIL   | fail (opus, gemini)   | —            | —          |
| Architecture | PASS   | —                     | pass         | —          |
```

`—` = not in scope for this role. On failure, parenthetical = which harness(es) failed.

### 6. Apply Review Feedback

**If Critical/High issues found:**
1. Reload the implementer route and create a mutating `incomplete_stages` marker per fix task
2. Dispatch fix agent(s)
3. Save valid fix reports, verify fixes with targeted review, then clear their markers
4. Update review.yaml with resolution
5. Only proceed when issues resolved; preserve failed fix markers and partial edits

Set the cursor to `fix` around mutating fixes and `targeted_review` around their read-only gate.
Persist targeted-review agent/report states. A failed targeted review returns to `fix: pending`;
a clean result advances to the next batch or final review.

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
     implementation_config:
       path: ./scopes/<state>/<scope>/config.yaml
       epoch_id: <current-epoch-id>
     phase_cursor:
       batch: <N+1>
       phase: tester
       status: pending
       tasks: [...]
       updated_at: <ISO_TIMESTAMP>
     incomplete_stages: []
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

After ALL batches complete, reload `config.yaml.routing.reviewer` and dispatch the final review
directly. Do **not** invoke standalone `/review --final`: that route owns its own
`--reviewers`/`validation.yaml.review_config`/interactive selection and must not replace the live
implementation route. Use the configured reviewer aliases and effort unchanged:

Before dispatch, materialize the complete implementation diff, scope requirements and acceptance
criteria, task statuses, prior batch/deferred review history, and exact reviewer report schema.
Embed them in every role prompt; workdir and git/gestalt commands are optional additions for
shell-capable reviewers.

Set `phase_cursor` to `final_review: in_progress`, with General/Architecture/Compliance report
states and directories, before dispatch. Preserve completed roles across interruption. After all
roles pass, write `final_review: completed`, then `phase: complete, status: completed`.

```
outdir=$(peer path {scope} final-review-{role} --run {run})
Per role (General / Architecture / Compliance), in one message:
  Codex native delegation(role=reviewer, prompt={role_prompt})     # codex-native, if configured
  Task(subagent_type="reviewer", model={native_alias}, prompt={role_prompt})  # opus/sonnet
  peer -C {workdir} -d {outdir} --agent reviewer \                 # externals only
    --peers {external_aliases} --effort {reviewer_effort} \
    --prompt-file {outdir}/prompt.md
```

Write each complete materialized role prompt to the shown `prompt.md` before dispatch; do not pass
it positionally.

Require at least one success from each execution class configured for every role. Record the
aliases and effort actually used in `review.yaml.final_review`; never prompt for a second reviewer
selection. An all-native `codex-native` default performs no peer call.

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
  reviewer_effort: <configured-peer-effort-or-inherit>
  native_effort: inherit
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

| Role | Native Task subagent_type | Skill |
|------|---------------------------|-------|
| Tester | tester | test |
| Implementer | implementer | implement |
| General Reviewer | reviewer | code review |
| Architecture Reviewer | reviewer | gestalt |
| Compliance Reviewer | reviewer | loqui |

On Codex, `codex-native` uses native delegation and Claude-family roles use `opus-cli`/`sonnet-cli`
through peer. On Claude, `opus`/`sonnet` use the table's Task type and GPT-family roles use
registered Codex aliases through peer. External aliases use
`peer --agent tester|implementer|reviewer`; peer loads the matching agent contract. Store reports
under `.peer/<scope>/<run>/<stage>/` as defined in `reference/configuration.md`.

---

## Quality Gates

| Gate | When | Action if Failed |
|------|------|------------------|
| Pre-impl gate | Before any dispatch | Block if Initiative gates failed |
| RED verification | After Phase A | Structural: `failure_output` non-empty, shows failures (not errors), fails because feature missing |
| **Test review** | **After Phase A, before Phase B** | **Triage findings, re-dispatch tester(s) with the verified ones; converge in one round** |
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
- Bypass the configured agent alias for any phase
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
- Continue collecting available reports, but do not pass until every configured execution class has a success
- Note partial results in output
- Pause for deliberate redispatch when the minimum is not met

---

## Example Workflow

```
[Load scope, create TodoWrite, checkout branch]

Batch 1: Task 1 (single task; example config: opus + gpt + gemini reviewers)
├── Phase A: Dispatch tester
│   └── Tester: Wrote 3 tests, all failing (RED)
├── Phase A.5: Dispatch configured host-native + external routes
│   ├── opus: Clean
│   ├── gpt: Clean
│   └── gemini: Clean — no oracle mirroring or tautologies
├── Phase B: Dispatch implementer + tester report
│   └── Implementer: Made tests pass (GREEN)
├── Phase C: Dispatch reviewers (3 in parallel)
│   ├── opus: approved, no issues
│   ├── gpt: approved, 1 minor issue
│   └── gemini: approved, no issues
├── Synthesize: 1 minor issue (note for later)
└── Commit: feat(cache): add caching layer

Batch 2: Tasks 2, 3, 4 (parallel batch — independent, different files)
├── Phase A: Dispatch 3 testers (single message)
│   └── All testers complete with failing tests
├── Phase A.5: Dispatch configured reviewers in parallel (all 3 test files)
│   ├── Synthesized: Task 2 tests — oracle mirroring detected (flagged by gpt)
│   ├── Re-dispatch Task 2 tester with finding
│   └── Task 2 re-tester: Clean on second attempt
├── Phase B: Dispatch 3 implementers (single message)
│   └── All implementers complete, tests passing
├── Phase C: Dispatch reviewers (3 in parallel)
│   ├── opus: changes_requested, 1 critical
│   ├── gpt: changes_requested, 1 critical (same issue)
│   └── gemini: approved
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
