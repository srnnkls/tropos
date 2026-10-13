# Test Quality Audit

Audit named or changed tests for reachable failure modes that let a broken implementation pass.

## Target

Use `$TARGET` when supplied; otherwise only test files changed in the current diff. With neither, report that no bounded target was supplied. Never enumerate the whole test tree.

## Finding Bar

Apply the canonical [finding bar](../reference/finding-bar.md).

## Failure Modes

Apply [the canonical test failure modes](../../test/reference/failure-modes.md) and the listed `review.tests` providers ([review slots](../SKILL.md#slots)).

## Workflow

1. Read the requirements and named test files.
2. For each candidate, state a plausible wrong implementation and whether the test rejects it.
3. Report only candidates that clear the finding bar.
4. Stop after one pass over the named tests.

## Output

```yaml
test_audit:
  target: [path/to/test_file]
  findings:
    - file: path/to/test_file
      test: test_name
      failure_mode: "Exact heading from the canonical test failure modes"
      trigger: "Concrete reachable state"
      wrong_outcome: "Broken implementation passes"
      fix_direction: "Sharpen the existing assertion"
```

Return an empty `findings` list when no candidate clears the bar.
