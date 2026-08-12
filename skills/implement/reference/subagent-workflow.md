# Subagent Workflow Details

## Task Batching

See `operations/execute.md` Step 3 and `reference/parallel-detection.md` for the full algorithm.

## Four-Phase Pipeline

**Each batch executes four mandatory phases:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase A: TESTERS                                               │
│  ├── Writes failing tests (RED)                                 │
│  └── Reports test paths + failure output                        │
│                          ↓                                      │
│  Phase A.5: TEST REVIEW (native + external reviewers)           │
│  ├── Reviews all Phase A test files                             │
│  ├── Checks: oracle mirroring, mock tautologies,                │
│  │   framework tests, trivial assertions                        │
│  └── Gate: clean → Phase B | issues → re-dispatch tester(s)     │
│                          ↓                                      │
│  Phase B: IMPLEMENTERS                                          │
│  ├── Receives tester's report (test-review-cleared)             │
│  ├── Makes tests pass (GREEN)                                   │
│  └── Reports impl files + pass output                           │
│                          ↓                                      │
│  Phase C: REVIEWERS                                             │
│  ├── Reviews ALL changes from batch                             │
│  ├── Checks against scope requirements                          │
│  └── Reports issues by severity                                 │
└─────────────────────────────────────────────────────────────────┘
```

**CRITICAL:** All four phases are mandatory. A batch is not complete until all phases finish.

## Role Routing

Resolve and reload routing per [configuration.md](configuration.md) immediately before each
phase. Use the same role prompt and YAML report schema regardless of harness:

```text
codex-native: Codex native delegation(role=<role>, prompt=<role-prompt>)
              # inherit current session model/reasoning; never call peer
explicit native: Task(subagent_type="<role>", model="<configured-alias>", prompt=<role-prompt>)
external: write <outdir>/prompt.md, then:
          peer -C <workdir> -d <outdir> --agent <role> --peers <configured-aliases> \
            --effort <configured-effort> --prompt-file <outdir>/prompt.md
