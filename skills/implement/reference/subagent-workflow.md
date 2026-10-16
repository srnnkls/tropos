# Subagent Prompt Materialization

Prompt skeletons for [implement](../SKILL.md). Order and gates: [execute.md](../operations/execute.md); routing: [configuration.md](configuration.md); pre-dispatch writes: [checkpoint-format.md](checkpoint-format.md).

## Canonical Inputs

[scripts/dispatch-context](../scripts/dispatch-context) writes every dispatch's `prompt.md` from the skeletons below; never write, copy, or paraphrase a prompt or library text yourself. It runs each library input (`henia show`, `henia slots --inline`) fresh and takes task data as files.

- `{repository_map}` — fresh bounded output from the [repository-orientation contract](../../../instructions/AGENTS.md#tools-and-context) for `{workdir}`, passed as `--repository-map`
- `{role_contract}` — the selected base role from `agents/tester.md`, `agents/implementer.md`, or `agents/reviewer.md`
- `{tester_contract}` — [test/SKILL.md](../../test/SKILL.md)
- `{test_failure_modes}` — [test/reference/failure-modes.md](../../test/reference/failure-modes.md)
- `{tester_report_schema}` — [test/reference/report.md](../../test/reference/report.md)
- `{implementer_report_schema}` and `{fix_report_schema}` — [report.md](report.md)
- `{reviewer_report_schema}` — [review/reference/report.md](../../review/reference/report.md)
- `{finding_bar}` — [review/reference/finding-bar.md](../../review/reference/finding-bar.md)
- `{slot_providers}` — verbatim bodies of the listed skill slot providers and the commands of the `code.validation` rows the role consumes (`test.conventions`, `code.style` and `test.approach.<domain>` for testers; `test.conventions`, `code.style`, `code.validation`, `test.approach.<domain>` and `implement.approach.<domain>` for implementers and fixers; for reviewers, the providers [review harnesses](../../review/reference/harnesses.md#materialization) lists, plus for Abstractions the outputs of the [`review.detectors.<language>`](../../review/SKILL.md#slots) commands for the change's languages), or `none`. The approach slots resolve per task from its [domain](../SKILL.md#slots) and the review slots per batch from its tasks' domains, with `henia slots --inline`.

Role behavior comes only from `agents/*.md`. Claude native definitions and `peer` load the role directly. A native Codex `codex-*` dispatch passes `--role-contract`, which prepends `{role_contract}` to its task prompt; every other mechanism leaves it empty.

## Dispatch

Take the script's absolute path from the `Dispatch context script` entry of the skill context; `--help` lists its arguments. Per dispatch, in the report directory from [`peer path`](../../peer/SKILL.md#report-layout--peer):

```bash
<dispatch-context> implementer -d <dir> -C <workdir> --domain <domain> \
  --task-id T003 --task-name "<name>" --requirements <file> \
  --repository-map <file> --tester-report <file>
```

It prints the absolute `prompt.md` path. Roles: `tester`, `implementer`, `fixer` (`--findings`), `reviewer` (`--review-role`, `--diff`, one `--domain` per batch domain, Abstractions `--language` and `--ownership`).

- Native Claude `Task`/`Agent` and native Codex: the prompt is only `Read <path> in full before any other action; it is your dispatch context.` with the printed path.
- Peer: `--prompt-file <path>` per [peer routing](../../peer/reference/routing.md#dispatch).
- A script failure blocks that dispatch; resolve its error and rerun it.

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

Write one prompt per batch and [code review role](../../code/SKILL.md#review-roles) with `reviewer --review-role <role>`; `--structural-context` holds bounded structural query output and `--guidelines` only material `code.style` excerpts.

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
