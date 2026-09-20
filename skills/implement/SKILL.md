---
name: implement
description: Strict delegated RED → GREEN → review workflow. Use only when explicitly invoked for a task, scope, verification, or debugging.
metadata:
  type: generic
henia:
  auto_invoke: false
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
  targets:
    claude:
      frontmatter:
        argument-hint: '[target]'
        allowed-tools: Bash(find *), Bash(ls *), Bash(git *), Bash(gh *), Bash(peer *)
    codex:
      openai:
        interface:
          display_name: Strict implementation
          short_description: Run delegated RED, GREEN, and review gates
          default_prompt: Use $implement to implement the requested task with delegated gates.
---

<!-- Generated from skills/implement/SKILL.md by henia build; edit the canonical source. -->

## {{if eq .preload_context "true"}}Pre-loaded Context{{else}}Runtime Context{{end}}

{{.context_instruction}}

{{range .context_commands}}{{.label}}:
{{if eq $.preload_context "true"}}!`{{.command}}`{{else}}```bash
{{.command}}
```{{end}}

{{end}}
# Strict Implementation

:::instruction{priority=high}
Explicit `$implement` is the high-assurance path. Ordinary requests do not enter it automatically.

The orchestrator coordinates and verifies. Fresh subagents write tests and production code. Every task follows RED → GREEN → review; no independent pre-implementation test-review phase exists.
:::

## Routes

Pre-parse `--config`, `--worktree`, `--base`, `--state`, and GitHub issue references as documented in [configuration.md](reference/configuration.md) and [execute.md](operations/execute.md).

| Target | Action |
|---|---|
| `config ...` | Update the selected scope's implementation routing |
| `verify` or `done` | Follow [verify.md](operations/verify.md) |
| `debug` or `trace` | Follow [debug.md](operations/debug.md) |
| Scope path or unique active scope | Follow [execute.md](operations/execute.md) |
| File path or task description | Run the single-task pipeline below |
| Missing or ambiguous | Ask for the target |

Invoking this skill is the opt-in. Do not downgrade an explicit task to direct current-agent authoring.

## Branch Gate

Never dispatch mutating agents on `main`, `master`, or an unrelated branch.

- Scope: use `feat/<scope-name>` unless the scope records another branch.
- GitHub issue: use `<issue-number>-<issue-title>`.
- Direct task: use the current non-trunk branch; if on trunk, ask for or create a task branch.
- Use a worktree only when explicitly requested.
- Run the base-drift gate once before the first mutating batch and again before PR creation. A later recheck requires new upstream evidence or an observed overlap.

## Configuration

Resolve routing once before a direct task or once at each scope batch boundary. The immutable snapshot governs that batch's tester, implementer, reviewers, effort, execution classes, and report run ID. Mid-batch edits apply to the next batch.

Configuration resolution and immutable snapshots live in [configuration.md](reference/configuration.md). Host compatibility, generated variants, peer fan-out, effort, and report paths live in the canonical [peer routing contract](../peer/reference/routing.md).

## Single-Task Pipeline

Use the same gates as one scope batch without a persisted checkpoint.

### Phase A: RED

1. Dispatch one fresh configured tester with the task requirements; the [test skill](../test/SKILL.md) owns its hard ceilings.
2. Require `tester_report` with the exact focused command and bounded RED evidence.
3. Run that command once and inspect one representative falsifier: name a plausible wrong implementation and confirm the test rejects it.

Apply the [canonical RED gate](../test/SKILL.md#red). Return invalid evidence to the tester only when the remaining canonical attempt/time budget permits; otherwise surface a gap.

### Phase B: GREEN

Dispatch one fresh configured implementer with the task requirements and tester report. After it returns, verify the focused command and directly affected native validation in one batched tool round, combining compatible selectors. Refactor only the changed mechanism.

### Phase C: Initial Review

Materialize the diff, requirements, report schema, finding bar, bounded Gestalt context, and applicable Loqui excerpts once. In one message, dispatch all configured reviewers for General, Architecture, and Compliance. Wait once and synthesize once.

Apply [review synthesis](../review/reference/synthesis.md) for admission, grouping, fixes, `needs decision`, re-review, and round limits. A post-fix re-review follows its targeted protocol and never re-enters Phase C.

Once review clears, Phase C plus final native validation completes a single-task run. Do not launch a duplicate final review.

## Scope Pipeline

[execute.md](operations/execute.md) owns batching, checkpoints, continuation, commits, and cross-batch integration. Its fixed dependency boundaries are:

1. all ready testers concurrently;
2. one RED gate;
3. all cleared implementers concurrently;
4. one initial review wave with all review roles and reviewer routes concurrently.

No serial dispatch is allowed inside a boundary unless one result changes another prompt.

## Failure and Recovery

For a failed or interrupted mutating subagent, preserve partial edits and record the relevant status, diff, report directory, and failure. Do not auto-retry, roll back, or advance. `$continue` is deliberate redispatch authorization for the exact recorded wave.

Reviewer failures apply the [canonical result-eligibility gate](../review/reference/harnesses.md#results).

## Stop Condition

Stop when the requested requirements are implemented, focused and directly affected native validation passes, the review gate clears, and no known blocker remains. Do not add adjacent cleanup, another review wave, or another confidence run.

## References

- [operations/execute.md](operations/execute.md) — scope execution
- [operations/verify.md](operations/verify.md) — completion evidence
- [operations/debug.md](operations/debug.md) — bounded root-cause work
- [reference/configuration.md](reference/configuration.md) — canonical role routing
- [reference/subagent-workflow.md](reference/subagent-workflow.md) — prompt materialization
- [reference/report.md](reference/report.md) — implementer and fix reports
- [../test/reference/report.md](../test/reference/report.md) — tester report
- [../review/reference/report.md](../review/reference/report.md) — reviewer report
- [reference/checkpoint-format.md](reference/checkpoint-format.md) — recovery state
- [reference/parallel-detection.md](reference/parallel-detection.md) — task batching
- [tester role](../../agents/tester.md), [implementer role](../../agents/implementer.md), and [reviewer role](../../agents/reviewer.md) — canonical role contracts
