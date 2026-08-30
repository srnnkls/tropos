# Parallel Task Detection

Build the widest file-safe batch allowed by explicit dependencies and known mutation paths.

## Authority

`tasks.yaml` carries:

- `depends_on`: task IDs that must be done first;
- `files`: paths the task may create or modify.

When `dependencies.yaml` exists, its `batches[*]` is the precomputed form of the same data and may be used directly after validating pending task IDs.

## Missing Paths

Missing `files` is a scope gap, not a reason to run a full single-task pipeline serially.

For every ready task without paths:

1. launch one bounded read-only discovery wave for all such tasks;
2. each explorer receives fresh repository orientation under [AGENTS.md](../../../instructions/AGENTS.md#tools-and-context), then runs targeted symbol/path lookups;
3. persist the resolved paths in `tasks.yaml`;
4. if a task's mutation boundary remains unknown, stop that task with a scope gap.

Do not speculate that two unknown tasks are independent. Do not silently isolate each one into its own batch.

## Batch Rules

A task may enter the current batch when:

1. every `depends_on` task is done; and
2. its declared files do not overlap any task already in the batch.

Place each ready task into the earliest file-safe batch. A dependency cycle, unknown dependency ID, or unresolved mutation boundary is an error.

```python
def can_share_batch(task_a: dict, task_b: dict) -> bool:
    files_a = set(task_a["files"])
    files_b = set(task_b["files"])
    return not (files_a & files_b)
```

The file list is a mutation boundary, not an instruction to enumerate every indirect caller or generated artifact. Expand it only when a named shared file will actually be edited.

## Execution

Within each batch:

- all testers launch together;
- all cleared implementers launch together;
- all review roles and reviewer routes launch together.

Batches remain sequential only where dependencies or mutation overlap require it.
