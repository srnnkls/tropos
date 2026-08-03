---
name: implement
description: Scope execution pipeline and implementation methodology. Use for executing scopes (TDD four-phase pipeline), verifying completion, debugging, or building features from requirements.
argument-hint: "[target]"
allowed-tools: Bash(find *), Bash(ls *), Bash(git *), Bash(gh *), Bash(peer *)
metadata:
  type: generic
---

## Pre-loaded Context

Active scopes:
!`find scopes -maxdepth 3 -name scope.md 2>/dev/null || true`

Checkpoints:
!`find scopes -name checkpoint.yaml -maxdepth 3 2>/dev/null || true`

Git status:
!`git status --short 2>/dev/null || true`

Current branch:
!`git branch --show-current 2>/dev/null || true`

# Implementation & Scope Execution

Executes scopes and tasks via a four-phase TDD pipeline (tester → test review → implementer → code review).

**INVARIANT: The orchestrator NEVER writes code or tests.** All code authoring — including test code — MUST be delegated to fresh subagents. This applies to ALL routes: scope execution, single tasks, file paths, and task descriptions. No exceptions.

---

## Auto-Detect Rules

**Pre-parse:** Extract these directives from `$ARGUMENTS` before pattern matching:
- `--config '<assignments>'` — non-interactive implementation-agent overrides. Supported keys are `tester`, `tester_effort`, `implementer`, `implementer_effort`, `reviewer`, and `reviewer_effort`; assignments are comma-separated and reviewer sets use `+`. Resolve and validate per [reference/configuration.md](reference/configuration.md).
- `--reviewers <aliases>` — legacy reviewer-only shorthand. Treat the comma-separated list as a `reviewer=<aliases joined with +>` implementation override; do not read or write `validation.yaml.review_config` for implementation routing.
- `--worktree` (or bare `worktree`) — checkout the determined branch as a `git worktree add ...` instead of in-place `git switch`. See "Git Workflow" → "Procedure" step 4.
- `--base <branch>` — base branch for new-branch creation. If absent and the branch doesn't exist, AskUserQuestion. See "Git Workflow" → "Procedure" step 3.
- `--state <draft|open>` — PR state when auto-creating a pull request at the end of execution (default: `draft`). Only used when `$ARGUMENTS` contains an issue reference.
- `gh:<n>`, `#<n>`, or a GitHub issue URL — flags GitHub-issue branch naming AND enables auto-PR creation after final review. See "Git Workflow" → "Branch Determination" and `operations/execute.md` Step 10.

Apply these rules to remaining `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| Starts with `config` | Configure | Resolve the scope and update its `config.yaml` per `reference/configuration.md`; preserve the current epoch |
| "verify" or "done" | Verify | Read and follow `operations/verify.md` |
| "debug" or "trace" | Debug | Read and follow `operations/debug.md` |
| Matches `./scopes/*/*/` path | Execute | Read and follow `operations/execute.md` |
| Exactly one active scope | Execute | Read and follow `operations/execute.md` |
| File path or task description | Direct | Use methodology below |
| No argument | Menu | See fallback |

---

## Menu Fallback

When no argument or ambiguous, use **AskUserQuestion**:

```
Header: Implement
Question: What would you like to do?
multiSelect: false
Options:
- Scope execution: Execute active scope with TDD pipeline (tester → implementer → reviewer)
- Verify: Evidence-based verification before claiming done
- Debug: Root cause tracing for a bug or failure
- Implement: Single implementation task with methodology below
```

**Routing by selection:**

| Selection | Action |
|---|---|
| Scope execution | Read and follow `operations/execute.md` |
| Verify | Read and follow `operations/verify.md` |
| Debug | Read and follow `operations/debug.md` |
| Implement | Use methodology below |

---

## When to Use

- Executing a scope's tasks via the four-phase pipeline
- Building features from requirements
- Writing code or creating artifacts
- Deciding on structure, patterns, or approach
- Designing domain models or data structures
- Verifying completion or debugging failures

---

## Git Workflow

**MANDATORY:** The dispatcher MUST ensure a dedicated branch is checked out before dispatching any phase. Never run implementation phases on `main`/`master` or on an unrelated branch.

### Branch Determination

Detect the branch source from `$ARGUMENTS` and apply the matching naming convention:

| Source | Detection | Branch Name | Example |
|---|---|---|---|
| GitHub issue | `gh:<n>`, `#<n>`, or `github.com/<owner>/<repo>/issues/<n>` | `<issue#>-<issue-title-in-kebab-case>` | `142-add-user-auth` |
| Scope | `./scopes/<state>/<name>/` path or active scope | `feat/<scope-name>` | `feat/user-auth` |
| Direct task | File path or task description, no scope/issue | **AskUserQuestion** (see below) | — |

