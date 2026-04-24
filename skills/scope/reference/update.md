# Scope Update

Synchronize scope documents with actual project state by analyzing git commits.

---

## Workflow

### Step 1: Locate and Parse Scope

1. **Find scope:** If name provided, use that. Else, find most recent in `./scopes/`
2. **Parse structure:** Extract tasks with current status from tasks.yaml
3. **Determine baseline:** Use file creation time or first commit mentioning scope

### Step 2: Analyze Current State

```bash
git log --oneline --since="<scope-creation-time>" --all
git log --stat --since="<scope-creation-time>" --all
git status --short
git diff <baseline>..HEAD --name-status
```

### Step 2.5: Sync TodoWrite to tasks.yaml

If TodoWrite has entries matching scope tasks:
1. For each "completed" todo, update corresponding task to `status: completed`
2. For each "in_progress" todo, update to `status: in_progress`
3. Update `meta.last_updated` and `meta.progress` fields

### Step 3: Map Evidence to Tasks

For each task:
1. Search for evidence (commit messages, file modifications, test existence)
2. Determine status: `completed`, `in_progress`, `pending`, `blocked`
3. Collect evidence notes (commits, files, test results)

### Step 4: Update tasks.yaml and Promote Status

Update task statuses and add evidence.

```yaml
tasks:
  - id: PROJ-001
    content: Set up project structure
    status: completed
    active_form: Setting up project structure
    evidence:
      commits: [c228fea, 2f069d7]
      files: [src/feature.py, tests/test_feature.py]
```

**Status promotion:** After updating tasks, if any task is `in_progress` or `completed` and the scope.md frontmatter has `status: draft`, promote it to `status: active`.

### Step 5: Present Summary

```
## Scope Update Summary

Scope: ./scopes/refactor/
Tasks: tasks.yaml (progress: 5/10)

Status:
  Completed: 5 tasks
  In Progress: 2 tasks
  Pending: 3 tasks

Next actions:
  1. REFAC-006: Implement validation (ready)
  2. REFAC-007: Add error handling (ready)
```

---

## Matching Heuristics

**Strong evidence (auto-mark complete):**
- Commit message explicitly references task
- Commit modifies exact files mentioned
- All acceptance criteria met

**Weak evidence (mark in-progress):**
- Commit touches related files
- Working directory has related changes

**Conservative approach:** When uncertain, prefer in-progress over completed
