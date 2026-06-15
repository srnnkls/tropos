# Checkpoint Format

Checkpoints are written after each successful batch to enable session recovery.

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
        file: src/auth/session.py
    parallel: false

  # Deferred issues (medium severity, noted for later)
  deferred_issues:
    - batch: 2
      severity: medium
      description: "Variable naming could be clearer in auth.py"
      location: "src/auth/auth.py:45"

  # Review config for resumption
  # Variant format: {reasoning_effort}-medium (verbosity fixed at medium)
  review_config:
    reasoning_effort: medium  # low | medium | high | xhigh 
    reviewers:
      - openai-codex/gpt-5.5          # pi
      - Gemini 3.5 Flash (High)       # agy
```

## Writing Checkpoints

After each batch completes successfully (all three phases + issues resolved):

1. Read current tasks.yaml to get task statuses
2. Calculate next batch from dependencies.yaml
3. Collect any deferred (medium) issues
4. Write checkpoint.yaml
5. Commit checkpoint with batch

## Reading Checkpoints

The `continue` skill reads checkpoint.yaml to:

1. Understand current progress
2. Identify next batch
3. Resume three-phase pipeline
4. Carry forward deferred issues

## Checkpoint vs tasks.yaml

| Aspect | tasks.yaml | checkpoint.yaml |
|--------|------------|-----------------|
| Purpose | Scope definition | Session state |
| Updates | Status changes | After each batch |
| Contains | All tasks | Progress + next batch |
| Used by | implement (execute) | continue |
