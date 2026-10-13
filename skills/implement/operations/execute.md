# Scope Execution

## Pipeline

Per batch: Phase A testers → RED gate → Phase B implementers → GREEN gate → Phase C review → synthesis and fixes → commit. Within a phase, dispatch every independent operation in one message and wait once. [Checkpoint writes](../reference/checkpoint-format.md#writes) land before each dispatch.

## 1. Load and Gate the Scope

1. Read `scope.md`, `tasks.yaml`, optional `dependencies.yaml`, `validation.yaml`, `config.yaml`, and any checkpoint. `tasks.yaml` is the sole task-status authority, `review.yaml` the sole finding/deferred-issue authority; never read state from TodoWrite.
2. Require `validation.yaml.review_gate.status: passed`; otherwise stop and run [scope](../../scope/SKILL.md) with `review <name>`.
3. Activate the scope branch/worktree; clear the [branch gate](../SKILL.md) and [base-drift preflight](../reference/base-drift-preflight.md) before mutation.
4. Promote `draft` to `active` when work begins.
5. Resolve routing through [configuration.md](../reference/configuration.md); mint a new run/epoch for a top-level execution.

## 2. Build Batches

Batch per [parallel-detection.md](../reference/parallel-detection.md), in dependency order.

## 3. Snapshot a Batch

Snapshot routing per [configuration.md](../reference/configuration.md#batch-snapshot), create report directories through [`peer path`](../../peer/SKILL.md#report-layout--peer), and materialize requirements, acceptance criteria, and orientation per [subagent-workflow.md](../reference/subagent-workflow.md).

## 4. Phase A: RED

Dispatch all testers from the [template](../reference/subagent-workflow.md); never copy [test skill](../../test/SKILL.md) ceilings into prompts. A tester gap blocks its task and dependents; independent tasks continue when their files do not overlap the blocked mutation.

RED gate, per report:

1. Validate the schema, exact command, test paths, RED kind, and bounded output.
2. Run the focused commands in one batched tool round, combining compatible ones.
3. Apply the [canonical RED gate](../../test/SKILL.md#red).
4. Confirm the report's plausible wrong implementation fails one representative test.

Run no test-review agents. Return invalid evidence only to the affected tester within the [tester budget](../../test/SKILL.md#tester-budget); otherwise record a gap.

## 5. Phase B: GREEN

Dispatch all implementers, each with its requirements, tester report, partial state, and template. Then run the deduplicated focused commands and directly affected native validation once, in one batched round with compatible selectors combined. Any failed, incomplete, or non-GREEN implementer pauses the batch in phase `green`.

## 6. Phase C: Initial Concurrent Review

Materialize role prompts once per [review harnesses](../../review/reference/harnesses.md#materialization), with the batch diff as the target and its tasks' acceptance criteria among the requirements.

Dispatch, per [code review role](../../code/SKILL.md#review-roles) and within its gates, every configured native reviewer and the external fan-out; the route snapshot decides the mechanism, not alias names. Architecture uses diff or named-symbol queries only when the changed structure needs them. Apply the [review result gate](../../review/reference/harnesses.md#results).

## 7. Synthesize and Fix

Apply [review synthesis](../../review/reference/synthesis.md). Dispatch file-independent fix groups concurrently, then the targeted re-review. Never re-enter Phase C or fan out by role, harness, or execution class after a fix.

## 8. Complete a Batch

Mark the tasks done in `tasks.yaml`, append the batch review to `review.yaml`, write the completion checkpoint, commit implementation, tests, and scope state as one commit, and start the next ready batch from a fresh snapshot.

## 9. Final Validation and Integration Review

1. Run the smallest full native validation covering cross-batch integration.
2. Confirm every task is done and every acceptance criterion has direct evidence.
3. Multi-batch scope only: send one holistic integration prompt to every configured reviewer concurrently, covering cross-batch interactions (including behavior definitions from different batches both own under the [abstraction admission](../../review/reference/finding-bar.md#abstraction-admission)), scope acceptance, deferred findings, and final validation evidence. Do not repeat role reviews or reopen cleared batch-local findings.
4. Record the integration result and readiness in `review.yaml`.

Before a PR, run the pre-PR sync in [base-drift-preflight.md](../reference/base-drift-preflight.md) and review and validate the proposed tree.

## 10. Finish

Ask whether to run [scope](../../scope/SKILL.md) with `done <name>`. Only if the original invocation included a GitHub issue reference, run `issue pr --state <draft|open> --issue <n>` after readiness and trunk sync.

## Recovery Rules

- Mutating failure (tester, implementer, or fix agent, any route): preserve partial edits; record status/diff evidence, report directory, failure, and the exact wave; pause without auto-retry, rollback, or advance.
- Initial review failure: keep existing reports; redispatch only missing configured reports for that wave.
- Targeted re-review failure: one canonical replacement attempt; never restore role or execution-class fan-out.
- [continue](../../continue/SKILL.md) authorizes redispatch of the exact recorded wave. Never restart RED after a completed RED gate.

## Stop Condition

Stop when all tasks are done, acceptance criteria have evidence, native validation passes, review gates clear, and no known blocker remains.
