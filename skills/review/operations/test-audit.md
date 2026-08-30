# Test Quality Audit

Audit named or changed tests for reachable failure modes that can make a broken implementation appear correct.

## Target

Use the explicit `$TARGET` when supplied. Otherwise inspect only test files changed in the current diff. If neither exists, report that no bounded target was supplied; do not enumerate the whole test tree.

## Finding Bar

Apply the canonical [finding bar](../reference/finding-bar.md). This operation supplies only audit targeting and reporting.

## Failure Modes

Read and apply [the canonical test failure modes](../../test/reference/failure-modes.md). Do not copy or paraphrase them here; this operation only supplies audit targeting and reporting.

## Workflow

1. Read the requirements and named test files.
2. For each candidate, state a plausible wrong implementation and determine whether the test rejects it.
3. Report only candidates that clear the shared finding bar.
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
