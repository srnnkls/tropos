# Parallel Task Detection

Build the widest file-safe batch allowed by explicit dependencies and known mutation paths.

## Authority

`tasks.yaml` carries `depends_on` (task IDs done first) and `files` (paths the task may create or modify). `dependencies.yaml` `batches[*].tasks`, when present, may be used directly after validating its pending task IDs.

## Missing Paths

Missing `files` is a scope gap, never a reason to run single-task pipelines serially. For all ready tasks without paths:

1. launch one bounded read-only discovery wave; each explorer orients per [AGENTS.md](../../../instructions/AGENTS.md#tools-and-context), then runs targeted symbol/path lookups;
2. persist resolved paths in `tasks.yaml`;
3. stop a task whose mutation boundary stays unknown with a scope gap.

Never assume two unknown tasks are independent or silently isolate each into its own batch.

## Batch Rules

A ready task (every `depends_on` done) enters the earliest batch whose tasks' `files` do not overlap its own. A dependency cycle, unknown dependency ID, or unresolved mutation boundary is an error.

`files` is a mutation boundary; expand it only when a named shared file will actually be edited, not for indirect callers or generated artifacts.

## Execution

Sequence batches only where dependencies or mutation overlap require it.
