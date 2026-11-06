---
created: 2026-11-05
status: draft
issue_type: Feature
---

# handoff

## Goal

Add a manual `handoff` skill that the live session runs to write a short artifact a fresh session in any harness resumes from, triggered from Emacs with one harness-neutral sentence. Design and decisions: [docs/handoff-study.md](../../../docs/handoff-study.md).

## Non-Goals

- No hooks, Claude Code mods, or in-place conversation swap.
- No external or cheaper summarizer model.
- No herdr.el or limen change.
- No split panes; a new session always gets a new herdr workspace.
- No routing around OMP or Pi native `/handoff`.
- No `/compact` focus text or clear/compact/handoff routing rule.
- No change to `peer`, which never writes Git state.
- The stale skill count in `docs/henia-phora.md` stays as is.

## Invariants

| ID | Invariant | Check |
|----|-----------|-------|
| INV-1 | Skills reach all four harnesses only through `henia.toml` modes; `handoff` uses the `dynamic` default and joins no `hybrid` list | `rg -n 'handoff' henia.toml` is empty |
| INV-2 | `sweep` writes pointers only, never scope, transcript or diff content | review of `skills/sweep/SKILL.md` step 3 |
| INV-3 | `implement` and `test` report YAML keep their names and schemas | `git diff skills/implement skills/test` is empty |
| INV-4 | `peer path` never writes `.git/info/exclude` | `skills/peer/scripts/peer-layout-test` |

## Conventions

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Data & types | The FR-2 artifact template, stated verbatim in `skills/handoff/SKILL.md` | `skills/sweep/SKILL.md` step 3 fenced template |
| Errors | Context commands end in `2>/dev/null \|\| true` | `skills/continue/SKILL.md` |
| Effects | Writes only under `.tropos/handoff/`; the ignore rule per AD-3 | `skills/sweep/SKILL.md` |
| State | Local, untracked files under the session checkout's `.tropos/`, named by UTC timestamp | `.tropos/peer/<target>/<timestamp>-<id>/` run directories |
| Dependencies & boundaries | Henia `context_commands`; no new scripts in `handoff` | `skills/continue/SKILL.md` frontmatter |
| Naming | Skill `handoff`; files `.tropos/handoff/<UTC timestamp>.md` (`%Y%m%dT%H%M%SZ`) | `skills/sweep/SKILL.md` timestamp |
| Config & tooling | `henia lint`, `mise run test-artifacts` | `mise.toml` |
| Testing | Native linter and artifact check for Markdown; manual trigger run per harness | `tests/scrut/henia-artifacts.md` |
| Prose & output | Global contract: imperative, no bold, sparse italics | `instructions/AGENTS.md` |

## Decisions

- AD-1: Library-only dynamic skill with `auto_invoke: false`, read through `henia show handoff`; rejected per-harness slash commands: a spelling table and untested triggers (study D3).
- AD-2: The skill delivers the exact artifact path itself: no target starts a new session, a target receives a message (FR-4); rejected a constant newest-on-branch resume line: siblings on one branch race on it
- AD-3: One canonical `.tropos/` local-state rule in `skills/git/reference/local-state.md` that `sweep`, `issue` and `handoff` apply (FR-5); rejected a third copy of the ignore check: it already diverges between `sweep` and `issue`
- AD-5: `.tropos/handoff/` lives in the session's checkout (`git rev-parse --show-toplevel`), so a linked worktree keeps its own handoffs and the fresh pane starts in that checkout; rejected the main checkout as the only root: a successor in the worktree would then need a path outside its tree
- AD-6: An existing target receives `herdr agent message send`, a new session its prompt as the agent's launch argument; rejected `agent prompt` to an existing target: the herdr rule reserves it, and the target's user keeps authority
- AD-7: Starting an agent in a new workspace is a herdr skill procedure that `handoff` links to; rejected stating it in `handoff`: `peer` and `sweep` operate the same workspaces
- AD-4: `sweep` items gain a `Handoff:` pointer and its prose stops calling `.tropos/sweep.md` a handoff (FR-6); rejected `sweep` prompting each agent to write a handoff before closing it: a model turn per agent and no completion signal

## Context

### Key Files

| File | Lines | Role |
|------|-------|------|
| `docs/handoff-study.md` | all | Decided design |
| `skills/continue/SKILL.md` | 1-31 | Frontmatter exemplar: `auto_invoke`, `context_commands` |
| `skills/sweep/SKILL.md` | 3, 19, 48, 53, 56, 58, 60-73, 80, 88 | Handoff wording, pointer template, ignore rule |
| `skills/issue/SKILL.md` | 83 | Ignore rule prose |
| `skills/issue/scripts/issue` | 84-89, 199 | `_warn_unignored` |
| `skills/git/reference/` | — | Home of the new local-state rule |
| `tests/scrut/check-artifacts.py` | 49-50, 86-92 | Dynamic skills appear in the `henia` catalog, not the projected inventory |
| `skills/implement/reference/checkpoint-format.md` | 3-12 | Checkpoint `branch:` field |

### Constraints

- Artifact 750–2,000 tokens.
- Anchors come from rendered `context_commands`, never from model memory.

## Requirements

### Functional Requirements

