# Subagent Workflow Details

## Task Batching

Before dispatching, analyze `dependencies.yaml` for execution batches:

1. Parse task dependency graph
2. Identify `[P]` markers (parallelizable within same phase)
3. Group consecutive `[P]` tasks that modify different files
4. Non-`[P]` tasks form single-task batches
5. Phase boundaries force batch breaks

## Four-Phase Pipeline

**Each batch executes four mandatory phases:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase A: TESTERS                                               │
│  ├── Writes failing tests (RED)                                 │
│  └── Reports test paths + failure output                        │
│                          ↓                                      │
│  Phase A.5: TEST REVIEW (Claude + Codex × N in parallel)        │
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

---

## Tester Dispatch Template

```yaml
Task:
  subagent_type: task-tester
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
Dispatch ALL testers in a SINGLE message:

```yaml
# Single message with multiple Task tool calls
Task (task-tester): "Write tests for Task N1" ...
Task (task-tester): "Write tests for Task N2" ...
Task (task-tester): "Write tests for Task N3" ...
```

Wait for ALL testers to complete before dispatching Phase A.5.

---

## Test Review Dispatch Template (Phase A.5)

**PRECONDITION:** All Phase A testers completed with `status: success` and RED verified.

Collect all test file paths from every `tester_report` in the batch, then dispatch a Claude `Task` **plus one `peer`** (which fans out to all configured external reviewers) — same shape as Phase C; never shell out to codex/gemini directly. Test review must be multi-harness for the same reason code review is: fresh-perspective models catch quality issues a single harness misses.

**Resolve reviewer config (in order):**
1. `validation.yaml` `review_config` for the active scope
2. Defaults from `/review` SKILL.md — `claude-opus` + `codex-gpt5.5` + `gemini-3.5-flash`
3. Never dispatch Claude alone — external shell-outs (Codex/Gemini) are mandatory whenever installed

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
  reviewer_id: [e.g. claude-opus | codex-gpt5.5 | gemini-3.5-flash]
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

**Dispatch (single message):** Claude `Task` + one `peer` for the external harnesses.

```
# Claude harness (required) — agent-native
Task(subagent_type="task-reviewer", description="Test quality review — claude-opus",
     prompt={shared_prompt with reviewer_id: claude-opus})

# External harnesses — peer fans out + watches; see the `peer` skill
Bash(run_in_background=true):
  peer -d {outdir} --effort high "{shared_prompt}"
