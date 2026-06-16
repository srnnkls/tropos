---
name: implement
description: Scope execution pipeline and implementation methodology. Use for executing scopes (TDD three-phase pipeline), verifying completion, debugging, or building features from requirements.
argument-hint: "[target]"
metadata:
  type: generic
---

## Pre-loaded Context

Active scopes:
!`find scopes -maxdepth 3 -name scope.md 2>/dev/null`

Checkpoints:
!`find scopes -name checkpoint.yaml -maxdepth 3 2>/dev/null`

Git status:
!`git status --short 2>/dev/null`

Current branch:
!`git branch --show-current 2>/dev/null`

Base drift (behind-count + overlapping files vs trunk):
!`b=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@.*/@@'); b=${b:-main}; git fetch origin "$b" --quiet 2>/dev/null; mb=$(git merge-base "origin/$b" HEAD 2>/dev/null); behind=$(git rev-list --count "HEAD..origin/$b" 2>/dev/null); echo "base=$b behind=${behind:-?}"; if [ "${behind:-0}" -gt 0 ]; then echo "-- base changed since fork --"; git diff --name-only "HEAD...origin/$b" 2>/dev/null; echo "-- this branch changed --"; git diff --name-only "$mb" HEAD 2>/dev/null; fi`

# Implementation & Scope Execution

Executes scopes and tasks via three-phase TDD pipeline (tester → implementer → reviewer).

**INVARIANT: The orchestrator NEVER writes code or tests.** All code authoring — including test code — MUST be delegated to fresh subagents. This applies to ALL routes: scope execution, single tasks, file paths, and task descriptions. No exceptions.

---

## Auto-Detect Rules

**Pre-parse:** Extract these directives from `$ARGUMENTS` before pattern matching:
- `--reviewers <aliases>` — comma-separated list from `{opus, sonnet, gpt, gemini}`. Resolution and alias table: `/review` SKILL.md "Reviewer Selection". Resolved list is passed to Phase A.5 + Phase C dispatch. If absent and `validation.yaml.review_config` is also absent, fall back to the interactive AskUserQuestion prompt (same as `/review`).
- `--worktree` (or bare `worktree`) — checkout the determined branch as a `git worktree add ...` instead of in-place `git switch`. See "Git Workflow" → "Procedure" step 4.
- `--base <branch>` — base branch for new-branch creation. If absent and the branch doesn't exist, AskUserQuestion. See "Git Workflow" → "Procedure" step 3.
- `--state <draft|open>` — PR state when auto-creating a pull request at the end of execution (default: `draft`). Only used when `$ARGUMENTS` contains an issue reference.
- `gh:<n>`, `#<n>`, or a GitHub issue URL — flags GitHub-issue branch naming AND enables auto-PR creation after final review. See "Git Workflow" → "Branch Determination" and `operations/execute.md` Step 10.

Apply these rules to remaining `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
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

- Executing a scope's tasks via three-phase pipeline
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
   - **Never fork from local `main`/`master`** — it may be stale (this is how branches are born already behind). When the base is the trunk, `git fetch origin <trunk>` and use `origin/<trunk>`.
   - Verify the base exists (`git rev-parse --verify <base>`) before proceeding.
4. **Checkout mode** — pre-parse `--worktree` (or `worktree`) from `$ARGUMENTS`:
   - **Worktree directive present** → follow `skills/git/reference/worktree.md` end-to-end with `BRANCH_NAME=<branch>` from step 1 and the resolved base from step 3. All subsequent phases run from the reported worktree path.
   - **No worktree directive** → in-place checkout:
     - Branch exists locally → `git switch <name>` and pull latest
     - Branch exists on remote → `git switch <name>` (tracks remote)
     - Otherwise → `git switch -c <name> <base>` using the resolved base from step 3
5. **Verify** current working tree is on the determined branch before dispatching Phase A.
6. **Base-drift preflight** — skip ONLY when step 4 just created the branch from a **freshly fetched remote ref** (`origin/<trunk>`); a branch created from any local ref, or created earlier by an outside tool (`workon`, `gh issue develop`, manual checkout), can already be behind — run the check. Read the `Base drift` block in Pre-loaded Context. If `behind > 0`, follow `reference/base-drift-preflight.md` to detect overlap and gate. **Do not dispatch Phase A past a non-empty overlap without a user decision.**

**Never** dispatch testers/implementers/reviewers while still on `main`, `master`, a stale unrelated branch, or a branch whose base drifted with unresolved overlapping changes.

---

## Process (Single-Task Pipeline)

**The orchestrator NEVER writes code or tests.** All code authoring is delegated to subagents.

Even for a single task, the four-phase pipeline applies:

### Phase A: Dispatch Tester Subagent

Dispatch a **fresh tester subagent** (`subagent_type: "task-tester"`) to write failing tests.

- Tester reads task requirements and discovers expected behavior independently
- Tester writes tests and verifies RED state
- Orchestrator verifies RED (see Quality Gates in `operations/execute.md`)

**Why a separate subagent?** The orchestrator's understanding of the task leaks into hand-written tests, causing oracle mirroring (tests that mirror implementation logic) and mock tautologies (mocks that assume the answer). A fresh subagent discovers behavior from code and specs independently.

### Phase A.5: Test Review Gate

Dispatch a Claude `Task` **plus one `peer run`** (which fans out to all configured external reviewers) on the test files from Phase A. Same shape as Phase C; never shell out to codex/gemini directly. External reviewers via `peer run` are mandatory — read its manifest, require ≥1 external `ok`.

- Reviewers check for oracle mirroring, mock tautologies, framework tests, trivial assertions
- Synthesize findings: a test is flagged if any harness reports `issues_found`
- If issues found → re-dispatch tester with specific feedback; repeat until clean
- **Gate:** Implementer NEVER receives tests that failed this review

See dispatch template in `reference/subagent-workflow.md` — Test Review Dispatch Template.

### Phase B: Dispatch Implementer Subagent

Dispatch a **fresh implementer subagent** (`subagent_type: "task-implementer"`) with the test-review-cleared tester report.

- Implementer makes tests pass (GREEN)
- Implementer refactors while staying green

### Phase C: Review

For single tasks, review can be done inline or via reviewer subagent(s) depending on scope.

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

- [operations/execute.md](operations/execute.md) — Three-phase scope execution pipeline
- [operations/verify.md](operations/verify.md) — Evidence-based completion verification
- [operations/debug.md](operations/debug.md) — Root cause tracing
- [reference/report.md](reference/report.md) — Report format
- [reference/review.md](reference/review.md) — Review workflow
- [reference/checkpoint-format.md](reference/checkpoint-format.md) — Checkpoint format
- [reference/subagent-workflow.md](reference/subagent-workflow.md) — Subagent workflow
- [reference/base-drift-preflight.md](reference/base-drift-preflight.md) — Base-drift / overlap gate before dispatch
- [reference/parallel-detection.md](reference/parallel-detection.md) — Parallel detection
- [reference/defense-in-depth.md](reference/defense-in-depth.md) — Defense in depth
- [reference/root-cause-tracing.md](reference/root-cause-tracing.md) — Root cause tracing
- [reference/roles/](reference/roles/) — Tester, implementer, reviewer role definitions
