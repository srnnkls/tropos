---
name: sweep
description: Sweep herdr projects — join each project's herdr agents, active scopes, branches and worktrees, write one pointer handoff per project to `.tropos/sweep.md`, then close agents without a turn in 24 hours and remove merged clean branches and worktrees. Use only when explicitly invoked.
metadata:
  type: generic
henia:
  slots:
    sweep.state: keyed(list(command))
  auto_invoke: false
  targets:
    claude:
      frontmatter:
        argument-hint: '[project-path ...]'
        allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/inventory), Bash(${CLAUDE_SKILL_DIR}/scripts/inventory *), Bash(herdr agent list *), Bash(herdr worktree list *), Bash(herdr pane list *), Bash(memex index *), Bash(memex sessions *), Bash(henia slots *), Bash(git worktree list *), Bash(git for-each-ref *), Bash(git status *)
    codex:
      openai:
        interface:
          display_name: Sweep
          short_description: Hand off and clean up herdr projects
          default_prompt: Use $sweep for the requested projects.
  variables:
    context_commands:
      - label: Now (UTC)
        command: date -u +%Y-%m-%dT%H:%M:%SZ
      - label: Own pane, never closed
        command: echo "${HERDR_PANE_ID:-none}"
---

::::head{context slots="sweep.state"}
Sweep each project named in the arguments, else every project with a herdr agent. A project root is the main checkout of the repository holding an agent's directory, else the directory.

## 1. Inventory

Run [scripts/inventory](scripts/inventory) `[project-path ...]`, resolved against this skill's directory, once. It indexes memex and prints one JSON document whose `projects` each carry:

- `kind`: `present`, or `missing` when the root no longer exists, which carries only `root` and `agents`;
- `root`, `default_branch`, `head_commit`;
- `agents`: pane, harness, status, directory and `tracking`: `tracked` with the newest memex `session` (`last_turn_at`, `resume_command`), `unindexed` when memex has no row for its session id, or `untracked` without one;
- `branches`: upstream, commits `ahead` of the default branch, the worktree checking it out, and `merge`: `ancestry` when `--merged` lists it, `pull_request` when a merged PR's head equals its tip, else `unmerged` with any `open_pull_request`;
- `worktrees`: `head` (`branch` or `detached`), `uncommitted_entries` and herdr `workspace_id`;
- `scopes`: each active scope with its `open_tasks` (tasks not `done`), per [scope location](../scope/SKILL.md#scope-location);
- `tool_state`: output of every `sweep.state` provider command that printed something at the root, and `slot_problems`;
- `previous_handoff`: the path of `.tropos/sweep.md` when one exists.

## 2. Classify

- An agent is stale when its `last_turn_at` is more than 24 hours before now. An `unindexed` or `untracked` agent, and the own pane, stay open.
- A work item is a branch, a worktree, an active scope or an agent, joined by branch, worktree path and scope name. Items of the previous handoff whose pointers still resolve are carried over.
- An item is open when its branch is not merged or it has uncommitted changes, an open scope task, tool-state output, or a stale agent whose last turn ended unfinished (`herdr agent read <pane> --lines 60`). Otherwise it is done.

## 3. Write the handoff

Overwrite `R/.tropos/sweep.md` with every open item, pointers only: never copy scope, transcript or diff content. When `git -C R check-ignore -q .tropos/sweep.md` fails, append `.tropos/` to `$(git -C R rev-parse --git-common-dir)/info/exclude`.

```markdown
# Sweep: <project>

<UTC timestamp>, <default branch> at <short sha>

## <item>

- State: <what is done, what remains, one line>
- Next: <one concrete action>
- Branch: <name>, <n> ahead, upstream <upstream>
- PR: <url>
- Worktree: <path>, <clean|dirty>
- Scope: <path>
- Session: <harness> <session id>, last turn <last_turn_at>: `<resume_command>`
```

Omit pointer lines that do not apply. Pane and workspace ids never appear. A project without open items gets `No open work.` under the header.

## 4. Clean

After the handoff is written:

1. Close each stale agent with `herdr pane close <pane_id>`. Close each workspace with no pane left (`herdr pane list --workspace <id>`) with `herdr workspace close <id>`.
2. Remove each worktree whose branch is merged, whose status is clean and which no remaining agent uses: `herdr worktree remove --workspace <open_workspace_id>` when it has one, else `git -C R worktree remove <path>`. Never pass `--force`.
3. Delete each merged branch, skipping the default branch and any branch still checked out: `git -C R branch -d <branch>` for an `ancestry` merge, `git -C R branch -D <branch>` only for a `pull_request` merge. Then run `git -C R worktree prune`.

## 5. Report

One line per project: handoff path, open items, agents closed, worktrees and branches removed. List every command that failed with its error.
::::

## Slots

| Slot | Covers |
|---|---|
| `sweep.state` | Commands run at a project root whose output marks unfinished tool state, such as undeployed or drifted artifacts; keyed by tool as `sweep.state.<tool>`. A command prints nothing or a success line when the state is clean and guards its own applicability. |
