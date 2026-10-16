---
name: implement
description: Strict delegated RED → GREEN → review workflow. Use only when explicitly invoked for a task, scope, verification, or debugging.
metadata:
  type: generic
henia:
  slots:
    implement.approach:
  variables:
    context_commands:
      - label: Active scopes
        command: find scopes -maxdepth 3 -name scope.md 2>/dev/null || true
      - label: Checkpoints
        command: find scopes -name checkpoint.yaml -maxdepth 3 2>/dev/null || true
      - label: Git status
        command: git status --short 2>/dev/null || true
      - label: Current branch
        command: git branch --show-current 2>/dev/null || true
      - label: Default reviewers
        command: peer defaults reviewers 2>/dev/null || true
      - label: Resolved routes
        command: peer route show -C . 2>/dev/null || true
      - label: Dispatch context script
        command: scripts/dispatch-context --locate
  targets:
    claude:
      frontmatter:
        argument-hint: '[target]'
        allowed-tools: Bash(find *), Bash(ls *), Bash(git *), Bash(gh *), Bash(peer *), Bash(henia slots *), Bash(*/scripts/dispatch-context *)
    codex:
      openai:
        interface:
          display_name: Strict implementation
          short_description: Run delegated RED, GREEN, and review gates
          default_prompt: Use $implement to implement the requested task with delegated gates.
---

::::head{context slots="git.branching test.conventions test.approach implement.approach code.orientation code.style code.validation review.criteria review.general review.architecture review.tests review.abstractions review.detectors"}


# Strict Implementation

:::instruction{priority=high}
Enter only on the user's explicit `$implement` or a route the user selected; ordinary requests never enter. Never downgrade an explicit task to current-agent authoring.

The orchestrator coordinates and verifies. Fresh subagents write tests and production code. Every task runs RED → GREEN → review, with no pre-implementation test-review phase.
:::

:::routes
Pre-parse `--config`, `--worktree`, `--base`, `--state`, and GitHub issue references per [configuration.md](reference/configuration.md) and [execute.md](operations/execute.md).

| Target | Action |
|---|---|
| `config ...` | Update the selected scope's implementation routing |
| `verify` or `done` | Follow [verify.md](operations/verify.md) |
| `debug` or `trace` | Follow [debug.md](operations/debug.md) |
| Scope path or unique active scope | Follow [execute.md](operations/execute.md) |
| GitHub issue (`#N` or URL) without a scope | Run the single-task pipeline with the issue body as requirements |
| File path or task description | Run the single-task pipeline below |
| Missing or ambiguous | Ask for the target |
:::

## Branch Gate

Never dispatch mutating agents on `main`, `master`, or an unrelated branch.

- Scope or GitHub issue: the branch the `git.branching` providers ([git slots](../git/SKILL.md#slots)) name.
- Direct task: the current non-trunk branch; on trunk, ask for or create a task branch.
- Worktree only when explicitly requested.
- Base drift: [base-drift-preflight.md](reference/base-drift-preflight.md).

## Slots

| Slot | Covers |
|---|---|
| `implement.approach` | How implementers and fixers shape a change. Keyed by task domain as `implement.approach.<domain>`; providers of the slot itself reach every domain, and all providers apply together. |

Every task carries a `domain`: the scope task's field, or for a direct task one the orchestrator names from its files and requirements before dispatch. It keys `implement.approach` and the [test skill's](../test/SKILL.md#slots) `test.approach` for that task's subagents.

::::

## Single-Task Pipeline

Run [execute.md](operations/execute.md) phases A–C and synthesis (sections 4–7) for the one task, without a persisted checkpoint or batch commit. Snapshot routing once in memory per [configuration.md](reference/configuration.md); the [peer routing contract](../peer/reference/routing.md) owns host compatibility, variants, fan-out, effort, and report paths. Verify GREEN with the `code.validation` rows from [code slots](../code/SKILL.md#slots), run as is, and refactor only the changed mechanism. Cleared review plus final native validation completes the run; no integration review.

## Scope Pipeline

Follow [execute.md](operations/execute.md). Within a phase, dispatch serially only when one result changes another prompt.

## Failure and Recovery

Follow [execute.md](operations/execute.md#recovery-rules); a user-issued `$continue` authorizes redispatch of the exact recorded wave. Reviewer failures: [result-eligibility gate](../review/reference/harnesses.md#results).

## Stop Condition

Stop when requirements are implemented, focused and directly affected native validation passes, review clears, and no known blocker remains. No adjacent cleanup, extra review wave, or extra confidence run.

:::references
- [operations/execute.md](operations/execute.md) — scope execution
- [operations/verify.md](operations/verify.md) — completion evidence
- [operations/debug.md](operations/debug.md) — bounded root-cause work
- [reference/configuration.md](reference/configuration.md) — canonical role routing
- [reference/subagent-workflow.md](reference/subagent-workflow.md) — prompt materialization
- [scripts/dispatch-context](scripts/dispatch-context) — writes dispatch prompts
- [reference/report.md](reference/report.md) — implementer and fix reports
- [../test/reference/report.md](../test/reference/report.md) — tester report
- [../review/reference/report.md](../review/reference/report.md) — reviewer report
- [reference/checkpoint-format.md](reference/checkpoint-format.md) — recovery state
- [reference/parallel-detection.md](reference/parallel-detection.md) — task batching
- [tester role](../../agents/tester.md), [implementer role](../../agents/implementer.md), and [reviewer role](../../agents/reviewer.md) — canonical role contracts
:::
