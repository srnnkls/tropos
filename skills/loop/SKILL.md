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

<!-- Generated from skills/loop/SKILL.md by henia build; edit the canonical source. -->

## {{if eq .preload_context "true"}}Pre-loaded Context{{else}}Runtime Context{{end}}

{{.context_instruction}}

{{range .context_commands}}{{.label}}:
{{if eq $.preload_context "true"}}!`{{.command}}`{{else}}```bash
{{.command}}
```{{end}}

{{end}}
# Autonomous Implementation Loop

Focus: $ARGUMENTS

`$loop` is explicit authorization to continue strict delegated implementation. The orchestrator does not author tests or production code.

## Protocol

1. Read matching scopes and authoritative `tasks.yaml` state.
2. Require `validation.yaml.review_gate.status: passed` for each selected scope.
3. Prioritize any checkpoint with in-flight mutations or a non-complete phase.
4. Otherwise derive the next dependency-ready batch through `implement/reference/parallel-detection.md`.
5. Activate that scope's branch/worktree and clear the required initial drift gate.
6. Snapshot and validate `config.yaml` once for a new batch. A recovered batch keeps its recorded snapshot.
7. Run [operations/iterate.md](operations/iterate.md).
8. Stop when all authoritative tasks are done, a blocker is reported, or ten batch iterations complete.

TodoWrite is optional display state and never drives selection or completion.

## Concurrency

Within a batch, dispatch all ready testers together, all cleared implementers together, and all review roles/reviewer routes together. A serial wait is valid only at the RED→GREEN and GREEN→review data boundaries or when one result changes another prompt.

## Related

- `implement` — canonical strict pipeline
- `continue` — exact checkpoint recovery
- `scope` — requirements and task state
