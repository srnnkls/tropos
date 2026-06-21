# Parallel Task Detection

The batch signal lives in **`tasks.yaml`**. Each task carries `depends_on` (task IDs that must
complete first) and `files` (the paths it will create or modify). Batches are derived from these
two fields. When `dependencies.yaml` exists (Feature/Initiative), its `batches[*]` block is the
same derivation precomputed at scope-creation time — use it directly as a fast-path.

## Task Schema

```yaml
tasks:
  - id: AUT-001
    content: Create auth middleware
    status: pending
    files: [src/auth/middleware.py]
    depends_on: []
  - id: AUT-002
    content: Add session storage
    status: pending
    files: [src/auth/session.py]
    depends_on: []
  - id: AUT-003
    content: Write integration tests
    status: pending
    files: [tests/test_auth_integration.py]
    depends_on: [AUT-001, AUT-002]
```

Fields that drive batching:
- **`depends_on`** — task IDs that must be `done` before this task can start.
- **`files`** — declared target paths. Two tasks that share any path cannot run together.

## Detection Algorithm

```python
def can_parallelize(task_a: dict, task_b: dict) -> bool:
    """Two tasks may run in the same batch."""
    # Neither may depend on the other (handled by batch ordering, but guard anyway)
    if task_a["id"] in task_b.get("depends_on", []):
        return False
    if task_b["id"] in task_a.get("depends_on", []):
        return False

    # A task with no declared files is conservatively isolated
    files_a = set(task_a.get("files", []))
    files_b = set(task_b.get("files", []))
    if not files_a or not files_b:
        return False

    # Must touch different files
    return not (files_a & files_b)
```

## Batching Algorithm

A task joins the earliest batch where all its `depends_on` are already satisfied and it shares no
file with another task already placed in that batch.

```python
def build_batches(tasks: list[dict]) -> list[list[str]]:
    """Group tasks into ordered parallel batches by depends_on + files."""
    done: set[str] = set()
    remaining = list(tasks)
    batches: list[list[str]] = []

    while remaining:
        ready = [t for t in remaining if set(t.get("depends_on", [])) <= done]
        if not ready:
            raise ValueError("dependency cycle or unknown task id in depends_on")

        batch: list[dict] = []
        for task in ready:
            if all(can_parallelize(task, placed) for placed in batch):
                batch.append(task)

        batches.append([t["id"] for t in batch])
        placed_ids = {t["id"] for t in batch}
        done |= placed_ids
        remaining = [t for t in remaining if t["id"] not in placed_ids]

    return batches
```

A task with no `files` declared falls through `can_parallelize` as isolated, so it lands in its own
single-task batch — the safe fallback.

## Example

Given `tasks.yaml`:

```yaml
tasks:
  - id: T001
    files: [src/middleware/auth.py]
    depends_on: []
  - id: T002
    files: [src/routes/index.py]
    depends_on: []
  - id: T003
    files: [src/models/base.py]
    depends_on: [T001, T002]
  - id: T004
    files: [src/utils/logger.py]
    depends_on: [T003]
  - id: T005
    files: [src/config/loader.py]
    depends_on: [T003]
```

Batching result:

| Batch | Tasks | Reason |
|-------|-------|--------|
| 1 | T001, T002 | No deps, different files |
| 2 | T003 | Depends on T001 + T002 |
| 3 | T004, T005 | Both depend only on T003, different files |

Execution: dispatch T001+T002 simultaneously → wait → review; T003 → wait → review;
T004+T005 simultaneously → wait → review.

## Edge Cases

**Same file in multiple tasks** — cannot co-batch even with identical deps:
```yaml
- id: T010
  files: [src/models/user.py]
  depends_on: []
- id: T011
  files: [src/models/user.py]
  depends_on: []
```
→ Separate batches (shared file `src/models/user.py`).

**No `files` declared** — cannot verify file independence:
```yaml
- id: T015
  content: Refactor authentication logic
  depends_on: []
```
→ Own single-task batch (conservative default).