```

Wait for the Claude Task and `peer`; read each `ok` row of `peer`'s manifest.
Dispatch contract, flags, exit codes: **[peer skill](../../peer/SKILL.md)**.

**Synthesis for Phase A.5:**
- Merge `findings` across all harnesses by `(test_file, test_name)`
- A test is flagged if **any** harness reports `issues_found` for it
- Dedup findings that describe the same anti-pattern on the same test
- Timeout handling: continue with completed reviews; note partial results; never proceed with zero reviews

**Gate logic after test_review_reports merged:**

- `status: clean` → proceed to Phase B
- `status: issues_found` → for each affected test file:
  1. Re-dispatch its tester with the `findings` for that file as explicit feedback
  2. Wait for re-dispatched tester(s) to complete
  3. Run Phase A.5 again on the re-written tests
  4. Repeat until all test files are clean
- Only dispatch Phase B once ALL test files pass the gate

**INVARIANT:** Never dispatch an implementer with tests that have `status: issues_found` in their test review.

---

## Implementer Dispatch Template

**PRECONDITION:** Tester for this task completed with `status: success` AND the batch's `test_review_report` is `status: clean`. If either is missing, complete Phase A and Phase A.5 first.

```yaml
Task:
  subagent_type: task-implementer
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
    3. If requirements are ambiguous, use AskUserQuestion
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
      clarifications:
        - question: [if used AskUserQuestion]
          answer: [user's response]
      blocked_reason: null  # or explanation if status=blocked
    ```
```

**For parallel batch (N tasks):**
Dispatch ALL implementers in a SINGLE message, each with its corresponding tester report:

```yaml
# Single message with multiple Task tool calls
Task (task-implementer): "Implement Task N1" + tester_1_report
Task (task-implementer): "Implement Task N2" + tester_2_report
Task (task-implementer): "Implement Task N3" + tester_3_report
```

Wait for ALL implementers to complete before dispatching reviewers.

---

## Reviewer Dispatch (Phase C)

**CRITICAL:** Reviewers are mandatory. Every batch gets reviewed. Three roles × all configured harnesses, all in a SINGLE message.

**Resolve reviewer config (in order):**
1. Explicit `--reviewers` flag if caller passed one (see `/review` SKILL.md "Reviewer Selection")
2. `validation.yaml` `review_config` for the active scope
3. Defaults: `claude-opus` + `codex-gpt5.5` (codex, reasoning effort `high`) + `gemini-3.5-flash` (gemini)
4. Never dispatch with zero external reviewers when Codex/Gemini are installed — external shell-outs are mandatory for cross-model coverage

**Dispatch (single message):** per role, a Claude `Task` + one `peer` that fans the
role prompt out to every configured external reviewer.

```
# Per role (General / Architecture / Compliance):
Task(subagent_type="task-reviewer", description="{role} review — claude-opus",
     prompt={role_prompt with reviewer_id: {role}-claude-opus})
Bash(run_in_background=true):
  peer -d {role_outdir} --reviewers {external_aliases} --effort high "{role_prompt}"
```

`peer` parallelises the external harnesses itself (one report file per reviewer,
each with its own idle-stall watchdog) and prints a manifest — the agent no longer
manages N background jobs. Read each `ok` row's report; skip stalled/error rows.
Dispatch contract, flags, exit codes, `peer list`: **[peer skill](../../peer/SKILL.md)**.

Role prompts live in `code` review SKILL.md Step 4 (General / Architecture / Compliance).
Then synthesize per `/review` [reference/synthesis.md](../../review/reference/synthesis.md).

---

## Review Synthesis

Synthesize per `/review` [reference/synthesis.md](../../review/reference/synthesis.md): parse reports, group by role, merge issues, aggregate gates and severity, present gate summary table and issues by severity.

---

## Fix Subagent Template

When review finds Critical/High issues:

```yaml
Task:
  subagent_type: task-implementer
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

After fixes, dispatch targeted review (can be single Claude reviewer for speed).

---

## Workflow Diagram (Three-Phase Pipeline)

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
    |    YES: Phase A:   Dispatch 1 tester (opus)
    |         Phase A.5: Dispatch reviewers (Claude + Codex × N) → gate
    |         Phase B:   Dispatch 1 implementer (opus)
    |         Phase C:   Dispatch reviewers (Claude + Codex × N, see /review)
    |         |
    |    NO (parallel [P] tasks):
    |         Phase A:   Dispatch N testers (single message)
    |         Phase A.5: Dispatch reviewers (Claude + Codex × N, all test files) → gate
    |         Phase B:   Dispatch N implementers (single message)
    |         Phase C:   Dispatch reviewers (Claude + Codex × N, see /review)
    |         |
    |         v
    +--> Synthesize Reviews (see /review reference/synthesis.md)
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
Final Review (see /review)
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
  subagent_type: task-tester
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

External reviewers run through `peer`, which owns the idle-stall watchdog, retry-once,
and skip. Read `peer`'s per-reviewer manifest status; continue with completed reviews
(minimum 1 Claude required), note any skipped reviewer as partial results, and synthesize
what landed. Details: **[peer skill](../../peer/SKILL.md)**. Never block the pipeline on an
external harness.

---

## Best Practices

1. **Specialized subagent types** - Use `task-tester`, `task-implementer`, `task-reviewer` for Claude native Task calls; external reviewers (codex/gemini) go through one `peer` per role, never raw shell-outs
2. **Tester first** - Implementer must receive failing tests
3. **Test review gate** - Every batch's tests pass Phase A.5 before implementers are dispatched
4. **All three code-review roles mandatory** - Every batch gets General + Architecture + Compliance review
5. **YAML reports** - Structured handoff between phases
6. **Single message dispatch** - Per role, the Claude `Task` + the `peer` in one message
7. **Fresh context** - Each subagent starts clean
8. **Track progress** - Update TodoWrite after each phase
9. **Configure harnesses** - Set external reviewers (codex/gemini) in validation.yaml `review_config` (applied to ALL roles); models per `peer list`
10. **Minimize subagent output** - Subagent final messages get embedded into parent context (duplicated in `.output` and `.result`). Every extra token directly inflates parent context. Subagents must return ONLY the YAML report — no prose, no explanation.