**For GitHub issues:** Fetch the title with `gh issue view <n> --json title -q .title`, kebab-case it (lowercase, spaces/punctuation → `-`, collapse repeats, trim), then prefix with the issue number. Do NOT add a `feat/` prefix — match GitHub's own branch convention.

### Procedure

1. **Determine branch name** per the table above.
2. **If source is unclear or ambiguous** (no scope, no issue ref, multiple candidates) → **AskUserQuestion**:
   ```
   Header: Branch
   Question: No branch detected for this work. How should I proceed?
   multiSelect: false
   Options:
   - Use current branch: <current-branch>
   - Create new branch: provide name
   - GitHub issue: provide issue number
   ```
3. **Resolve base branch** (only needed when creating a new branch):
   - Skip if branch already exists locally or on remote.
   - If `--base <branch>` was passed in `$ARGUMENTS` → use it.
   - Else → **AskUserQuestion**:
     ```
     Header: Base branch
     Question: New branch <name> needs a base. Which branch should it fork from?
     multiSelect: false
     Options:
     - origin/<trunk> (freshly fetched trunk — default)
     - <current-branch> (current — pick if cascading)
     - Other: provide branch name
     ```
   - **Never fork from local `main`/`master`** — it may be stale. When the base is the trunk, `git fetch origin <trunk>` and use `origin/<trunk>`.
   - Verify the base exists (`git rev-parse --verify <base>`) before proceeding.
4. **Checkout mode** — pre-parse `--worktree` (or `worktree`) from `$ARGUMENTS`:
   - **Worktree directive present** → follow `skills/git/reference/worktree.md` end-to-end with `BRANCH_NAME=<branch>` from step 1 and the resolved base from step 3. All subsequent phases run from the reported worktree path.
   - **No worktree directive** → in-place checkout:
     - Branch exists locally → `git switch <name>` and pull latest
     - Branch exists on remote → `git switch <name>` (tracks remote)
     - Otherwise → `git switch -c <name> <base>` using the resolved base from step 3
5. **Verify** current working tree is on the determined branch before dispatching Phase A.
6. **Base-drift preflight** — skip ONLY when step 4 just created the branch from a **freshly fetched remote ref** (`origin/<trunk>`); a branch created from any local ref, or created earlier by an outside tool (`workon`, `gh issue develop`, manual checkout), can already be behind — run the check via `reference/base-drift-preflight.md`, which fetches `origin/<trunk>` fresh, measures divergence, and gates on overlap. **Do not dispatch Phase A past a non-empty overlap without a user decision.**

**Never** dispatch testers/implementers/reviewers while still on `main`, `master`, a stale unrelated branch, or a branch whose base drifted with unresolved overlapping changes.

---

## Process (Single-Task Pipeline)

**The orchestrator NEVER writes code or tests.** All code authoring is delegated to subagents.

Even for a single task, the four-phase pipeline applies:

