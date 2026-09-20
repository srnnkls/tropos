# Completion Verification

Verify current evidence without mutating implementation or scope state.

## Evidence

For a scope, resolve it and read these in one batched boundary:

- acceptance criteria from `scope.md`;
- task status from `tasks.yaml`;
- the pre-implementation gate from `validation.yaml`;
- admitted findings and batch/integration outcomes from `review.yaml`;
- current phase and in-flight mutations from `checkpoint.yaml`.

For a direct task, use its materialized requirements, diff, review reports, and current validation evidence; do not invent scope state.

## Gate

Report ready only when:

1. every requested task and acceptance criterion has direct evidence;
2. required scope, batch, and integration review gates passed;
3. no admitted blocking or `needs_decision` finding remains;
4. the checkpoint records no incomplete phase or in-flight mutation; and
5. one smallest current native validation covering the completed integration behavior passes in this message.

Do not repeat already-cleared focused commands merely for confidence. An agent success report never substitutes for the artifact, report files, or current command output.

## Boundary

This operation is read-only. Never write tests or alter implementation files, dispatch implementation or review agents, edit scope documents, advance a checkpoint, commit, or move lifecycle state.

If recovery state is incomplete, name the exact recorded wave and stop at [continue](../../continue/SKILL.md). If the gate passes, hand off to [scope](../../scope/SKILL.md) with `done <name>`; that operation alone owns lifecycle completion.
