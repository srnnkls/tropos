# Subagent Dispatch

Dispatch prompts for [implement](../SKILL.md). Order and gates: [execute.md](../operations/execute.md); routing: [configuration.md](configuration.md); pre-dispatch writes: [checkpoint-format.md](checkpoint-format.md).

## Resolution

A dispatch carries task data only. Each role resolves its library input itself, before inspecting repository files:

1. Load the skills its role definition names. Claude agents preload them; every other harness runs `henia show <skill> --head` for each one not in its context. The heads list the slot providers live.
2. Run the `code.orientation` providers.
3. Read each listed provider for the task's domain and languages with the command it names.
4. Read the role references and the report schema its definition names with `henia show`.

Never paste library text, slot provider bodies, or orientation output into a prompt.

## Dispatch

Stage task data as files in the report directory from [`peer path`](../../peer/SKILL.md#report-layout) and write `prompt.md` there from the role's fields below. Every prompt names the working tree, the task's [domain](../SKILL.md#slots), and each language the task changes.

| Role | Fields |
|---|---|
| `tester` | task ID and name, requirements file |
| `implementer` | task ID and name, requirements file, verified tester report file, partial state or `none` |
| `fixer` | admitted findings file, grouped by shared mechanism |
| `reviewer` | [code review role](../../code/SKILL.md#review-roles), requirements file, diff file, report file; Abstractions adds the implementer reports' `ownership` |

Review prompts go one per batch and role; domains and languages are the batch tasks' union. Fixes then follow the [targeted re-review protocol](../../review/reference/synthesis.md#46-fix-and-re-review-protocol).

- Native Claude `Task`/`Agent`: the prompt is only `Read <path> in full before any other action; it is your dispatch.` with the absolute `prompt.md` path.
- Native Codex: the same line, preceded by `Read <role> in full; it is your role.` with the role's `agents/<role>.md` from the Codex build: the project's `.codex/agents/`, else `~/.codex/agents/`.
- Peer: `--prompt-file <path>` per [peer routing](../../peer/reference/routing.md#dispatch).

External-call cardinality: [peer routing](../../peer/reference/routing.md).

## Gaps and Failures

- Orientation or slot resolution failure: the role returns its canonical `gap` or `blocked` status before inspecting repository files.
- Tester gap: consult existing scope evidence, then ask one blocking question if unresolved; never broaden the tester budget.
- Other failures: [execute.md](../operations/execute.md#recovery-rules).