```

Tester and implementer routes are singular. Dispatch one external peer call per task so reports
and partial mutations remain attributable. Reviewer routes may be all-native, all-external, or
mixed: dispatch `codex-native` through Codex delegation, explicit native aliases as Tasks, and one
peer fan-out only when external aliases are configured. A gate needs one success from each
execution class actually configured.

Before any native or external tester, implementer, or fix dispatch, persist that task's
`checkpoint.incomplete_stages` marker with its assigned `.peer` report directory and baseline git
evidence. Store the returned normalized report there and clear the marker only after the role's
gate passes. Keep and update it on failure or interruption; see
[checkpoint-format.md](checkpoint-format.md).

---

## Tester Dispatch Template

```yaml
Task:
  subagent_type: tester
  model: {tester_agent}  # explicit native route only; omit for codex-native delegation
  description: "Write tests for Task N: [task name]"
  prompt: |
    You are writing failing tests for Task N from [scope-file].

    ## TDD Methodology
    Read `./skills/test/SKILL.md` for TDD methodology — follow the Iron Law.
    Follow RED-GREEN-REFACTOR: write failing tests first, then minimal code to pass.

    ## Language Conventions
    Read `./skills/loqui/reference/loqui/languages/{lang}/README.md` for language-specific test conventions (NOT for writing implementation code — that is the implementer's job).

    **Task requirements:**
    [paste task from tasks.yaml including test_hints]

    **Your job:**
    1. Read the task requirements and test_hints
    2. Write tests that cover all specified behaviors
    3. Tests must FAIL (features not implemented yet)
    4. Run tests — verify RED state (MANDATORY, never skip):
       - Tests fail (not error from typos or missing imports)
       - Failure message matches expected behavior
       - Tests fail because the feature is missing
       - If tests pass immediately → you're testing existing behavior, fix the test
    5. `failure_output` MUST contain actual test failure output proving RED state

    **Work from:** [directory]

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    tester_report:
      status: success  # or "gap" if cannot write tests
      test_files:
        - path: [test file path]
          tests: [list of test names]
      failure_output: |
        [last 20 lines of test failure output only]
      gap_reason: null  # or explanation if status=gap
    ```
```

**For parallel batch (N tasks):**
Dispatch ALL testers in a SINGLE message. Use Codex native delegation for `codex-native`, Task
calls for explicit native aliases, or background `peer --agent tester` calls for external aliases:

```yaml
# Single message with multiple Task tool calls
Task (tester): "Write tests for Task N1" ...
Task (tester): "Write tests for Task N2" ...
Task (tester): "Write tests for Task N3" ...
```

Wait for ALL testers to complete before dispatching Phase A.5.

For an external tester, use
`.peer/<scope-or-direct>/<epoch>/<batch>/tester/<task-id>/` as its output directory. If peer fails,
stalls, or returns no valid `tester_report`, preserve partial edits, capture worktree status/diff,
mark Phase A incomplete, and pause. Do not retry, roll back, or proceed.

---

## Test Review Dispatch Template (Phase A.5)

**PRECONDITION:** All Phase A testers completed with `status: success` and RED verified.

Collect all test file paths from every `tester_report` in the batch, reload the live reviewer
route, then dispatch configured native reviewers through their host-native mechanisms plus one
peer fan-out only when external reviewers are configured. Never send `codex-native` to peer, invoke
an external harness directly, or use
`validation.yaml.review_config` for this gate.

**Shared prompt (reused across all harnesses):**

```
Review these test files for quality issues before implementation proceeds.

Read `./skills/review/operations/test-audit.md` for the four anti-patterns to check.

**Test files to review:**
[list each path from tester_reports[*].test_files[*].path]

**Expected behavior each test suite verifies:**
[paste task description for each corresponding tester]

**Your job:**
1. Read each test file
2. Apply the four anti-pattern checks from test-audit.md
3. For each issue found: name the test, name the anti-pattern, one-line reason

**OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.

**Report in YAML format:**
```yaml
test_review_report:
  reviewer_id: {reviewer-id}  # configured native or external alias
  status: clean  # or "issues_found"
  findings:
    - test_file: [path]
      test_name: [function name]
      anti_pattern: oracle_mirroring | mock_tautology | framework_test | trivial_assertion
      reason: "[one-line reason]"
      fix_direction: "[what the tester should do instead]"
  summary: "[one sentence — or 'No issues found']"
```
```

**Dispatch (single message):** configured host-native dispatches plus one peer fan-out when an
external class is configured.

```
# Codex native delegation when codex-native is configured (inherits session settings)
Codex native delegation(role=reviewer, prompt={shared_prompt})

# One Task per configured explicit native alias (opus/sonnet)
Task(subagent_type="reviewer", model={native_alias},
     description="Test quality review — {native_alias}",
     prompt={shared_prompt with reviewer_id: {native_alias}})

# All configured external aliases in one reviewer fan-out; omit when none configured
Bash(run_in_background=true):
  peer -C {workdir} -d {outdir} --agent reviewer --peers {external_aliases} \
    --effort {reviewer_effort} --prompt-file {outdir}/prompt.md
```

Use `.peer/<scope-or-direct>/<epoch>/<batch>/test-review/` for `{outdir}`. Wait for all Tasks and
`peer` when external aliases were configured; read each `ok` row of peer's manifest. The gate
requires one valid report from each execution class actually configured.
Write the complete shared prompt to `{outdir}/prompt.md` before dispatch.
Dispatch contract, flags, exit codes: **[peer skill](../../peer/SKILL.md)**.

**Synthesis for Phase A.5:**
- Merge `findings` across all harnesses by `(test_file, test_name)`
- Dedup findings that describe the same anti-pattern on the same test
- Triage the merged findings per [review synthesis](../../review/reference/synthesis.md). A
  test is flagged only when a finding names a concrete failure mode against the actual test:
  a probe that passes when it should not, an oracle that cannot fire, a false failure for a
  design-conformant implementation. `issues_found` alone does not flag a test, and the number
  of harnesses reporting it is agreement rather than validity
- Record findings that do not clear triage as residual on the report; they never flag a test
- Timeout handling: continue with completed reviews; note partial results; never proceed with zero reviews

**Gate logic after test_review_reports merged:**

- `status: clean` → proceed to Phase B
- `status: issues_found` → for each affected test file:
  1. Re-dispatch its tester with the triaged `findings` for that file as explicit feedback
  2. Wait for re-dispatched tester(s) to complete
  3. Run Phase A.5 again on the re-written tests
  4. Converge in one round. A further round requires a finding that names a new verified
     failure mode; findings that only narrow or restate a prior round are residual, and the
     file is clean. Report every round beyond the first with what forced it
- Only dispatch Phase B once ALL test files pass the gate

**INVARIANT:** Never dispatch an implementer with tests that have `status: issues_found` in their test review.

---

## Implementer Dispatch Template

**PRECONDITION:** Tester for this task completed with `status: success` AND the batch's `test_review_report` is `status: clean`. If either is missing, complete Phase A and Phase A.5 first.

```yaml
Task:
  subagent_type: implementer
  model: {implementer_agent}  # explicit native route only; omit for codex-native delegation
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N from [scope-file].

    ## Language Guidelines
    Read `./skills/loqui/reference/loqui/languages/{lang}/README.md` for language-specific conventions.

    **Tests written by tester:**
    ```yaml
    [paste tester_report YAML]
    ```

    **Your job:**
    1. Run the tests to see current failures
    2. Write minimal code to make tests pass (GREEN)
    3. If requirements are ambiguous, report `status: blocked` for the orchestrator to resolve
    4. Refactor while keeping tests green

    **Work from:** [directory]

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    implementer_report:
      status: success  # or "blocked" if cannot proceed
      implementation_files:
        - path: [impl file path]
      test_output: |
        [last 20 lines of test output only]
      blocked_reason: null  # or explanation if status=blocked
    ```
```

**For parallel batch (N tasks):**
Dispatch ALL implementers in a SINGLE message, each with its corresponding tester report. Use
Codex native delegation for `codex-native`, Task calls for explicit native aliases, or background
`peer --agent implementer` calls for an external route:

```yaml
# Single message with multiple Task tool calls
Task (implementer): "Implement Task N1" + tester_1_report
Task (implementer): "Implement Task N2" + tester_2_report
Task (implementer): "Implement Task N3" + tester_3_report
```

Wait for ALL implementers to complete before dispatching reviewers.

For an external implementer, use
`.peer/<scope-or-direct>/<epoch>/<batch>/implementer/<task-id>/` as its output directory. If peer
fails, stalls, or returns no valid report, preserve partial edits, capture worktree status/diff,
mark Phase B incomplete, and pause. Do not retry, roll back, or proceed.

---

## Reviewer Dispatch (Phase C)

**CRITICAL:** Reviewers are mandatory. Every batch gets reviewed. Before each of the three roles,
reload the live reviewer route. Each role dispatches `codex-native` through Codex delegation,
explicit native aliases through Tasks, and a peer fan-out only if external aliases are configured.

```
# Per role (General / Architecture / Compliance), one per native alias:
Codex native delegation(role=reviewer, prompt={role_prompt})  # codex-native only
Task(subagent_type="reviewer", model={native_alias}, description="{role} review — {native_alias}",
     prompt={role_prompt with reviewer_id: {role}-{reviewer-id}})
Bash(run_in_background=true):
  peer -C {workdir} -d {role_outdir} --agent reviewer --peers {external_aliases} \
    --effort {reviewer_effort} --prompt-file {role_outdir}/prompt.md
```

Write the complete materialized role prompt to `{role_outdir}/prompt.md` before dispatch.

`peer` parallelises the external harnesses itself (one report file per reviewer,
each with its own idle-stall watchdog) and prints a manifest — the agent no longer
manages N background jobs. Read each `ok` row's report; skip stalled/error rows.
Dispatch contract, flags, exit codes, `peer list`: **[peer skill](../../peer/SKILL.md)**.

Role prompts live in `code` review SKILL.md Step 4 (General / Architecture / Compliance).
Then synthesize per `/review` [reference/synthesis.md](../../review/reference/synthesis.md).

Materialize and embed the reviewed diff, applicable requirements, and exact YAML report schema in
every role prompt before dispatch. Do not send a git command as the only review input: shell-less
external reviewers must be able to complete from the prompt. Commands, workdir, structural
analysis, and file paths are optional additions for shell-capable reviewers.

---

## Review Synthesis

Synthesize per `/review` [reference/synthesis.md](../../review/reference/synthesis.md): parse reports, group by role, merge issues, aggregate gates and severity, present gate summary table and issues by severity.

---

## Fix Subagent Template

When review finds Critical/High issues:

```yaml
Task:
  subagent_type: implementer
  model: {implementer_agent}  # explicit native only; omit for codex-native delegation
  description: "Fix issues from batch review"
  prompt: |
    Fix these issues from code review:

    **Issues to fix:**
    ```yaml
    [paste relevant issues from synthesized review]
    ```

    Make targeted fixes only. Don't refactor beyond what's needed.
    Run tests to verify fixes don't break anything.

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    fix_report:
      status: success
      fixes_applied:
        - issue: [description]
          fix: [what you did]
      test_output: |
        [last 20 lines of test output only]
    ```
```

If the configured implementer is external, use `peer --agent implementer` and apply the mutating
failure rule. After fixes, reload reviewer routing and dispatch targeted review with at least one
success from every configured execution class; do not require a class absent from config.

---

## Workflow Diagram (Four-Phase Pipeline)

```
Load Scope + dependencies.yaml
    |
    v
Build Execution Batches
    |
    v
[For each batch]
    |
    +--> Single task?
    |         |
    |    YES: Phase A:   Dispatch 1 configured tester
    |         Phase A.5: Dispatch configured reviewer set → gate
    |         Phase B:   Dispatch 1 configured implementer
    |         Phase C:   Dispatch configured reviewer set from live config
    |         |
    |    NO (multi-task batch):
    |         Phase A:   Dispatch N testers (single message)
    |         Phase A.5: Dispatch configured reviewers (all test files) → gate
    |         Phase B:   Dispatch N implementers (single message)
    |         Phase C:   Dispatch configured reviewers from live config
    |         |
    |         v
    +--> Synthesize Reviews (shared synthesis contract)
    |         |
    |         v
    |    Critical/High Issues? --YES--> Dispatch Fix Subagent(s)
    |         |                              |
    |         NO                             v
    |         |                        Targeted Review
    |         v                              |
    |    Commit Batch <----------------------+
    |         |
    v         v
[Next Batch]
    |
    v
Config-driven Final Review (direct role dispatch)
    |
    v
Done
```

---

## Handling Tester Gaps

If tester reports `status: gap`:

1. Read `gap_reason` from tester's report
2. Consult scope (tasks.yaml, scope.md) for clarification
3. If still unclear, use AskUserQuestion to clarify with user
4. Re-dispatch tester with additional context:

```yaml
Task:
  subagent_type: tester
  model: {tester_agent}  # explicit native only; omit for codex-native delegation
  description: "Write tests for Task N (clarified)"
  prompt: |
    Previous attempt reported gap: [gap_reason]

    **Clarification received:**
    [additional context or user's answer]

    Now write tests with this clarified understanding.
    [rest of tester template]
```

---

## Handling Reviewer Timeouts

External reviewers run through `peer`, which owns reviewer retry/timeout behavior. Read its
per-reviewer manifest and synthesize completed reports, but do not pass a review gate unless at
least one report from every configured execution class succeeded. Note skipped reviewers as
partial results and pause for deliberate redispatch when the configured-class minimum is not met.
Mutating tester/implementer peers
never use reviewer retry behavior; their failures follow the preserve-evidence-and-pause rule.
