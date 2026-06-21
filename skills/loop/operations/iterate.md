# Iteration Protocol

Execute one **batch** per iteration until no pending tasks remain. A batch is a set of tasks that
run in parallel; batches run in order. Build batches from the batch signal — `dependencies.yaml`'s
precomputed `batches[*]` when present, otherwise derived from `tasks.yaml`'s `depends_on` + `files`
(see `../../implement/reference/parallel-detection.md`).

## Per-Batch Steps

1. **Select** — Pick the next batch whose dependencies are all complete
2. **Read** — Read the relevant scope sections for the batch's tasks
3. **Delegate** — Run the `implement` skill's four-phase pipeline (`operations/execute.md`) for the
   whole batch: parallel testers → test review gate → parallel implementers → review. For a
   single-task batch this collapses to one tester/one implementer.
4. **Verify** — Run `hk check --all --fix`
5. **Commit** — `git add -A && git commit -m "feat(loop): <batch tasks>"` (one commit per batch)
6. **Update** — Mark every todo in the batch complete (before the drift check, so a drift-block can't leave a committed batch showing as pending)
7. **Drift check** — Since the loop runs unattended, re-sync with trunk every iteration so drift can't silently accumulate:
   ```bash
   git fetch origin <trunk> --quiet
   behind=$(git rev-list --count "HEAD..origin/<trunk>")
   [ "$behind" -eq 0 ] || git rebase "origin/<trunk>"
   ```
   Clean rebase → continue. Conflicts → output `LOOP_BLOCKED: trunk drift conflict in <files>` and stop (do not autonomously resolve semantic conflicts). See `../../implement/reference/base-drift-preflight.md`.
8. **Next** — Return to step 1

## CI Failures

If `hk check --all --fix` fails after step 4:
1. Read the error output
2. Spawn a focused fix subagent with the errors as context
3. Re-run `hk check --all --fix`
4. If still failing: output `LOOP_BLOCKED: <summary>` and stop

## Exit Conditions

| Condition | Output |
|---|---|
| All todos complete | `LOOP_COMPLETE: <n> tasks across <m> batches implemented` |
| CI unrecoverable | `LOOP_BLOCKED: <reason>` |
| 10 batch-iterations reached | `LOOP_LIMIT: review progress and resume` |

## Commit Format

feat(loop): <batch tasks>

Loop-Iteration: <n>
Batch: <batch-number>
Focus: <focus topic>
