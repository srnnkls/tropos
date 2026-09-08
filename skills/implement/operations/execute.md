# Scope Execution

Execute an explicit implementation scope with strict delegated TDD and bounded concurrent gates.

## Pipeline

Each batch has three phases:

```text
Phase A: all ready testers concurrently
    ↓ one RED gate
Phase B: all cleared implementers concurrently
    ↓ one GREEN gate
Phase C: every review role and configured reviewer concurrently
    ↓ one synthesis and targeted fix verification
commit batch
```

The A→B→C barriers are data dependencies. Inside each phase, dispatch every independent operation in one message.

## 1. Load and Gate the Scope

1. Resolve the scope directory and read `scope.md`, `tasks.yaml`, optional `dependencies.yaml`, `validation.yaml`, `config.yaml`, and any checkpoint.
2. Treat `tasks.yaml` as the sole task-status authority and `review.yaml` as the finding/deferred-issue authority. TodoWrite is optional display state and is never required or read back.
3. Activate the scope branch/worktree and clear the branch/base-drift gate from `../SKILL.md` before mutation.
4. Promote `draft` to `active` when work begins.
5. Require `validation.yaml.review_gate.status: passed`. If absent or failed, stop and run `/scope review <name>`.
6. Resolve and validate implementation routing through [configuration.md](../reference/configuration.md). Mint a new run/epoch for a top-level execution.

## 2. Build Batches

Use `dependencies.yaml.batches[*].tasks` when present. Otherwise derive batches from `tasks.yaml` through [parallel-detection.md](../reference/parallel-detection.md).

- A task is ready when all `depends_on` tasks are done.
- Tasks that share a target file cannot mutate concurrently.
- Resolve missing `files` for all ready tasks in one bounded Gestalt-first discovery wave before batching. Persist resolved paths. If independence remains unknown, report a scope gap; do not silently create one full pipeline per task.

Batches follow dependency order. All tasks inside a batch execute concurrently per phase.

## 3. Snapshot a Batch

At the batch boundary:

