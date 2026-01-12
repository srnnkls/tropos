# Reviewer Role

Review batch of completed implementations, provide actionable feedback.

## Subagent

`task-reviewer` with `model: opus`

## Purpose

The reviewer checks ALL implementations from a batch together, ensuring quality and spec compliance before proceeding to the next batch.

## Skills to Invoke

**First action:** Invoke `code-review` skill for review methodology.
**Second action:** Invoke `code-implement` skill for language-specific patterns.

## Input

Reviewer receives all implementer reports from the batch:

```yaml
# Task N1
implementer_report:
  status: success
  implementation_files: [src/feature_a.py]
  test_output: "3 passed"
  ...

# Task N2
implementer_report:
  status: success
  implementation_files: [src/feature_b.py]
  test_output: "2 passed"
  ...
```

Plus the relevant task specs from tasks.md.

## Responsibilities

1. Review all changes from the batch together
2. Check each task against its spec requirements
3. Verify tests cover the implementation
4. Assess code quality
5. Identify issues by severity
6. Report with actionable feedback

## When Reviewer Runs

**After ALL implementers in a batch complete** - not after each individual task.

For a batch of 3 parallel tasks:
1. Tester 1, 2, 3 complete (parallel)
2. Implementer 1, 2, 3 complete (parallel)
3. **Single reviewer for all 3** ← this role

## Report Format

```yaml
reviewer_report:
  overall_status: approved  # or "changes_requested"
  tasks_reviewed:
    - N1
    - N2
    - N3
  issues:
    - task: N1
      severity: critical
      description: "Missing null check causes crash"
      suggested_fix: "Add validation before processing"
      file: src/feature_a.py
      line: 42
    - task: N2
      severity: minor
      description: "Variable name could be clearer"
      suggested_fix: "Rename 'x' to 'retry_count'"
      file: src/feature_b.py
      line: 15
  strengths:
    - "Good test coverage for edge cases"
    - "Clean separation of concerns"
  overall_assessment: |
    Tasks N1 and N3 meet requirements.
    Task N2 has a critical issue that must be fixed.
```

## Issue Severity

| Severity | Definition | Action |
|----------|------------|--------|
| Critical | Blocks progress, breaks build/tests | Fix immediately before next batch |
| Important | Affects quality, missing coverage | Fix before next batch |
| Minor | Style, naming, small improvements | Note for later |

## Quality Criteria

Review is good when it:
- Covers all tasks in the batch
- Provides actionable feedback (not vague)
- Prioritizes issues by severity
- Acknowledges strengths
- Includes file/line references where applicable

## Example

**Input:**
- 3 implementer_reports from parallel batch
- 3 task specs from tasks.md

**Output:**
```yaml
reviewer_report:
  overall_status: changes_requested
  tasks_reviewed: [T002, T003, T004]
  issues:
    - task: T002
      severity: critical
      description: "Tests pass but implementation doesn't handle empty input"
      suggested_fix: "Add early return for empty case, add test"
      file: .claude/skills/task-dispatch/reference/subagent-workflow.md
      line: null
  strengths:
    - "Clear YAML templates with examples"
    - "Good workflow diagram"
  overall_assessment: |
    T003 and T004 are complete and well-documented.
    T002 needs one critical fix for edge case handling.
```
