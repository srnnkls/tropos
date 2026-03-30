# Iteration Protocol

Execute for each pending todo until none remain.

## Per-Task Steps

1. **Select** — Pick the next incomplete todo
2. **Read** — Read the relevant scope section for context
3. **Delegate** — Use the `implement` skill with the task as argument
4. **Verify** — Run `hk check --all --fix`
5. **Commit** — `git add -A && git commit -m "feat(loop): <task>"`
6. **Update** — Mark todo complete
7. **Next** — Return to step 1

## CI Failures

If `hk check --all --fix` fails after step 4:
1. Read the error output
2. Spawn a focused fix subagent with the errors as context
3. Re-run `hk check --all --fix`
4. If still failing: output `LOOP_BLOCKED: <summary>` and stop

## Exit Conditions

| Condition | Output |
|---|---|
| All todos complete | `LOOP_COMPLETE: <n> tasks implemented` |
| CI unrecoverable | `LOOP_BLOCKED: <reason>` |
| 10 iterations reached | `LOOP_LIMIT: review progress and resume` |

## Commit Format

feat(loop): <task description>

Loop-Iteration: <n>
Focus: <focus topic>
