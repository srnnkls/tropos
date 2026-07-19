# Iteration Protocol

Execute one batch per iteration until no pending tasks remain. Build batches from the batch signal — `dependencies.yaml`'s
precomputed `batches[*]` when present, otherwise derived from `tasks.yaml`'s `depends_on` + `files`
(see `../../implement/reference/parallel-detection.md`).

## Per-Batch Steps

1. Recover-first selection — Before choosing a new batch, prioritize any scope whose checkpoint
   has non-empty `incomplete_stages`; otherwise prioritize a non-complete `phase_cursor`. Use a
   normal dependency-ready batch only when neither recovery state exists.
2. Prepare — Activate that scope's branch/worktree and clear the mandatory base-drift
   preflight from the `implement` skill before writing scope state. Then read the relevant scope
   sections, re-read `checkpoint.yaml`, and read its live `config.yaml`. If enumeration marked config missing, run the interactive
   `/implement config <scope>` setup and create it now on the active scope branch/worktree.
   Validate external aliases with `peer list` and enforce same-host-family native routing. Under
   Codex reject `opus`/`sonnet` and every registry Codex-family peer alias (use `codex-native`;
   cross-family Claude CLI is allowed). Under Claude reject `codex-native` and every registry
   Claude-family peer alias (use native `opus`/`sonnet`; cross-family GPT peer is allowed). If incompatible, output
   `LOOP_BLOCKED: edit implementation config — host-incompatible agent` and stop without
   substitution. Never send a host-native token to peer. Never derive execution routing from `checkpoint.yaml` or
   `validation.yaml.review_config`.
3. Recover or delegate — Apply the same recovery protocol as `/continue`:
   - Recover every `incomplete_stages` entry first, preserving partial edits and redispatching only
     that exact task/phase; clear it only after its saved report passes the stage gate.
   - When no mutating marker remains, resume `phase_cursor` exactly. For test/targeted review or
     code/final review, accept saved `ok` reports and redispatch only pending/failed agents or roles
     from their recorded report directories. Never restart testers for an interrupted read-only gate.
   - Persist cursor/marker transitions before and after every dispatch. Only after the cursor reaches
     the next dependency-ready `tester: pending` may the loop begin that batch.

   Run the `implement` skill's four-phase pipeline (`operations/execute.md`) from that recovered
   point: testers → test review gate → implementers → review. Immediately
   before each Phase A, A.5, B, and C dispatch, re-read and validate `config.yaml`; route
   `codex-native` through Codex native delegation with inherited settings, explicit native aliases
   through the matching Task agent, and external aliases through `peer --agent <role> --peers ...`.
   Review gates require one success from each execution class actually configured. A config edit affects the next dispatch, never agents
   already running. If the file is missing, recreate it through the interactive
   `/implement config <scope>` setup before dispatching; never fall back to stale routing.
4. Verify — Run `hk check --all --fix`
5. Commit — `git add -A && git commit -m "feat(loop): <batch tasks>"` (one commit per batch)
6. Update — Mark every todo in the batch complete (before the drift check, so a drift-block can't leave a committed batch showing as pending)
7. Drift check — Re-sync with trunk every iteration:
   ```bash
   git fetch origin <trunk> --quiet
   behind=$(git rev-list --count "HEAD..origin/<trunk>")
   [ "$behind" -eq 0 ] || git rebase "origin/<trunk>"
   ```
   Clean rebase → continue. Conflicts → output `LOOP_BLOCKED: trunk drift conflict in <files>` and stop. See `../../implement/reference/base-drift-preflight.md`.
8. Next — Return to step 1

## CI Failures

If `hk check --all --fix` fails after step 4:
1. Spawn a focused fix subagent
2. Re-run `hk check --all --fix`
3. If still failing: output `LOOP_BLOCKED: <summary>` and stop

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
