# Reviewer Role

Review batch of completed implementations, provide actionable feedback.

## Reviewers

**Multiple reviewers in parallel:**
- 1 native Claude reviewer: `task-reviewer` with `model: opus`
- 2 opencode reviewers: configured in `validation.yaml` during spec creation

## Purpose

Reviewers check ALL implementations from a batch together, ensuring quality and spec compliance before proceeding to the next batch.

**CRITICAL:** Dispatch all reviewers in the same message for true parallelism.

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

## Dispatch Configuration

**Native Claude reviewer (Task tool):**
```python
Task(
  subagent_type="task-reviewer",
  model="opus",
  prompt=review_prompt
)
```

**OpenCode reviewers (Bash tool, background):**
```bash
timeout 300 opencode run --model "{MODEL}" "{review_prompt}"
```

Models are configured in `validation.yaml` under `review_config.reviewers`.

## When Reviewers Run

**After ALL implementers in a batch complete** - not after each individual task.

For a batch of 3 parallel tasks:
1. Tester 1, 2, 3 complete (parallel)
2. Implementer 1, 2, 3 complete (parallel)
3. **Multiple reviewers for all 3** (native + 2 opencode, parallel) ← these roles

## Report Format

Each reviewer produces a YAML report:

```yaml
reviewer_report:
  reviewer: claude-opus  # or opencode-gpt5.2-pro, opencode-gemini3-pro, etc.
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

## Synthesizing Multiple Reviews

After all reviewers complete:

1. **Parse reports** - Extract YAML from all reviewer outputs
2. **Merge issues:**
   - Deduplicate by description similarity
   - Combine issues flagged by multiple reviewers (higher confidence)
   - Note which reviewer(s) found each issue
3. **Aggregate severity:**
   - Issue severity is the HIGHEST across all reviewers
   - Critical by any reviewer = Critical overall
4. **Present unified feedback:**
   - Group issues by severity
   - Show which reviewers found each issue
   - Prioritize issues found by multiple reviewers

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

**Individual Reviewer Outputs:**

Claude Opus:
```yaml
reviewer_report:
  reviewer: claude-opus
  overall_status: changes_requested
  tasks_reviewed: [T002, T003, T004]
  issues:
    - task: T002
      severity: critical
      description: "Tests pass but implementation doesn't handle empty input"
      suggested_fix: "Add early return for empty case, add test"
      file: src/feature.py
      line: 42
```

GPT-5.2 Pro:
```yaml
reviewer_report:
  reviewer: opencode-gpt5.2-pro
  overall_status: changes_requested
  tasks_reviewed: [T002, T003, T004]
  issues:
    - task: T002
      severity: critical
      description: "Missing validation for empty input parameter"
      suggested_fix: "Add parameter validation"
      file: src/feature.py
      line: 42
    - task: T003
      severity: minor
      description: "Consider more descriptive variable name"
      suggested_fix: "Rename 'x' to 'config_value'"
```

**Synthesized Output:**
```
## Critical Issues (2 reviewers agree on T002)
- [C1] Missing empty input handling (T002)
  Found by: claude-opus, opencode-gpt5.2-pro
  File: src/feature.py:42
  Fix: Add early return for empty case with validation

## Minor Issues
- [M1] Variable naming in T003
  Found by: opencode-gpt5.2-pro
  Fix: Rename 'x' to 'config_value'
```
