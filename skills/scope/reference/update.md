# Scope Update

Sync `tasks.yaml`, the sole task-state input and output ([Step 5](../SKILL.md#step-5-validate-execution-metadata)), with git history.

1. Locate the scope per [Scope Location](../SKILL.md#scope-location) and extract tasks with status from `tasks.yaml`. Baseline: the scope's file creation time or the first commit mentioning the scope.
2. Collect state:

   ```bash
   git log --oneline --since="<scope-creation-time>" --all
   git log --stat --since="<scope-creation-time>" --all
   git status --short
   git diff <baseline>..HEAD --name-status
   ```

3. Per task, gather evidence (commit messages, file modifications, test existence, test results) and set status `done`, `in_progress`, `pending`, or `blocked`:

   | Evidence | Status |
   |---|---|
   | Commit message references the task, commit modifies the exact files named, and all acceptance criteria are met | `done` |
   | Commit touches related files, or the working directory has related changes | `in_progress` |
   | Ambiguous | `in_progress`, never `done` |

4. Write statuses and evidence:

   ```yaml
   tasks:
     - id: PROJ-001
       content: Set up project structure
       status: done
       active_form: Setting up project structure
       evidence:
         commits: [c228fea, 2f069d7]
         files: [src/feature.py, tests/test_feature.py]
   ```

   If any task is `in_progress` or `done` and scope.md has `status: draft`, promote the scope ([promotion](../SKILL.md#scope-location)).

5. Present:

   ```
   ## Scope Update Summary

   Scope: ./scopes/active/refactor/
   Tasks: tasks.yaml (progress: 5/10)

   Status:
     Completed: 5 tasks
     In Progress: 2 tasks
     Pending: 3 tasks

   Next actions:
     1. REFAC-006: Implement validation (ready)
     2. REFAC-007: Add error handling (ready)
   ```