1. Re-read and validate `config.yaml` once.
2. Snapshot tester, implementer, reviewer, effort, execution-class, and run-ID routing into `checkpoint.yaml`.
3. Create report directories through the canonical [`peer path` interface](../../peer/SKILL.md#report-layout--peer).
4. Materialize task requirements, acceptance criteria, and the repository orientation required by [subagent-workflow.md](../reference/subagent-workflow.md).

The snapshot is immutable for the batch. Configuration edits apply to the next batch.

## 4. Phase A: RED

Before dispatch, write one checkpoint transition containing every batch task as an in-flight tester mutation with baseline status/diff evidence and its report directory.

Dispatch all testers in one message using the route snapshot and the canonical template in [subagent-workflow.md](../reference/subagent-workflow.md). The role loads its ceilings from the [test skill](../../test/SKILL.md); do not copy them into task prompts.

Wait once for all reports. A tester gap blocks only its task and every dependent task; independent cleared tasks may continue if their files do not overlap the blocked mutation.

### RED gate

For each successful report:

1. Validate the report schema, exact command, test paths, RED kind, and bounded output.
2. Combine compatible focused commands where the native runner permits; otherwise run the reported commands as one batched tool round.
3. Apply the [canonical RED gate](../../test/SKILL.md#red).
4. Inspect one representative falsifier: use the report's plausible wrong implementation and confirm its test would fail.

No test-review agents run. Return invalid evidence only to the affected tester and only within the remaining budget owned by the [test skill](../../test/SKILL.md#tester-budget); otherwise record a gap.

At the RED→GREEN boundary, write one checkpoint transition that clears successful tester mutations, preserves failed/incomplete tester evidence, sets phase `green`, and records every cleared task as an in-flight implementer mutation. This write must land before any implementer dispatch.

## 5. Phase B: GREEN

Dispatch all implementers in one message. Each receives its task requirements, tester report, existing partial state, and the canonical implementer prompt. The implementer must run RED, make the smallest production change, verify GREEN, and refactor only the changed mechanism.

Wait once. Collect every implementer report, deduplicate identical commands, combine compatible native selectors, and run incompatible groups in one batched tool round. Verify each focused command and directly affected native validation once.

If any implementer is failed, incomplete, or fails GREEN, clear successful entries, retain failed evidence under phase `green`, and pause. Only after every implementer clears GREEN may one GREEN→review checkpoint transition clear the mutation entries, set phase `review`, and record all review report directories.

## 6. Phase C: Initial Concurrent Review

Every completed batch receives one initial review wave.

Prepare shared inputs once:

- materialized batch diff;
- applicable task requirements and acceptance criteria;
- exact report schema;
- verbatim [finding bar](../../review/reference/finding-bar.md);
- repository orientation from the batch snapshot plus bounded Gestalt context for changed symbols/files;
- only the Loqui excerpts material to changed language patterns.

Create General, Architecture, and Compliance prompts from the canonical code-review roles. In one assistant message, dispatch every configured native reviewer for all three roles and start each role's external peer fan-out. The route snapshot and [configuration.md](../reference/configuration.md) determine the mechanism; alias names do not.

Each role stays within its gate:

| Role | Gates |
|---|---|
| General | Correctness, Security, Performance |
| Architecture | Architecture |
| Compliance | Style |

For architecture, use `gestalt diff` or named-symbol queries only when the changed structure requires them. Do not require `analyze`, verbose propagation, and caller enumeration as a fixed command floor.

Wait once, then apply the [canonical review result gate](../../review/reference/harnesses.md#results).

## 7. Synthesize and Fix

Apply [review synthesis](../../review/reference/synthesis.md), which owns admission, grouping, disposition, `needs decision`, re-review scope, and round limits.

Before any fix wave, persist every file-safe fix group as an in-flight mutation in one checkpoint write. Dispatch independent groups concurrently. After results, clear successful fix markers and retain failed/interrupted evidence in one write, then enter the targeted re-review protocol. Never re-enter Phase C or fan out by role, harness, or execution class after a fix.

## 8. Complete a Batch

When RED, GREEN, review, and accepted fixes pass:

1. Mark the batch tasks done in `tasks.yaml`.
2. Append the batch review to `review.yaml`.
3. Write the minimal recovery checkpoint from [checkpoint-format.md](../reference/checkpoint-format.md).
4. Commit implementation, tests, and scope state as one batch commit.
5. Start the next dependency-ready batch from a fresh routing snapshot.

Do not fetch/rebase merely because a batch ended. Re-run drift analysis only when new upstream movement is known, overlap appears, or the pre-PR gate requires it.

## 9. Final Validation and Integration Review

After all batches:

1. Run the smallest full native validation that covers cross-batch integration.
2. Confirm every task is done and every acceptance criterion has direct evidence.
3. For a one-batch scope, cleared Phase C — including targeted fix verification when needed — is final. Do not dispatch a separate integration review.
4. For a multi-batch scope, dispatch one holistic integration prompt to every configured reviewer concurrently. Check only cross-batch interactions, scope acceptance, deferred findings, and final validation evidence. Do not repeat General/Architecture/Compliance or reopen cleared batch-local findings.
5. Record the integration result and readiness in `review.yaml`.

Before a PR, fetch trunk and apply [base-drift-preflight.md](../reference/base-drift-preflight.md). Review and validate the tree that will be proposed.

## 10. Finish

When readiness passes, ask whether to run `/scope done <name>`; that operation owns lifecycle movement and final scope validation.

If the original explicit invocation included a GitHub issue reference, invoke `issue pr --state <draft|open> --issue <n>` after readiness and trunk sync. Do not create a PR without that original issue signal.

## Recovery Rules

- Mutating failure: preserve edits, report directory, status/diff evidence, and exact wave; pause.
- Initial read-only review failure: report files are the recovery source; redispatch only missing configured reports for that initial wave.
- Targeted re-review failure: use only the canonical single replacement attempt; never restore role or execution-class fan-out.
- `/continue` authorizes deliberate redispatch of the exact recorded wave.
- Never restart RED after a completed RED gate, and never infer progress from TodoWrite.

## Stop Condition

The scope is ready when all tasks are done, acceptance criteria have evidence, native validation passes, review gates clear, and no known blocker remains. Stop there.
