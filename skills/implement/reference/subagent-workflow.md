# Subagent Prompt Materialization

Prompt skeletons for explicit `/implement`. Pipeline order and gates live in [execute.md](../operations/execute.md); routing lives in [configuration.md](configuration.md). [Checkpoint boundaries](checkpoint-format.md) persist all mutations before dispatch. A boundary write may simultaneously close one wave and arm the next.

## Canonical Inputs

Load these resources at dispatch time and materialize them verbatim into the named placeholders:

- `{tester_report_schema}` — [test/reference/report.md](../../test/reference/report.md)
- `{implementer_report_schema}` and `{fix_report_schema}` — [report.md](report.md)
- `{reviewer_report_schema}` — [review/reference/report.md](../../review/reference/report.md)
- `{finding_bar}` — [review/reference/finding-bar.md](../../review/reference/finding-bar.md)

Role behavior comes only from `agents/tester.md`, `agents/implementer.md`, and `agents/reviewer.md`. Prompts supply task-specific data; they do not restate role policy.

## Tester

```text
Write failing tests for {task_id}: {task_name}.

Requirements:
{task_requirements}

Work from: {workdir}

Return only this schema:
{tester_report_schema}
```

Dispatch every tester for the batch in one message. Use one external peer call per mutating task so partial writes remain attributable.

## Implementer

```text
Implement {task_id}: {task_name}.

Requirements:
{task_requirements}

RED evidence:
{tester_report}

Existing partial state:
{partial_state}

Work from: {workdir}

Return only this schema:
{implementer_report_schema}
```

Dispatch every cleared implementer in one message, each with its corresponding tester report.

## Review Wave

Materialize once per batch:

- `{materialized_diff}`;
- `{requirements}`;
- `{reviewer_report_schema}`;
- `{finding_bar}`;
- `{structural_context}` from bounded Gestalt queries;
- `{guidelines}` containing only material Loqui excerpts.

Build General, Architecture, and Compliance prompts from the [code skill](../../code/SKILL.md). Start all native role agents and external role fan-outs in one message. Save each complete prompt as `prompt.md` in its canonical `peer path` directory.

```text
Review this completed change against only the assigned {role} gates.

Requirements:
{requirements}

Change:
{materialized_diff}

Structural context:
{structural_context}

Applicable language guidance:
{guidelines}

Finding bar:
{finding_bar}

Return only this schema:
{reviewer_report_schema}
```

## Fix

```text
Fix these admitted review findings, grouped by shared mechanism:
{findings}

Work from: {workdir}

Return only this schema:
{fix_report_schema}
```

Dispatch file-independent fix groups together. Re-review only the failed lens and changed mechanism. Round limits come from [review synthesis](../../review/reference/synthesis.md).

## Gaps and Failures

- Tester gap: consult existing scope evidence, then ask one blocking question if unresolved. Do not broaden the tester budget.
- Mutating failure: preserve edits and evidence; pause. `/continue` authorizes deliberate redispatch.
- Reviewer failure: retain successful reports and redispatch only missing configured reports for the same wave.