- FR-1: `henia show handoff` MUST render, live: the current branch; `git rev-parse --short HEAD`; the path of every `scopes/*/*/checkpoint.yaml` whose `branch:` equals the current branch; and the path of the newest `.tropos/handoff/*.md` (the predecessor) whose `Branch:` line equals `Branch: <current branch>` as a whole fixed-string line (`grep -lxF`), else `none`.
- FR-2: The skill MUST state this artifact template verbatim and direct the model to fill it, 750–2,000 tokens, at `$(git rev-parse --show-toplevel)/.tropos/handoff/<UTC %Y%m%dT%H%M%SZ>.md`:

  ```markdown
  # Handoff: <purpose from the trigger>

  Branch: <rendered branch>
  HEAD: <rendered short HEAD>
  Predecessor: <rendered newest handoff path, or none>

  ## Goal and next step
  ## Constraints
  ## Decisions
  ## Tried and failed
  ## Not verified
  ```

  Goal and next step: the purpose, the next concrete step and its reason. Constraints: the user's constraints and exclusions verbatim; when `Predecessor:` is not `none`, the model MUST first read that file in full and carry forward each constraint still active. Decisions: each with its reason and rejected option. Tried and failed: each attempt with its cause. Not verified: each claim with its checking command, first `git status --short` and `git diff --stat <HEAD>`.
- FR-3: With one or more FR-1 checkpoints rendered, Goal and next step MUST name each checkpoint path and `continue` as the resume path, and no section restates waves or tasks.
- FR-4: After writing, the skill MUST deliver `Read <absolute artifact path> in full before any other action, and open your reply with its Handoff title.`: when the first trigger argument resolves with `herdr agent get`, as `herdr agent message send <target>`; otherwise by starting an agent of the session's own kind (`herdr agent get "$HERDR_PANE_ID"`, field `agent`) in a new herdr workspace at the checkout per the herdr skill, with that line as its launch prompt. Outside herdr (`HERDR_PANE_ID` unset) it prints the line. The remaining arguments are the purpose; without one, the model states the goal from the session.
- FR-7: The herdr skill MUST own one procedure: start an agent of a given kind in a new workspace (`herdr workspace create --cwd <dir> --label <label>`, then `herdr agent start <name> --kind <kind> --pane <its pane> -- <launch prompt>`), with timeout and failure reporting.
- FR-5: `skills/git/reference/local-state.md` MUST state once, for a named repository `<repo>`: when `git -C <repo> check-ignore -q .tropos/` fails, append `.tropos/` to `$(git -C <repo> rev-parse --git-common-dir)/info/exclude`. `sweep` and `handoff` MUST link to it, `issue` prose MUST link to it, and `issue`'s `_warn_unignored` MUST implement it instead of warning.
- FR-6: Each `sweep` item MUST carry `Handoff: <path>` for the newest `.tropos/handoff/*.md` under the item's worktree (else `R`) whose `Branch:` line equals the item's branch, omitted when none exists. `sweep` MUST rename every hand-off wording to pointer-index wording at lines 3, 19, 48, 53, 56, 80 and 88.

### Technical Requirements

- TR-1: `skills/handoff/SKILL.md` MUST pass `henia lint`.
- TR-2: `mise run test-artifacts` MUST pass, and the generated `henia` catalog of each of the four harnesses MUST name `handoff` (the `- \`handoff\`:` line that `tests/scrut/check-artifacts.py` checks for dynamic skills).
- TR-3: T002 MUST update `docs/handoff-study.md` design steps 1 and 6, D3, D4 and D6 to FR-4, AD-5 and AD-6.

## Acceptance Criteria

- [ ] AC-1 (FR-1): Given a checkout on `main` with handoffs whose `Branch:` lines are `main`, `feat/x` and `main-old`, when `henia show handoff` renders, then it names the newest `main` file; given none on the branch, it renders `none`.
- [ ] AC-2 (FR-2, FR-4, FR-7): Given a live session in each of Claude Code, Codex, Pi and OMP inside herdr, when the user sends `henia show handoff and follow it for: <purpose>`, then a file under the checkout's `.tropos/handoff/` matches the FR-2 template, a new workspace at the checkout runs the same harness, and its first reply opens with that file's `# Handoff:` title.
- [ ] AC-3 (FR-4): Given an existing agent's pane id or `agent_session` id as first argument, when the skill finishes, then that agent receives one herdr message with the FR-4 line and no workspace is created; with `HERDR_PANE_ID` unset, the line is printed.
- [ ] AC-4 (FR-2): Given a predecessor handoff with a constraint still active, when the skill writes a new handoff, then `Predecessor:` names it and Constraints repeats that constraint verbatim.
- [ ] AC-5 (FR-3): Given a rendered checkpoint on the current branch, when the skill writes the artifact, then Goal and next step names the checkpoint path and `continue`, and no section lists waves.
- [ ] AC-6 (FR-5): Given a repository where `.tropos/` is not ignored, when `issue draft` runs, then `.tropos/` is appended to `info/exclude` and `git status --short` shows no tracked change.
- [ ] AC-7 (FR-5): `rg -n 'check-ignore' skills --glob '*.md'` lists only `skills/git/reference/local-state.md` and `skills/git/reference/worktree.md`, and `rg -l 'git/reference/local-state.md' skills` lists `skills/sweep/SKILL.md`, `skills/issue/SKILL.md` and `skills/handoff/SKILL.md`.
- [ ] AC-8 (FR-6): `rg -n -i 'hand ?off' skills/sweep/SKILL.md` matches only the `Handoff:` pointer line in the step 3 template and the FR-6 lookup sentence; given an item in a linked worktree with a matching handoff there, the swept item names that path.
- [ ] AC-9 (TR-1, TR-2): `henia lint skills/handoff/SKILL.md` and `mise run test-artifacts` exit 0, and each harness's built `henia` catalog contains `` - `handoff`: ``.
- [ ] AC-10 (TR-3): `docs/handoff-study.md` matches FR-4, AD-5 and AD-6.
- [ ] AC-11 (FR-7): `henia show herdr` lists the new-workspace agent procedure, and `skills/handoff/SKILL.md` links to it instead of restating its commands.
