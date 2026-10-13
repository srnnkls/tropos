---
name: test
description: Bounded RED-GREEN-REFACTOR methodology. Use when the user explicitly requests TDD or tests, or when the implement pipeline invokes it.
metadata:
  type: generic
henia:
  slots:
    test.conventions:
    test.approach: keyed(unique)
  targets:
    claude:
      frontmatter:
    codex:
      openai:
        interface:
          display_name: Bounded testing
          short_description: Write focused tests and verify RED and GREEN
          default_prompt: Use $test to test the requested behavior.
---

:::head{.context slots="test.conventions"}


# Bounded Test-Driven Development

Watch a check fail for the requested missing behavior, add minimal production code, then watch it pass.

## Slots

| Slot | Covers |
|---|---|
| `test.conventions` | Test locations, frameworks, fixtures, and the focused test command, in place of inference from nearby tests. Budget ceilings stay. |
| `test.approach` | Test design: oracle, test level and seam, falsifier selection. Keyed `test.approach.<domain>`, one provider per domain; the slot's own provider serves every domain without one. The budget, test value gate, and RED evidence stay. |

## Activation

Use only within the [workflow boundary](../../instructions/AGENTS.md#workflow-boundary), or when an active implementation pipeline dispatches a tester or implementer.

## Tester Budget

The dispatch prompt may lower these ceilings; raising them needs user authorization.

- One test by default, three per task at most; merge assertions that exercise one failure mechanism.
- At most two RED attempts and ten minutes total.
- Use existing local test infrastructure, installed dependencies, and the smallest focused native command; no repository-wide suite when that command can falsify the behavior.
- Behavior not falsifiable within budget, or a test needing substitute infrastructure: return `status: gap` with the missing tool, requirement, or decision.

Apply the [tester mutation boundary](../../agents/tester.md#boundary).

## Test Value Gate

Apply [reference/failure-modes.md](reference/failure-modes.md) before writing tests and again before reporting RED.

## RED

Design the tests with the task's `test.approach` provider (`henia slots --inline test.approach.<domain>`). The dispatch materializes it; a direct `$test` run names the domain from the task's files and requirements. Run the focused command and record the exact failure.

Valid RED evidence:

- a test assertion failing because the requested behavior is absent or wrong; or
- a native compiler/typechecker failure that directly names a requested missing API or contract.

Setup, import, syntax, dependency, unrelated compilation, and environment failures are invalid. A test that passes immediately does not establish RED.

## GREEN and Refactor

1. Add the minimum production change for the RED check.
2. Run the focused command and directly affected native validation once.
3. Refactor only the changed mechanism, staying green.
4. Stop when the requested acceptance condition passes and no known blocker remains.

Add no adjacent behavior, configurability, cleanup, or extra confidence run.

## Evidence

Return the exact [tester report](reference/report.md) during RED. Implementers return the report owned by the [implementation workflow](../implement/reference/report.md).

:::
