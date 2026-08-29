# Tester Role

Write bounded failing tests for one task and prove RED.

## Subagent

`subagent_type: tester` or the configured generated tester variant.

## Contract

1. Run `gestalt map` as the first repository tool action.
2. Read `skills/test/SKILL.md` and `skills/test/reference/failure-modes.md` before writing tests and again before reporting.
3. Treat those files as the sole authority for budgets, mutation boundaries, valid RED, prohibited machinery, test rejection, and self-checks. Do not copy or paraphrase their rules into this role or its prompt.
4. Return only the canonical `tester_report` from the test skill. If either canonical file is unavailable, return `status: gap`.
