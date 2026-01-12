# Subagent Workflow Details

## Task Batching

Before dispatching, analyze `dependencies.md` for execution batches:

1. Parse task dependency graph
2. Identify `[P]` markers (parallelizable within same phase)
3. Group consecutive `[P]` tasks that modify different files
4. Non-`[P]` tasks form single-task batches
5. Phase boundaries force batch breaks

## Two-Phase TDD Dispatch

**Per task, execute two phases:**

```
Phase A: TESTER
├── Writes failing tests (RED)
└── Reports test paths + failure output

Phase B: IMPLEMENTER
├── Receives tester's report
├── Makes tests pass (GREEN)
└── Reports impl files + pass output
```

---

## Tester Dispatch Template

```yaml
Task:
  subagent_type: task-tester
  model: opus
  description: "Write tests for Task N: [task name]"
  prompt: |
    You are writing failing tests for Task N from [spec-file].

    **First:** Invoke the `code-test` skill for TDD methodology.
    **Second:** Invoke the `code-implement` skill for language-specific test patterns.

    **Task requirements:**
    [paste task from tasks.md including test_hints]

    **Your job:**
    1. Read the task requirements and test_hints
    2. Write tests that cover all specified behaviors
    3. Tests must FAIL (features not implemented yet)
    4. Run tests to verify RED state

    **Work from:** [directory]

    **Report in YAML format:**
    ```yaml
    tester_report:
      status: success  # or "gap" if cannot write tests
      test_files:
        - path: [test file path]
          tests: [list of test names]
      failure_output: |
        [actual test failure output]
      gap_reason: null  # or explanation if status=gap
    ```
```

**For parallel batch (N tasks):**
Dispatch ALL testers in a SINGLE message:

```yaml
# Single message with multiple Task tool calls
Task (task-tester, opus): "Write tests for Task N1" ...
Task (task-tester, opus): "Write tests for Task N2" ...
Task (task-tester, opus): "Write tests for Task N3" ...
```

Wait for ALL testers to complete before dispatching implementers.

---

## Implementer Dispatch Template

```yaml
Task:
  subagent_type: task-implementer
  model: opus
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N from [spec-file].

    **First:** Invoke the `code-implement` skill for language guidelines.

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

    **Report in YAML format:**
    ```yaml
    implementer_report:
      status: success  # or "blocked" if cannot proceed
      implementation_files:
        - path: [impl file path]
      test_output: |
        [test pass output]
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
Task (task-implementer, opus): "Implement Task N1" + tester_1_report
Task (task-implementer, opus): "Implement Task N2" + tester_2_report
Task (task-implementer, opus): "Implement Task N3" + tester_3_report
```

Wait for ALL implementers to complete before review.

---

## Reviewer Dispatch Template

After ALL implementers in a batch complete, dispatch single reviewer:

```yaml
Task:
  subagent_type: task-reviewer
  model: opus
  description: "Review batch: Tasks N1, N2, N3"
  prompt: |
    Review the changes made for Tasks N1, N2, N3.

    **First:** Invoke the `code-review` skill for review methodology.

    **What was implemented:**
    [paste all implementer_report YAMLs]

    **Spec requirements:**
    [paste relevant tasks from tasks.md]

    **Review against:**
    1. All task requirements met?
    2. Tests cover the implementation?
    3. Code quality acceptable?
    4. Any regressions?

    **Report in YAML format:**
    ```yaml
    reviewer_report:
      overall_status: approved  # or "changes_requested"
      tasks_reviewed: [N1, N2, N3]
      issues:
        - task: N1
          severity: critical|important|minor
          description: [issue]
          suggested_fix: [fix]
      strengths:
        - [positive observation]
    ```
```

---

## Fix Subagent Template

When review finds issues:

```yaml
Task:
  subagent_type: task-implementer
  model: opus
  description: "Fix issues from Task N review"
  prompt: |
    Fix these issues from code review:

    **Issues to fix:**
    ```yaml
    [paste relevant issues from reviewer_report]
    ```

    Make targeted fixes only. Don't refactor beyond what's needed.
    Run tests to verify fixes don't break anything.

    **Report in YAML format:**
    ```yaml
    fix_report:
      status: success
      fixes_applied:
        - issue: [description]
          fix: [what you did]
      test_output: |
        [test output after fixes]
    ```
```

---

## Workflow Diagram (Two-Phase TDD)

```
Load Spec + dependencies.md
    |
    v
Build Execution Batches
    |
    v
[For each batch]
    |
    +--> Single task?
    |         |
    |    YES: Phase A: Dispatch ONE tester (opus)
    |         Wait for tester
    |         Phase B: Dispatch ONE implementer (opus) + tester_report
    |         Wait for implementer
    |         |
    |    NO (parallel [P] tasks):
    |         Phase A: Dispatch N testers (single message)
    |         Wait for ALL testers
    |         Phase B: Dispatch N implementers (single message)
    |         Wait for ALL implementers
    |         |
    |         v
    +--> Dispatch SINGLE reviewer for batch
    |         |
    |         v
    |    Issues Found? --YES--> Dispatch Fix Subagent(s)
    |         |                      |
    |         NO                     |
    |         |                      v
    |         v               Verify Fixes
    |    Mark Batch Complete <-------+
    |         |
    v         v
[Next Batch or Final Review]
```

---

## Handling Tester Gaps

If tester reports `status: gap`:

1. Read `gap_reason` from tester's report
2. Consult spec (tasks.md, spec.md) for clarification
3. If still unclear, use AskUserQuestion to clarify with user
4. Re-dispatch tester with additional context:

```yaml
Task:
  subagent_type: task-tester
  model: opus
  description: "Write tests for Task N (clarified)"
  prompt: |
    Previous attempt reported gap: [gap_reason]

    **Clarification received:**
    [additional context or user's answer]

    Now write tests with this clarified understanding.
    [rest of tester template]
```

---

## Best Practices

1. **Always opus** - Never use sonnet for task subagents
2. **Tester first** - Implementer must receive failing tests
3. **YAML reports** - Structured handoff between phases
4. **Single reviewer** - One review for entire batch
5. **Fresh context** - Each subagent starts clean
6. **Track progress** - Update TodoWrite after each phase
