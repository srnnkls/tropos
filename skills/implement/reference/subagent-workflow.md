# Subagent Prompt Materialization

Prompt skeletons for [implement](../SKILL.md). Order and gates: [execute.md](../operations/execute.md); routing: [configuration.md](configuration.md); pre-dispatch writes: [checkpoint-format.md](checkpoint-format.md).

## Canonical Inputs

Load at dispatch time and materialize verbatim. Run each library input (`henia show`, `henia slots --inline`) fresh for every dispatch and pipe it straight into that dispatch's `prompt.md`. Task data (requirements, repository map) may be staged.

- `{repository_map}` — fresh bounded output from the [repository-orientation contract](../../../instructions/AGENTS.md#tools-and-context) for `{workdir}`
- `{role_contract}` — the selected base role from `agents/tester.md`, `agents/implementer.md`, or `agents/reviewer.md`
- `{tester_contract}` — [test/SKILL.md](../../test/SKILL.md)
- `{test_failure_modes}` — [test/reference/failure-modes.md](../../test/reference/failure-modes.md)
- `{tester_report_schema}` — [test/reference/report.md](../../test/reference/report.md)
- `{implementer_report_schema}` and `{fix_report_schema}` — [report.md](report.md)
- `{reviewer_report_schema}` — [review/reference/report.md](../../review/reference/report.md)
- `{finding_bar}` — [review/reference/finding-bar.md](../../review/reference/finding-bar.md)
- `{slot_providers}` — verbatim bodies of the listed skill slot providers and the commands of the `code.validation` rows the role consumes (`test.conventions`, `code.style` and `test.approach.<domain>` for testers; `test.conventions`, `code.style`, `code.validation`, `test.approach.<domain>` and `implement.approach.<domain>` for implementers and fixers; for reviewers, the providers [review harnesses](../../review/reference/harnesses.md#materialization) lists, plus for Abstractions the outputs of the [`review.detectors.<language>`](../../review/SKILL.md#slots) commands for the change's languages), or `none`. The approach slots resolve per task from its [domain](../SKILL.md#slots) and the review slots per batch from its tasks' domains, with `henia slots --inline`.

Role behavior comes only from `agents/*.md`. Claude native definitions and `peer` load the role directly. A native Codex `codex-*` dispatch prepends `{role_contract}` to its task prompt; every other mechanism leaves it empty.

## Tester

```text
Write failing tests for {task_id}: {task_name}.

Role contract:
{role_contract}

Requirements:
{task_requirements}

Repository orientation:
{repository_map}

Tester contract:
{tester_contract}

Slot providers:
{slot_providers}

Test failure modes:
{test_failure_modes}

Work from: {workdir}

Return only this schema:
{tester_report_schema}
```

External-call cardinality: [peer routing](../../peer/reference/routing.md).

## Implementer

```text
Implement {task_id}: {task_name}.

Role contract:
{role_contract}

Requirements:
{task_requirements}

Repository orientation:
{repository_map}

RED evidence:
{tester_report}

Existing partial state:
{partial_state}

Slot providers:
{slot_providers}

Work from: {workdir}

Return only this schema:
{implementer_report_schema}
```

## Initial Review Wave

Materialize once per batch; `{structural_context}` comes from bounded Gestalt queries and `{guidelines}` holds only material `code.style` excerpts. Build one prompt per [code review role](../../code/SKILL.md#review-roles) and save it as `prompt.md` in its `peer path` directory.

```text
Review this completed change against only the assigned {role} gates.

Role contract:
{role_contract}

Requirements:
{requirements}

Change:
{materialized_diff}

Repository orientation:
{repository_map}

Structural context:
{structural_context}

Applicable language guidance:
{guidelines}

Slot providers:
{slot_providers}

Finding bar:
{finding_bar}

Return only this schema:
{reviewer_report_schema}
```

## Fix

```text
Fix these admitted review findings, grouped by shared mechanism:
{findings}

Role contract:
{role_contract}

Repository orientation:
{repository_map}

Slot providers:
{slot_providers}

Work from: {workdir}

Return only this schema:
{fix_report_schema}
```

Then follow the [targeted re-review protocol](../../review/reference/synthesis.md#46-fix-and-re-review-protocol).

## Gaps and Failures

- Missing repository orientation: return the role's canonical `gap` or `blocked` status before inspecting repository files.
- Tester gap: consult existing scope evidence, then ask one blocking question if unresolved; never broaden the tester budget.
- Other failures: [execute.md](../operations/execute.md#recovery-rules).
