---
name: loop
description: Autonomous execution of explicit implementation scopes, one dependency batch per iteration with concurrent RED → GREEN → review waves.
henia:
  targets:
    claude:
      frontmatter:
        argument-hint: <focus topic>
        allowed-tools: Bash(find *), Bash(git *), Bash(peer *)
        context: fork
        hooks:
          Stop:
            - hooks:
                - type: command
                  command: |
                    echo "$HOOK_INPUT" | jq -e '.stop_hook_active' 2>/dev/null | grep -q true && exit 0
                    hk check --all --fix 2>&1 || exit 2
    codex:
      openai:
        interface:
          display_name: Loop
          short_description: Apply the canonical loop skill workflow
          default_prompt: Use $loop for the requested task.
  auto_invoke: false
  variables:
    context_commands:
      - label: Pending tasks
        command: 'find scopes -maxdepth 3 -name "tasks.yaml" -type f 2>/dev/null | xargs -I{} sh -c ''echo "=== {} ===" && grep -A1 "status: pending" {} 2>/dev/null'''
      - label: Git status
        command: git status --short 2>/dev/null || true
      - label: Current branch
        command: git branch --show-current 2>/dev/null || true
      - label: Current routes (recorded batch snapshots remain authoritative)
        command: peer route show -C . 2>/dev/null || true
metadata:
  type: generic
---

:::head{.context slots="workflow"}


# Autonomous Implementation Loop

Focus: $ARGUMENTS

`$loop` authorizes strict delegated implementation; the orchestrator authors no tests or production code.

1. Read matching scopes and their `tasks.yaml`; gate each selected scope per [execute.md](../implement/operations/execute.md#1-load-and-gate-the-scope).
2. Run [operations/iterate.md](operations/iterate.md) once per dependency batch.
3. Stop when all tasks are done, a blocker is reported, or ten batch iterations complete.

:::

:::related
- `implement` — canonical strict pipeline
- `continue` — exact checkpoint recovery
- `scope` — requirements and task state
:::
