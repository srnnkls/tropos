# Checkpoint Format

## Location

```
./scopes/<state>/<scope-name>/checkpoint.yaml
```

Where `<state>` is the scope's lifecycle dir: `draft`, `active`, or `done`. Most checkpoints live under `active/` since checkpoints are written when work is in progress.

## Schema

```yaml
checkpoint:
  # Metadata
  scope_name: auth-system
  scope_path: ./scopes/active/auth-system
  branch: feat/auth-system
  timestamp: 2026-01-22T14:30:00Z

  # Progress
  last_batch: 2
  last_commit: a1b2c3d4

  # Task status summary (mirrors tasks.yaml)
  tasks:
    done:
      - id: T001
        name: "Add user model"
      - id: T002
        name: "Add authentication endpoint"
    in_progress: []
    pending:
      - id: T003
        name: "Add session management"
      - id: T004
        name: "Add logout endpoint"

  # Next batch info
  next_batch:
    number: 3
    tasks:
      - id: T003
        name: "Add session management"
        files: [src/auth/session.py]
    parallel: false

  # Deferred issues (medium severity, noted for later)
  deferred_issues:
    - batch: 2
      severity: medium
      description: "Variable naming could be clearer in auth.py"
      location: "src/auth/auth.py:45"

  # Live routing is not duplicated here. Resume reads this file before every dispatch.
  implementation_config:
    path: ./scopes/active/auth-system/config.yaml
    epoch_id: 20260719T123456Z-a1b2c3

  # Durable pipeline position. This is authoritative once incomplete_stages is empty.
  phase_cursor:
    batch: 3
    phase: test_review  # tester | test_review | implementer | code_review | fix |
                        # targeted_review | final_review | complete
    status: in_progress  # pending | in_progress | completed | failed
    tasks: [T003, T004]
    updated_at: 2026-07-19T12:48:00Z
    # Used by test_review and targeted_review. One entry per configured alias.
    reports:
      - agent: opus
        status: ok  # pending | in_progress | ok | failed
        report_dir: .peer/auth-system/20260719T123456Z-a1b2c3/b3-test-review
        report_file: opus.yaml
      - agent: gpt
        status: failed
        report_dir: .peer/auth-system/20260719T123456Z-a1b2c3/b3-test-review
        report_file: gpt.yaml
    # Used by code_review and final_review. Preserve completed roles independently.
    roles:
      general:
        status: completed  # pending | in_progress | completed | failed
        report_dir: .peer/auth-system/20260719T123456Z-a1b2c3/b3-review-general
        reports:
          - {agent: opus, status: ok}
          - {agent: gpt, status: ok}
      architecture:
        status: in_progress
        report_dir: .peer/auth-system/20260719T123456Z-a1b2c3/b3-review-architecture
        reports:
          - {agent: opus, status: ok}
          - {agent: gpt, status: failed}
      compliance:
        status: pending
        report_dir: .peer/auth-system/20260719T123456Z-a1b2c3/b3-review-compliance
        reports: []

  # Recovery markers for mutating tester/implementer/fix dispatches. Empty at a clean gate.
  incomplete_stages:
    - batch: 3
      task: T003
      phase: implementer  # tester | implementer | fix
      agent: gpt
      report_dir: .peer/auth-system/20260719T123456Z-a1b2c3/b3-implementer-T003
      status: failed  # in_progress | failed
      started_at: 2026-07-19T12:45:00Z
      updated_at: 2026-07-19T12:47:00Z
      evidence:
        pre_dispatch:
          git_status: |
            M src/auth/session.py
          git_diff: |
            <relevant pre-dispatch diff or "clean">
        post_failure:
          git_status: |
            M src/auth/session.py
          git_diff: |
            <relevant post-failure diff>
      failure: "peer exited without a valid implementer_report"
```

## Writing Checkpoints

Persist recovery state throughout a batch, not only when the batch completes:

1. Immediately before every tester, implementer, or fix dispatch, append its stage entry with
   `status: in_progress`, the exact batch/task/phase/agent/report directory, and pre-dispatch
   `git status --short` plus the relevant `git diff`.
2. If a background launch returns a handle, update the entry immediately with its launch metadata.
3. On a valid successful report, save the normalized report under `report_dir`, verify the stage's
   RED/GREEN/fix gate, then remove that entry. A successful tool exit alone does not clear it.
4. On failure, interruption, stall, or invalid report, keep the entry, set `status: failed`, and
   add post-failure status/diff evidence and the failure reason. Never roll back partial edits.

For parallel batches, `incomplete_stages` contains one entry per task so each completion can be
cleared independently. Write the checkpoint after every transition above.

Advance `phase_cursor` with a checkpoint write before and after every phase/gate:

1. `tester`: set `in_progress` before Phase A; after all required tester reports pass RED, write
   `completed`, then advance to `test_review: pending`.
2. `test_review`: create agent report entries with report directories/statuses, mark the gate
   `in_progress`, and update each result independently. A clean gate has at least one success from
   every configured execution class and advances to `implementer: pending`; findings advance to
   `tester: pending` for only affected tasks.
3. `implementer`: set `in_progress` before Phase B. After all GREEN reports pass, write
   `completed`, then create `code_review: pending` with General, Architecture, and Compliance roles.
4. `code_review`: before each role dispatch set that role/report entries `in_progress`; preserve
   completed roles. When all roles pass, advance to the next batch's `tester: pending`, or to
   `fix: pending` when Critical/High findings exist.
5. `fix`: use `incomplete_stages` for each mutating fix. On success advance to
   `targeted_review: pending`; targeted-review failure returns to `fix: pending`, and success
   advances to the next batch or final review.
6. `final_review`: use per-role state/report directories exactly like code review. On a clean gate
   write `completed`, then `phase: complete, status: completed`.

For `test_review`, `targeted_review`, `code_review`, and `final_review`, store every native or
external report's alias, status, and report directory before dispatch. A failed/interrupted
read-only report remains on the current cursor; resume redispatches only non-`ok` entries/roles.
`incomplete_stages` always has priority over `phase_cursor` because it may represent live partial
mutations inside the cursor's mutating phase.

After each batch completes successfully (all four phases + issues resolved and
`incomplete_stages: []`):

1. Read current tasks.yaml to get task statuses
2. Calculate next batch from dependencies.yaml
3. Collect any deferred (medium) issues
4. Write checkpoint.yaml
5. Commit checkpoint with batch

## Reading Checkpoints

The `continue` skill reads checkpoint.yaml to:

1. Understand current progress
2. Identify next batch
3. Resume the four-phase pipeline
4. Carry forward deferred issues
5. Load `implementation_config.path`, verify its epoch ID, and reload that config before every
   tester, reviewer, implementer, fix, or final-review dispatch
6. Inspect `incomplete_stages` before deriving the next batch; recover those exact stages first
7. When no incomplete mutating stage exists, resume `phase_cursor` exactly; never infer Phase A
   merely from `next_batch`

If a legacy checkpoint has no `implementation_config`, resolve `<scope>/config.yaml`. When that
file is also absent, prompt once using `reference/configuration.md`, persist it, then resume. Never
fall back to a copied checkpoint route or `validation.yaml.review_config`.
