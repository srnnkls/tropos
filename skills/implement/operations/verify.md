# Completion Verification

## Evidence

Scope: read in one batched boundary the acceptance criteria (`scope.md`), task status (`tasks.yaml`), pre-implementation gate (`validation.yaml`), admitted findings and batch/integration outcomes (`review.yaml`), and phase and in-flight mutations (`checkpoint.yaml`).

Direct task: use its materialized requirements, diff, review reports, and current validation evidence; invent no scope state.

## Gate

Report ready only when:

1. every requested task and acceptance criterion has direct evidence;
2. required scope, batch, and integration review gates passed;
3. no admitted blocking or `needs_decision` finding remains;
4. the checkpoint records no incomplete phase or in-flight mutation; and
5. one smallest current native validation covering the completed integration behavior passes in this message.

Do not rerun cleared focused commands. An agent success report never substitutes for the artifact, report files, or current command output.

## Boundary

Read-only: never write tests or implementation, dispatch agents, edit scope documents, advance a checkpoint, commit, or move lifecycle state.

Incomplete recovery state: name the exact recorded wave and stop at [continue](../../continue/SKILL.md). Gate passed: hand off to [scope](../../scope/SKILL.md) with `done <name>`.
