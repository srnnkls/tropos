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
│  Phase A.5: TEST REVIEW (Claude + Pi × N in parallel)           │
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
  subagent_type: general
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
Task (general): "Write tests for Task N1" ...
Task (general): "Write tests for Task N2" ...
Task (general): "Write tests for Task N3" ...
```

Wait for ALL testers to complete before dispatching Phase A.5.

---

## Test Review Dispatch Template (Phase A.5)

**PRECONDITION:** All Phase A testers completed with `status: success` and RED verified.

Collect all test file paths from every `tester_report` in the batch, then dispatch **all configured reviewers in parallel** (Claude native + Pi shell-outs — same cartesian dispatch pattern as Phase C). Test review must be multi-harness for the same reason code review is: fresh-perspective models catch quality issues a single harness misses.

**Resolve reviewer config (in order):**
1. `validation.yaml` `review_config` for the active scope
2. Defaults from `/review` SKILL.md — `claude-opus` + `openai-gpt5.5` + `gemini-3.1-pro`, thinking `high`
3. Never dispatch Claude alone — Pi shell-outs are mandatory whenever Pi is installed

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
  reviewer_id: [e.g. claude-opus | pi-gpt5.5 | pi-gemini-3.1-pro]
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

**Dispatch (single message, full cartesian product):**

```
# Claude harness (required)
Task(
  subagent_type="general",
  description="Test quality review — claude-opus",
  prompt={shared_prompt with reviewer_id: claude-opus}
)

# Pi harnesses (one per configured Pi model)
Bash(run_in_background=true):
  timeout 1200 pi --fast -p --model openai-codex/gpt-5.5 --thinking high "{shared_prompt with reviewer_id: pi-gpt5.5}"
Bash(run_in_background=true):
  timeout 1200 pi --fast -p --model google-gemini-cli/gemini-3.1-pro-preview --thinking high "{shared_prompt with reviewer_id: pi-gemini-3.1-pro}"
```

Wait for ALL harnesses to complete (Claude via Task result, Pi via BashOutput on completion).

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
  subagent_type: general
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
Task (general): "Implement Task N1" + tester_1_report
Task (general): "Implement Task N2" + tester_2_report
Task (general): "Implement Task N3" + tester_3_report
```

Wait for ALL implementers to complete before dispatching reviewers.

---

## Reviewer Dispatch (Phase C)

**CRITICAL:** Reviewers are mandatory. Every batch gets reviewed. Three roles × all configured harnesses, all in a SINGLE message.

**Resolve reviewer config (in order):**
1. Explicit `--reviewers` flag if caller passed one (see `/review` SKILL.md "Reviewer Selection")
2. `validation.yaml` `review_config` for the active scope
3. Defaults: `claude-opus` + `openai-gpt5.5` + `gemini-3.1-pro`, thinking `high`
4. Never dispatch with zero Pi reviewers when Pi is installed — Pi shell-outs are mandatory for cross-model coverage

**Dispatch (single message, full cartesian product — roles × harnesses):**

```
# General role
Task(subagent_type="general",
     description="General review — claude-opus",
     prompt={general_prompt with reviewer_id: general-claude-opus})
Bash(run_in_background=true):
  timeout 1200 pi --fast -p --model openai-codex/gpt-5.5 --thinking high "{general_prompt with reviewer_id: general-pi-gpt5.5}"
Bash(run_in_background=true):
  timeout 1200 pi --fast -p --model google-gemini-cli/gemini-3.1-pro-preview --thinking high "{general_prompt with reviewer_id: general-pi-gemini-3.1-pro}"

# Architecture role
Task(subagent_type="general",
     description="Architecture review — claude-opus",
     prompt={architecture_prompt with reviewer_id: architecture-claude-opus})
Bash(run_in_background=true):
  timeout 1200 pi --fast -p --model openai-codex/gpt-5.5 --thinking high "{architecture_prompt with reviewer_id: architecture-pi-gpt5.5}"
Bash(run_in_background=true):
  timeout 1200 pi --fast -p --model google-gemini-cli/gemini-3.1-pro-preview --thinking high "{architecture_prompt with reviewer_id: architecture-pi-gemini-3.1-pro}"

# Compliance role
Task(subagent_type="general",
     description="Compliance review — claude-opus",
     prompt={compliance_prompt with reviewer_id: compliance-claude-opus})
Bash(run_in_background=true):
  timeout 1200 pi --fast -p --model openai-codex/gpt-5.5 --thinking high "{compliance_prompt with reviewer_id: compliance-pi-gpt5.5}"
Bash(run_in_background=true):
  timeout 1200 pi --fast -p --model google-gemini-cli/gemini-3.1-pro-preview --thinking high "{compliance_prompt with reviewer_id: compliance-pi-gemini-3.1-pro}"
```

Role prompts live in `code` review SKILL.md Step 4 (General / Architecture / Compliance). Harness details live in `/review` [reference/harnesses.md](../../review/reference/harnesses.md).

Wait for ALL harnesses to complete (Claude via Task result, Pi via BashOutput). Then synthesize per `/review` [reference/synthesis.md](../../review/reference/synthesis.md).

---

## Review Synthesis

Synthesize per `/review` [reference/synthesis.md](../../review/reference/synthesis.md): parse reports, group by role, merge issues, aggregate gates and severity, present gate summary table and issues by severity.

---

## Fix Subagent Template

When review finds Critical/High issues:

```yaml
Task:
  subagent_type: general
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
    |         Phase A.5: Dispatch reviewers (Claude + Pi × N) → gate
    |         Phase B:   Dispatch 1 implementer (opus)
    |         Phase C:   Dispatch reviewers (Claude + Pi × N, see /review)
    |         |
    |    NO (parallel [P] tasks):
    |         Phase A:   Dispatch N testers (single message)
    |         Phase A.5: Dispatch reviewers (Claude + Pi × N, all test files) → gate
    |         Phase B:   Dispatch N implementers (single message)
    |         Phase C:   Dispatch reviewers (Claude + Pi × N, see /review)
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
  subagent_type: general
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

If OpenCode reviewer times out (> 5 minutes):

1. Continue with completed reviews (minimum 1 required)
2. Add warning to output:
   ```
   Note: [Reviewer] timed out after 5 minutes.
   Results are from available reviewers only.
   ```
3. Proceed with synthesis using available data
4. Consider re-running batch if only 1 reviewer completed

---

## Best Practices

1. **subagent_type: general** - Use `general` for all task subagents
2. **Tester first** - Implementer must receive failing tests
3. **Test review gate** - Every batch's tests pass Phase A.5 before implementers are dispatched
4. **All three code-review roles mandatory** - Every batch gets General + Architecture + Compliance review
5. **YAML reports** - Structured handoff between phases
6. **Single message dispatch** - All role × harness combinations in one message
7. **Fresh context** - Each subagent starts clean
8. **Track progress** - Update TodoWrite after each phase
9. **Configure harnesses** - Set OpenCode models in validation.yaml (applied to ALL roles)
10. **Minimize subagent output** - Subagent final messages get embedded into parent context (duplicated in `.output` and `.result`). Every extra token directly inflates parent context. Subagents must return ONLY the YAML report — no prose, no explanation.
