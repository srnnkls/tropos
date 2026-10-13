# Iteration Protocol

## Selection

1. Recover a checkpoint with in-flight mutations or a non-complete phase per [continue](../../continue/SKILL.md).
2. Only without recovery state, derive the next dependency-ready batch through `implement/reference/parallel-detection.md`.

## Batch

1. Activate the scope branch/worktree and clear any required initial drift gate.
2. Snapshot routing for a new batch; a recovered batch keeps its recorded snapshot.
3. Follow `implement/operations/execute.md` from the selected point.
4. Run `hk check --all --fix` once.
5. Commit the completed batch and scope state.
6. Return to selection.

## Check Failure

Dispatch one focused fix agent for the reachable failure mechanism and re-run the failed check once. If it still fails, output `LOOP_BLOCKED: <summary>` and stop.

## Exit

| Condition | Output |
|---|---|
| All authoritative tasks complete and final gate passes | `LOOP_COMPLETE: <n> tasks across <m> batches implemented` |
| Unresolved gap, mutation failure, review-class failure, drift conflict, or repeated native-check failure | `LOOP_BLOCKED: <reason>` |
| Ten batch iterations reached | `LOOP_LIMIT: review progress and resume` |
