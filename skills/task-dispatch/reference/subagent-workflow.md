# Subagent Workflow Details

## Task Batching

Before dispatching, analyze `dependencies.yaml` for execution batches:

1. Parse task dependency graph
2. Identify `[P]` markers (parallelizable within same phase)
3. Group consecutive `[P]` tasks that modify different files
4. Non-`[P]` tasks form single-task batches
5. Phase boundaries force batch breaks

## Three-Phase Pipeline

**Each batch executes three mandatory phases:**

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase A: TESTERS                                               │
│  ├── Writes failing tests (RED)                                 │
│  └── Reports test paths + failure output                        │
│                          ↓                                      │
│  Phase B: IMPLEMENTERS                                          │
│  ├── Receives tester's report                                   │
│  ├── Makes tests pass (GREEN)                                   │
│  └── Reports impl files + pass output                           │
│                          ↓                                      │
│  Phase C: REVIEWERS                                             │
│  ├── Reviews ALL changes from batch                             │
│  ├── Checks against spec requirements                           │
│  └── Reports issues by severity                                 │
└─────────────────────────────────────────────────────────────────┘
```

**CRITICAL:** All three phases are mandatory. A batch is not complete until reviewers finish.

---

## Tester Dispatch Template

```yaml
Task:
  subagent_type: general
  description: "Write tests for Task N: [task name]"
  prompt: |
    You are writing failing tests for Task N from [spec-file].

    ## TDD Methodology
    Follow RED-GREEN-REFACTOR: write failing tests first, then minimal code to pass.

    ## Language Conventions
    Read `./skills/code-implement/resources/loqui/languages/{lang}/README.md` for language-specific test conventions (NOT for writing implementation code — that is the implementer's job).

    **Task requirements:**
    [paste task from tasks.yaml including test_hints]

    **Your job:**
    1. Read the task requirements and test_hints
    2. Write tests that cover all specified behaviors
    3. Tests must FAIL (features not implemented yet)
    4. Run tests to verify RED state

    **Work from:** [directory]

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    tester_report:
      status: success  # or "gap" if cannot write tests
      test_files:
        - path: [test file path]
          tests: [list of test names]
      failure_output: |
        [last 20 lines of test failure output only]
      gap_reason: null  # or explanation if status=gap
    ```
```

**For parallel batch (N tasks):**
Dispatch ALL testers in a SINGLE message:

```yaml
# Single message with multiple Task tool calls
Task (general): "Write tests for Task N1" ...
Task (general): "Write tests for Task N2" ...
Task (general): "Write tests for Task N3" ...
```

Wait for ALL testers to complete before dispatching implementers.

---

## Implementer Dispatch Template

**PRECONDITION:** Tester for this task completed with `status: success`. The tester_report YAML below is REQUIRED — if missing, dispatch the tester first.

```yaml
Task:
  subagent_type: general
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N from [spec-file].

    ## Language Guidelines
    Read `./skills/code-implement/resources/loqui/languages/{lang}/README.md` for language-specific conventions.

    **Tests written by tester:**
    ```yaml
    [paste tester_report YAML]
    ```

    **Your job:**
    1. Run the tests to see current failures
    2. Write minimal code to make tests pass (GREEN)
    3. If requirements are ambiguous, use AskUserQuestion
    4. Refactor while keeping tests green

    **Work from:** [directory]

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    implementer_report:
      status: success  # or "blocked" if cannot proceed
      implementation_files:
        - path: [impl file path]
      test_output: |
        [last 20 lines of test output only]
      clarifications:
        - question: [if used AskUserQuestion]
          answer: [user's response]
      blocked_reason: null  # or explanation if status=blocked
    ```
```

**For parallel batch (N tasks):**
Dispatch ALL implementers in a SINGLE message, each with its corresponding tester report:

```yaml
# Single message with multiple Task tool calls
Task (general): "Implement Task N1" + tester_1_report
Task (general): "Implement Task N2" + tester_2_report
Task (general): "Implement Task N3" + tester_3_report
```

Wait for ALL implementers to complete before dispatching reviewers.

---

## Reviewer Dispatch Template

**CRITICAL:** Reviewers are mandatory. Every batch gets reviewed. Three roles, multiple harnesses.

**Step 1: Resolve batch diff**
```bash
# last_batch_commit from checkpoint.yaml (or initial branch point for first batch)
# diff_cmd: "git diff <last_batch_commit>..HEAD"
# range: <last_batch_commit>..HEAD   (for gestalt diff)
```

**Step 2: Dispatch ALL role × harness combinations in a SINGLE message:**

Reviewers receive pointers (diff command, file paths) and load code themselves. No content is pasted inline.

**Variables for all reviewer prompts:**
- `{diff_cmd}` — full command, e.g., `git diff abc123f..HEAD`
- `{range}` — git range for gestalt, e.g., `abc123f..HEAD`
- `{workdir}` — repo root or worktree path
- `{scope_dir}` — scope directory path (e.g., `./scopes/cache`)
- `{task_ids}` — task IDs in this batch (e.g., `T001, T002`)
- `{batch_n}` — batch number

```yaml
# Single message — full cartesian product in parallel
# For each role, dispatch Claude harness + all OpenCode harnesses

# ── General role — Claude harness [REQUIRED] ──
Task:
  subagent_type: general
  description: "General review: Tasks {task_ids}"
  prompt: |
    You are the GENERAL reviewer. Your gates: Correctness, Security, Performance.

    ## What to Review

    Working directory: {workdir}
    Run: `{diff_cmd}`

    Context: Batch {batch_n} review — tasks {task_ids}

    Read `{scope_dir}/tasks.yaml` for task requirements.

    ## Your Gates

    1. Correctness - Logic errors, edge cases, error handling
    2. Performance - Efficiency, data structures
    3. Security - Input validation, secrets, injection risks

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    reviewer_report:
      reviewer: general-claude-opus
      role: general
      batch: {batch_n}
      diff_reviewed: true
      gates:
        correctness: { status: pass | fail, issues: [] }
        performance: { status: pass | fail, issues: [] }
        security: { status: pass | fail, issues: [] }
      issues:
        - task: T001
          severity: critical | high | medium
          gate: correctness
          location: "file:line"
          description: "Clear description"
          suggestion: "How to fix"
      strengths:
        - "Positive observation"
    ```

# ── General role — OpenCode harnesses [0-N from validation.yaml] ──
Bash:
  command: timeout 1200 opencode run --model "openai/gpt-5.3-codex" --variant {reasoning_effort}-medium "{general_review_prompt}"
  run_in_background: true

Bash:
  command: timeout 1200 opencode run --model "google/gemini-3-pro-preview" --variant {reasoning_effort}-medium "{general_review_prompt}"
  run_in_background: true

# ── Architecture role — Claude harness [REQUIRED] ──
Task:
  subagent_type: general
  description: "Architecture review: Tasks {task_ids}"
  prompt: |
    You are the ARCHITECTURE reviewer. Your gate: Architecture.

    ## What to Review

    Working directory: {workdir}
    Run: `{diff_cmd}`

    Context: Batch {batch_n} review — tasks {task_ids}

    ## Structural Analysis (run these from {workdir})

    1. `gestalt analyze` — current architecture
    2. `gestalt diff {range}` — definition-level changes
    3. `gestalt diff {range} --verbose` — impact propagation
    4. Additional `gestalt callers/callees/refs/rank` as needed

    ## Review Focus

    1. Coupling — inter-module coupling changes?
    2. Hotspots — new high-centrality symbols?
    3. Cycles — dependency cycles introduced?
    4. Seams — cluster boundaries respected?
    5. Impact — propagation radius of changes?

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    reviewer_report:
      reviewer: architecture-claude-opus
      role: architecture
      batch: {batch_n}
      diff_reviewed: true
      gates:
        architecture: { status: pass | fail, issues: [] }
      structural_analysis:
        coupling_delta: increased | stable | decreased
        new_hotspots: [{ symbol: "name", file: "path", in_degree: N }]
        cycles_introduced: [{ members: ["A", "B"] }]
        seam_violations: [{ symbol: "name", expected_cluster: "X", actual_cluster: "Y" }]
        impact_radius: N
      issues:
        - severity: critical | high | medium
          gate: architecture
          area: coupling
          location: "file:line"
          description: "Clear description"
          suggestion: "How to fix"
      strengths:
        - "Positive observation"
    ```

# ── Architecture role — OpenCode harnesses [0-N from validation.yaml] ──
Bash:
  command: timeout 1200 opencode run --model "openai/gpt-5.3-codex" --variant {reasoning_effort}-medium "{architecture_review_prompt}"
  run_in_background: true

Bash:
  command: timeout 1200 opencode run --model "google/gemini-3-pro-preview" --variant {reasoning_effort}-medium "{architecture_review_prompt}"
  run_in_background: true

# ── Compliance role — Claude harness [REQUIRED] ──
Task:
  subagent_type: general
  description: "Compliance review: Tasks {task_ids}"
  prompt: |
    You are the COMPLIANCE reviewer. Your gate: Style.

    ## What to Review

    Working directory: {workdir}
    Run: `{diff_cmd}`

    Context: Batch {batch_n} review — tasks {task_ids}

    ## Loqui Guidelines

    1. Detect language(s) from file extensions in the diff
    2. Read `./skills/code-implement/resources/loqui/languages/{lang}/README.md`
    3. Read topic files relevant to the changes (quality.md, composition.md, modules.md, errors.md)

    ## Review Focus

    1. Naming — 5x rule, descriptive names?
    2. Composition — composition over inheritance?
    3. Modules — feature-based organization?
    4. Errors — language-idiomatic error handling?
    5. Anti-patterns — items from language README checklist?

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    reviewer_report:
      reviewer: compliance-claude-opus
      role: compliance
      batch: {batch_n}
      diff_reviewed: true
      gates:
        style: { status: pass | fail, issues: [] }
      compliance_analysis:
        languages_checked: [python]
        rules_evaluated: N
        violations:
          - rule: "naming/5x-rule"
            source: "python/quality.md"
            location: "file:line"
            description: "Description"
            suggestion: "Fix"
      issues:
        - severity: critical | high | medium
          gate: style
          area: naming
          location: "file:line"
          description: "Clear description"
          suggestion: "How to fix"
      strengths:
        - "Positive observation"
    ```

# ── Compliance role — OpenCode harnesses [0-N from validation.yaml] ──
Bash:
  command: timeout 1200 opencode run --model "openai/gpt-5.3-codex" --variant {reasoning_effort}-medium "{compliance_review_prompt}"
  run_in_background: true

Bash:
  command: timeout 1200 opencode run --model "google/gemini-3-pro-preview" --variant {reasoning_effort}-medium "{compliance_review_prompt}"
  run_in_background: true
```

Wait for ALL role × harness combinations to complete before synthesizing.

**validation.yaml configuration:**
```yaml
review_config:
  reasoning_effort: high  # low | medium | high | xhigh (user-selected, xhigh GPT-5.2 only)
  roles:
    general: true       # always true
    architecture: true   # gestalt-based
    compliance: true     # loqui-based
  harnesses:
    - openai/gpt-5.3-codex          # OpenCode (applied to ALL roles)
    - google/gemini-3-pro-preview    # OpenCode (applied to ALL roles)
  # Empty harnesses list = Claude-only review (all 3 roles still run)
  # Variant = {reasoning_effort}-medium
  # Full dispatch = roles × (1 Claude + len(harnesses) OpenCode)
```

---

## Review Synthesis

After all role × harness combinations complete:

1. **Parse reports** - Extract YAML from all outputs (including `structural_analysis` and `compliance_analysis`)
2. **Group by role** - Aggregate harness results within each role first
3. **Merge issues within role:**
   - Deduplicate across Claude + OpenCode harnesses within each role
   - Issues flagged by multiple harnesses = higher confidence
4. **Merge issues across roles:**
   - Deduplicate by location + description similarity
   - Preserve role attribution
5. **Aggregate gates:**
   - Each role owns its gates (General: Correctness/Security/Performance, Architecture: Architecture, Compliance: Style)
   - Gate fails if ANY harness within the owning role fails it
6. **Aggregate severity:**
   - Issue severity is the HIGHEST across all harnesses
   - Critical by any harness = Critical overall

**Gate Summary Table (by role):**

```
| Gate         | Status | General | Architecture | Compliance |
|--------------|--------|---------|--------------|------------|
| Correctness  | FAIL   | fail (Codex)          | —            | —          |
| Style        | PASS   | —                     | —            | pass       |
| Performance  | PASS   | pass                  | pass         | —          |
| Security     | FAIL   | fail (Claude, Gemini) | —            | —          |
| Architecture | PASS   | —                     | pass         | —          |
```

`—` = not in scope for this role. On failure, note which harness(es) failed.

**Issues by Severity:**

```
## Critical (found by 2+ harnesses — high confidence)
- [C1] SQL injection in user input at src/db/query.py:45
  Role: General | Failed by: Claude, Gemini
  Suggestion: Use parameterized queries

## High
- [H1] Missing null check at src/api/handler.ts:112
  Role: General | Failed by: Codex
  Suggestion: Add guard clause
```

---

## Fix Subagent Template

When review finds Critical/High issues:

```yaml
Task:
  subagent_type: general
  description: "Fix issues from batch review"
  prompt: |
    Fix these issues from code review:

    **Issues to fix:**
    ```yaml
    [paste relevant issues from synthesized review]
    ```

    Make targeted fixes only. Don't refactor beyond what's needed.
    Run tests to verify fixes don't break anything.

    **OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
    No prose, no explanation, no summary. The full subagent conversation gets embedded
    into the parent session context — every extra token costs budget.

    **Report in YAML format:**
    ```yaml
    fix_report:
      status: success
      fixes_applied:
        - issue: [description]
          fix: [what you did]
      test_output: |
        [last 20 lines of test output only]
    ```
```

After fixes, dispatch targeted review (can be single Claude reviewer for speed).

---

## Workflow Diagram (Three-Phase Pipeline)

```
Load Spec + dependencies.yaml
    |
    v
Build Execution Batches
    |
    v
[For each batch]
    |
    +--> Single task?
    |         |
    |    YES: Phase A: Dispatch 1 tester (opus)
    |         Phase B: Dispatch 1 implementer (opus)
    |         Phase C: Dispatch reviewers (roles × harnesses, parallel)
    |         |
    |    NO (parallel [P] tasks):
    |         Phase A: Dispatch N testers (single message)
    |         Phase B: Dispatch N implementers (single message)
    |         Phase C: Dispatch reviewers (roles × harnesses, single message)
    |         |
    |         v
    +--> Synthesize Reviews
    |         |
    |         v
    |    Critical/High Issues? --YES--> Dispatch Fix Subagent(s)
    |         |                              |
    |         NO                             v
    |         |                        Targeted Review
    |         v                              |
    |    Commit Batch <----------------------+
    |         |
    v         v
[Next Batch]
    |
    v
Final Review (roles × harnesses in parallel)
    |
    v
Done

(roles × harnesses = {General, Architecture, Compliance} × {Claude + N OpenCode models})
```

---

## Handling Tester Gaps

If tester reports `status: gap`:

1. Read `gap_reason` from tester's report
2. Consult scope (tasks.yaml, scope.md) for clarification
3. If still unclear, use AskUserQuestion to clarify with user
4. Re-dispatch tester with additional context:

```yaml
Task:
  subagent_type: general
  description: "Write tests for Task N (clarified)"
  prompt: |
    Previous attempt reported gap: [gap_reason]

    **Clarification received:**
    [additional context or user's answer]

    Now write tests with this clarified understanding.
    [rest of tester template]
```

---

## Handling Reviewer Timeouts

If OpenCode reviewer times out (> 5 minutes):

1. Continue with completed reviews (minimum 1 required)
2. Add warning to output:
   ```
   Note: [Reviewer] timed out after 5 minutes.
   Results are from available reviewers only.
   ```
3. Proceed with synthesis using available data
4. Consider re-running batch if only 1 reviewer completed

---

## Best Practices

1. **subagent_type: general** - Use `general` for all task subagents
2. **Tester first** - Implementer must receive failing tests
3. **All three roles mandatory** - Every batch gets General + Architecture + Compliance review
4. **YAML reports** - Structured handoff between phases
5. **Single message dispatch** - All role × harness combinations in one message
6. **Fresh context** - Each subagent starts clean
7. **Track progress** - Update TodoWrite after each phase
8. **Configure harnesses** - Set OpenCode models in validation.yaml (applied to ALL roles)
9. **Minimize subagent output** - Subagent final messages get embedded into parent context (duplicated in `.output` and `.result`). Every extra token directly inflates parent context. Subagents must return ONLY the YAML report — no prose, no explanation.
