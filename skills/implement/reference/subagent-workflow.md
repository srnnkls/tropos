# Subagent Workflow Details

## Task Batching

Before dispatching, analyze `dependencies.yaml` for execution batches:

1. Parse task dependency graph
2. Identify `[P]` markers (parallelizable within same phase)
3. Group consecutive `[P]` tasks that modify different files
4. Non-`[P]` tasks form single-task batches
5. Phase boundaries force batch breaks

## Three-Phase Pipeline

**Each batch executes three mandatory phases:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase A: TESTERS                                               │
│  ├── Writes failing tests (RED)                                 │
│  └── Reports test paths + failure output                        │
│                          ↓                                      │
│  Phase B: IMPLEMENTERS                                          │
│  ├── Receives tester's report                                   │
│  ├── Makes tests pass (GREEN)                                   │
│  └── Reports impl files + pass output                           │
│                          ↓                                      │
│  Phase C: REVIEWERS                                             │
│  ├── Reviews ALL changes from batch                             │
│  ├── Checks against spec requirements                           │
│  └── Reports issues by severity                                 │
└─────────────────────────────────────────────────────────────────┘
```

**CRITICAL:** All three phases are mandatory. A batch is not complete until reviewers finish.

---

## Tester Dispatch Template

```yaml
Task:
  subagent_type: general
  description: "Write tests for Task N: [task name]"
  prompt: |
    You are writing failing tests for Task N from [spec-file].

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
    4. Run tests to verify RED state

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

Wait for ALL testers to complete before dispatching implementers.

---

## Implementer Dispatch Template

**PRECONDITION:** Tester for this task completed with `status: success`. The tester_report YAML below is REQUIRED — if missing, dispatch the tester first.

```yaml
Task:
  subagent_type: general
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N from [spec-file].

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

## Reviewer Dispatch

**CRITICAL:** Reviewers are mandatory. Every batch gets reviewed. Three roles, multiple harnesses.

For reviewer dispatch templates, see `code` review SKILL.md Step 4 (role prompts) and `/review` reference (harness dispatch):
- `/review` [reference/harnesses.md](../../review/reference/harnesses.md) — dispatch templates
- `/review` [reference/models.md](../../review/reference/models.md) — available models

Configuration from `validation.yaml` `review_config`.

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
Load Spec + dependencies.yaml
    |
    v
Build Execution Batches
    |
    v
[For each batch]
    |
    +--> Single task?
    |         |
    |    YES: Phase A: Dispatch 1 tester (opus)
    |         Phase B: Dispatch 1 implementer (opus)
    |         Phase C: Dispatch reviewers (see /review)
    |         |
    |    NO (parallel [P] tasks):
    |         Phase A: Dispatch N testers (single message)
    |         Phase B: Dispatch N implementers (single message)
    |         Phase C: Dispatch reviewers (see /review)
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
3. **All three roles mandatory** - Every batch gets General + Architecture + Compliance review
4. **YAML reports** - Structured handoff between phases
5. **Single message dispatch** - All role × harness combinations in one message
6. **Fresh context** - Each subagent starts clean
7. **Track progress** - Update TodoWrite after each phase
8. **Configure harnesses** - Set OpenCode models in validation.yaml (applied to ALL roles)
9. **Minimize subagent output** - Subagent final messages get embedded into parent context (duplicated in `.output` and `.result`). Every extra token directly inflates parent context. Subagents must return ONLY the YAML report — no prose, no explanation.
