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
        allowed-tools: Bash(find *), Bash(ls *), Bash(git *), Bash(peer *)
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
---

<!-- Generated from skills/continue/SKILL.md by henia build; edit the canonical source. -->

## {{if eq .preload_context "true"}}Pre-loaded Context{{else}}Runtime Context{{end}}

{{.context_instruction}}

{{range .context_commands}}{{.label}}:
{{if eq $.preload_context "true"}}!`{{.command}}`{{else}}```bash
{{.command}}
```{{end}}

{{end}}
# Continue Implementation

Resume the exact RED, GREEN, review, fix, or integration wave recorded by an explicit `$implement` run. Do not restart the pipeline from task status alone.

## 1. Resolve State

1. Resolve the named scope or the unique most-recent checkpoint.
2. Read checkpoint, config, scope, tasks, optional dependencies, validation, review, and existing report directories in one batched read boundary.
3. Treat `tasks.yaml` as task-status authority and `review.yaml` as finding authority. TodoWrite is irrelevant.
4. Activate the recorded branch/worktree and verify the recorded commit against the live tree.
5. Run base-drift analysis before new mutation only when resume has not yet cleared the initial gate, upstream movement is known, or overlap evidence exists.

If no checkpoint exists, report that `$implement` with `<target>` must start the run.

## 2. Validate Recovery

Use the checkpoint's immutable routing snapshot for the recorded batch. A current `config.yaml` change applies after that batch completes; do not rewrite in-flight routes.

Validate aliases and mechanisms through `implement/reference/configuration.md`. If a recorded route no longer exists, report the exact blocker and ask for a decision; never silently substitute.

Report:

- branch and last commit;
- current batch, tasks, phase, and status;
- in-flight mutations;
- existing report directories;
- the one wave that will resume.

## 3. Resume

Priority:

1. in-flight mutation entries;
2. recorded RED, GREEN, review, fix, or integration wave;
3. next dependency-ready batch derived from authoritative files.

### Mutating wave

Compare the entry's baseline/current diff with any saved report. Accept it only if its RED/GREEN/fix gate now passes. Otherwise `$continue` authorizes deliberate redispatch of that exact task and phase with the partial edits and evidence supplied.

Dispatch every independent missing task in one message. Write one checkpoint before the wave and one after all results land.

### Read-only review wave

Read reports already present in the recorded role directories. Dispatch all missing configured reports across every pending role in one message. Do not rerun testers or implementers.

For a multi-batch integration review, dispatch only the missing holistic reports; do not recreate the per-role cascade.

### Next batch

After the recovered batch completes, derive the next batch, snapshot current `config.yaml` once, and follow `implement/operations/execute.md`.

## Failure Rules

- Preserve partial mutations and update their evidence; pause after a failed redispatch.
- Retain successful reviewer reports and redispatch only missing configured reports.
- Apply the [canonical RED gate](../test/SKILL.md#red) to recovered evidence; do not restart a cleared phase or re-open cleared findings.
- Apply the [review result gate](../review/reference/harnesses.md#results) to the recorded batch snapshot.

## Completion

When the checkpoint phase is `complete`, verify authoritative task/review state and report completion without dispatch. A one-batch run has no duplicate final review; a multi-batch run completes after its holistic integration gate.
