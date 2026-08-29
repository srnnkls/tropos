# Subagent Workflow

Canonical prompts and report contracts for explicit `/implement` execution. Pipeline order and gates live in [operations/execute.md](../operations/execute.md); routing lives in [configuration.md](configuration.md).

## Dispatch Rule

At every phase boundary, launch all independent tasks in one assistant message. Use the immutable batch routing snapshot; do not reload configuration per task or review role.

Tester and implementer routes are singular per task. Reviewer routes may contain several native and external agents. External reviewer aliases fan out through one `peer` call per role; all three role calls start in the same assistant message.

Before a mutating wave, persist all task recovery markers in one checkpoint write. After the wave, persist successful and failed outcomes in one checkpoint write.

## Tester Prompt

```text
Write failing tests for {task_id}: {task_name}.

First repository tool action: `gestalt map`.
Read and apply `skills/test/SKILL.md` and
`skills/test/reference/failure-modes.md` before writing tests and again before
reporting. They are the sole authority for tester budgets, mutation boundaries,
valid RED, prohibited machinery, test rejection, and self-checks. Do not copy,
reconstruct, or weaken them. If either is unavailable, return `status: gap`.

Requirements:
{task_requirements}

Work from: {workdir}
Return only this YAML:

tester_report:
  status: success | gap
  test_files:
    - path: path/to/test
      tests: [test_name]
  test_command: "focused command"
  red_kind: assertion | compiler | typechecker
  rejected_wrong_implementation: "plausible wrong behavior the test rejects"
  failure_output: |
    [last 20 relevant lines]
  gap_reason: null
```

Dispatch every tester for the batch in one message. External mutating routes use one peer call per task so partial writes remain attributable.

## Implementer Prompt

```text
Implement {task_id}: {task_name}.

First repository tool action: `gestalt map`.
Load language-specific guidance only when the local pattern does not settle it.

Requirements:
{task_requirements}

RED evidence:
{tester_report}

Run the focused command and observe RED. Write the minimum production change
that makes it GREEN. Refactor only the changed mechanism while staying green.
Do not add adjacent cleanup, configurability, tests, or validation machinery.
If requirements or RED evidence are insufficient, return `status: blocked`.

Work from: {workdir}
Return only this YAML:

implementer_report:
  status: success | blocked
  implementation_files: [path/to/file]
  test_command: "focused command"
  test_output: |
    [last 20 relevant lines]
  blocked_reason: null
```

Dispatch every cleared implementer in one message, each with its corresponding tester report.

## Review Wave

Prepare once:

- `{materialized_diff}`
- `{requirements}`
- `{report_schema}`
- `{finding_bar}` from `skills/review/reference/finding-bar.md`
- `{structural_context}` from bounded Gestalt queries
- `{guidelines}` containing only material Loqui excerpts

Build General, Architecture, and Compliance prompts from `skills/code/SKILL.md`. Start all native role Tasks and all external role fan-outs in one assistant message. Save each complete prompt as `prompt.md` in its canonical `peer path` directory.

Reviewers return only the exact reviewer schema. A report clears a gate only after synthesis admits its findings under the shared finding bar.

## Fix Prompt

```text
Fix these admitted review findings, grouped by shared mechanism:
{findings}

First repository tool action: `gestalt map`.
Make the smallest root fix. Do not address residual, deferred, adjacent, or
`needs decision:` items. Run the focused validation once.

Return only this YAML:

fix_report:
  status: success | blocked
  fixes_applied:
    - issue: "finding"
      fix: "root change"
  test_output: |
    [last 20 relevant lines]
  blocked_reason: null
```

Dispatch file-independent fix groups together. Re-review only the failed lens and changed mechanism. Two fix rounds per subject are the ceiling.

## Gaps and Failures

- Tester gap: consult existing scope evidence, then ask one blocking question if unresolved. Do not broaden the tester's budget.
- Mutating failure: preserve edits and evidence; pause. `/continue` authorizes deliberate redispatch.
- Reviewer failure: retain successful reports and redispatch only missing configured reports for the same wave.