Before the first dispatch, resolve an ephemeral agent configuration per
`reference/configuration.md`. Supplying `--config` skips setup prompts; otherwise prompt for
tester, implementer, and reviewer routing. Do not write a repository-level config for a direct
task. Reload the in-memory configuration before each phase just as a scope run reloads
`config.yaml`. Enforce same-host-family native routing during both interactive and inline setup;
reject host-family loopback through peer and ask for edits rather than silently converting.

### Phase A: Dispatch Tester Subagent

Dispatch a **fresh tester agent** to write failing tests. Route `codex-native` through Codex's
native delegation interface with inherited session settings, `opus`/`sonnet` through
`Task(subagent_type: "tester", model: <alias>)`, and external aliases through `peer --agent tester`.

- Tester reads task requirements and discovers expected behavior independently
- Tester writes tests and verifies RED state
- Orchestrator verifies RED (see Quality Gates in `operations/execute.md`)

### Phase A.5: Test Review Gate

Reload routing, then dispatch every configured native reviewer through its host-native mechanism
and fan configured external reviewers through one `peer --agent reviewer` call. Require one
success from each execution class actually configured; an all-native or all-external gate does not
require the absent class.

- Reviewers check for oracle mirroring, mock tautologies, framework tests, trivial assertions
- Synthesize findings: a test is flagged if any harness reports `issues_found`
- If issues found → re-dispatch tester with specific feedback; repeat until clean
- **Gate:** Implementer NEVER receives tests that failed this review

See dispatch template in `reference/subagent-workflow.md` — Test Review Dispatch Template.

### Phase B: Dispatch Implementer Subagent

Dispatch a **fresh implementer agent** with the test-review-cleared tester report. Route
`codex-native` through Codex native delegation with inherited settings, explicit native aliases
through `Task(subagent_type: "implementer", model: <alias>)`, and external aliases through
`peer --agent implementer`.

- Implementer makes tests pass (GREEN)
- Implementer refactors while staying green

### Phase C: Review

Review is mandatory. Reload routing and use the configured native and external reviewer set.

For external tester or implementer failure, preserve partial edits, record worktree status/diff,
mark the phase incomplete, and pause. Do not retry, roll back, or advance automatically.

### Dispatch Templates

Use the tester and implementer dispatch templates from `reference/subagent-workflow.md`.

### Red Flags

**If you catch yourself writing test code or implementation code directly: STOP.**
You are the orchestrator. You dispatch. You verify. You do not author.

---

## Domain Context

Domain skills inject specifics into this generic methodology:
- **code**: Language guidelines (loqui), code intelligence (gestalt), review roles
- **doc**: Templates, structure, style guides

When invoked via a domain skill, follow the domain-specific guidance provided.

---

## Related Skills

- **dispatch**: Intent router — routes to this skill for execution
- **test**: TDD workflow (write test first, then implement)
- **continue**: Resume from checkpoint
- **review**: Review methodology for completed work

---

## Reference

- [operations/execute.md](operations/execute.md) — Four-phase scope execution pipeline
- [operations/verify.md](operations/verify.md) — Evidence-based completion verification
- [operations/debug.md](operations/debug.md) — Root cause tracing
- [reference/report.md](reference/report.md) — Report format
- [reference/review.md](reference/review.md) — Review workflow
- [reference/checkpoint-format.md](reference/checkpoint-format.md) — Checkpoint format
- [reference/configuration.md](reference/configuration.md) — Live implementation-agent routing
- [reference/subagent-workflow.md](reference/subagent-workflow.md) — Subagent workflow
- [reference/base-drift-preflight.md](reference/base-drift-preflight.md) — Base-drift / overlap gate before dispatch
- [reference/parallel-detection.md](reference/parallel-detection.md) — Parallel detection
- [reference/defense-in-depth.md](reference/defense-in-depth.md) — Defense in depth
- [reference/root-cause-tracing.md](reference/root-cause-tracing.md) — Root cause tracing
- [reference/roles/](reference/roles/) — Tester, implementer, reviewer role definitions
