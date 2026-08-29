---
name: test
description: Bounded RED-GREEN-REFACTOR methodology. Use when the user explicitly requests TDD or tests, or when the implement pipeline invokes it.
metadata:
  type: generic
---

# Bounded Test-Driven Development

Write the smallest discriminating check, watch it fail for the requested missing behavior, add minimal production code, then watch it pass.

## Activation

Use this workflow only when:

- the user invokes `/test` or `/implement`;
- the user explicitly asks for tests or TDD; or
- an active implementation pipeline dispatches a tester or implementer.

Ordinary edits follow the direct-execution policy and native validation. Static configuration, generated declarations, and platform-validated artifacts do not justify invented test machinery.

## Tester Budget

The dispatch prompt may lower these ceilings. It may not raise them without user authorization.

- First repository tool action: `gestalt map`.
- Default: one test. Maximum: three tests per task.
- Merge assertions that exercise one failure mechanism.
- Maximum: two RED attempts and ten minutes total.
- Use existing test infrastructure, installed dependencies, and the smallest focused native command.
- If the behavior cannot be falsified within the budget, return `status: gap` with the missing tool, requirement, or decision.

Do not:

- download tools, use the network or a live API, or add a dependency;
- create a compiler, parser, interpreter, simulator, symbolic executor, protocol emulator, mock server, DSL, mini-framework, or compatibility matrix;
- enumerate every caller, usage, input, syscall, crash point, schedule, or interleaving;
- run a repository-wide suite when a focused native command can falsify the behavior;
- test framework, dependency, standard-library, compiler, runtime, serializer, parser, collection, or operating-system behavior;
- write production code during the tester phase.

## Test Value Gate

Read and apply [reference/failure-modes.md](reference/failure-modes.md) before writing tests and again before reporting RED. It is the single source of truth; do not copy its failure-mode list into prompts, role files, or reports.

A test that needs substitute infrastructure is a gap, not a larger test task.

## RED

1. Derive the oracle from the requirement before reading implementation bodies.
2. Read existing tests and the target public interface for conventions and the test seam. Read implementation only as far as needed to locate that seam; never copy its behavior into the oracle.
3. Write the smallest representative falsifier set.
4. Run the focused command and record the exact failure.

Valid RED evidence is either:

- a test assertion failing because the requested behavior is absent or wrong; or
- a native compiler/typechecker failure that directly names a requested missing API or contract.

Setup, import, syntax, dependency, unrelated compilation, and environment failures are invalid. A test that passes immediately does not establish RED.

Before reporting, choose the most important test and name one plausible wrong implementation it rejects. If it would pass, sharpen or delete it.

## GREEN and Refactor

1. Add the minimum production change needed for the RED check.
2. Run the focused command and directly affected native validation once.
3. Refactor only the changed mechanism while staying green.
4. Stop when the requested acceptance condition passes and no known blocker remains.

Do not add adjacent behavior, configurability, cleanup, or another confidence run.

## Tester Evidence

```yaml
tester_report:
  status: success  # or gap
  test_files:
    - path: tests/test_feature.py
      tests: [test_requested_behavior]
  test_command: "pytest tests/test_feature.py -q"
  red_kind: assertion | compiler | typechecker
  rejected_wrong_implementation: "Returns the untransformed value"
  failure_output: |
    [last 20 relevant lines]
  gap_reason: null
```

## Implementer Evidence

```yaml
implementer_report:
  status: success  # or blocked
  implementation_files: [src/feature.py]
  test_command: "pytest tests/test_feature.py -q"
  test_output: |
    [last 20 relevant lines]
  blocked_reason: null
```
