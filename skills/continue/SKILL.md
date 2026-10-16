---
name: continue
description: Resume an interrupted explicit implementation from its exact checkpoint wave.
metadata:
  type: generic
henia:
  targets:
    claude:
      frontmatter:
        argument-hint: '[scope-name]'
        allowed-tools: Bash(find *), Bash(ls *), Bash(git *), Bash(peer *), Bash(henia slots *), Bash(*/scripts/dispatch-context *)
    codex:
      openai:
        interface:
          display_name: Continue
          short_description: Apply the canonical continue skill workflow
          default_prompt: Use $continue for the requested task.
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
      - label: Current routes (the recorded batch snapshot remains authoritative)
        command: peer route show -C . 2>/dev/null || true
      - label: Dispatch context script
        command: henia preload --skill implement -- 'scripts/dispatch-context --locate'
---

:::head{context slots="git.branching test.conventions test.approach implement.approach code.orientation code.style code.validation review.criteria review.general review.architecture review.tests review.abstractions review.detectors"}


# Continue Implementation

Resume the exact wave recorded by an explicit `$implement` run, never restart from task status alone. Recovery order: [checkpoint-format.md](../implement/reference/checkpoint-format.md#recovery-priority); otherwise the next dependency-ready batch.

## 1. Resolve State

1. Resolve the named scope or the unique most-recent checkpoint. If none exists, report that `$implement <target>` must start the run.
2. In one batched read, load checkpoint, config, scope, tasks, optional dependencies, validation, review, and existing report directories.
3. Activate the recorded branch/worktree and verify the recorded commit against the live tree.
4. Apply the resume rule of [base-drift-preflight.md](../implement/reference/base-drift-preflight.md) before new mutation.

## 2. Validate Recovery

Keep the recorded routing snapshot and validate it through [configuration.md](../implement/reference/configuration.md). A recorded route that no longer exists is a blocker: report it and ask; never substitute.

Report the branch and last commit; current batch, tasks, phase, and status; in-flight mutations; existing report directories; and the one wave that will resume.

## 3. Resume

### Mutating wave

Accept an entry only if, comparing its baseline/current diff with any saved report, its RED/GREEN/fix gate now passes. Otherwise rewrite its prompt per [dispatch](../implement/reference/subagent-workflow.md#dispatch) and redispatch that exact task and phase with its partial edits and evidence; the user-issued `$continue` authorizes this. Dispatch all missing tasks in one message, with one checkpoint write before and one after.

### Read-only review wave

Keep existing reports; dispatch only missing configured reports (holistic ones for integration review) in one message. Never rerun testers or implementers.

### Next batch

Follow [execute.md](../implement/operations/execute.md) from a fresh snapshot.

## Failure Rules

- A failed redispatch: preserve partial mutations, update their evidence, and pause.
- Recovered RED evidence: [canonical RED gate](../test/SKILL.md#red). Never restart a cleared phase or reopen cleared findings.
- Review results: [review result gate](../review/reference/harnesses.md#results) against the recorded snapshot.

## Completion

Phase `complete`: verify task and review state and report completion without dispatch; a multi-batch run needs its integration gate.

:::
