# Iteration Protocol

Execute or recover one dependency batch per iteration through the canonical strict pipeline.

## Selection

1. Recover in-flight mutations first.
2. Otherwise resume the exact recorded RED, GREEN, review, fix, or integration wave.
3. Only when no recovery state exists, derive a dependency-ready batch from `dependencies.yaml` or `tasks.yaml` through `implement/reference/parallel-detection.md`.

Task status comes from `tasks.yaml`; review state comes from `review.yaml`. TodoWrite does not participate.

## Batch

1. Activate the scope branch/worktree and clear any required initial drift gate.
2. For a new batch, read and validate `config.yaml` once and persist an immutable routing snapshot. For recovery, keep the recorded snapshot.
3. Follow `implement/operations/execute.md` from the selected point:
   - all ready testers in one message;
   - one RED gate;
   - all cleared implementers in one message;
   - one GREEN gate;
   - all review roles and configured reviewer routes in one message;
   - one synthesis with bounded fixes.
4. Run `hk check --all --fix` once after the batch.
5. Commit the completed batch and authoritative scope state.
6. Return to selection.

Do not reload routing per phase or role. Do not run a test-review agent wave. Do not fetch/rebase at every iteration; drift work requires new upstream or overlap evidence, or the final pre-PR gate.

## Check Failure

When the post-batch native check fails:

1. Dispatch one focused fix agent for the reachable failure mechanism.
2. Re-run the failed check once.
3. If it still fails, output `LOOP_BLOCKED: <summary>` and stop.

## Exit

| Condition | Output |
|---|---|
| All authoritative tasks complete and final gate passes | `LOOP_COMPLETE: <n> tasks across <m> batches implemented` |
| Unresolved gap, mutation failure, review-class failure, drift conflict, or repeated native-check failure | `LOOP_BLOCKED: <reason>` |
| Ten batch iterations reached | `LOOP_LIMIT: review progress and resume` |
