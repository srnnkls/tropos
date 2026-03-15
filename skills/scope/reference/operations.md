# Scope Operations

Simple sub-operations for done and list.

---

## Done

When `/scope done <name>` is invoked:

1. Read `tasks.yaml` and check all tasks completed
2. If tasks remain: warn and ask to proceed or update first
3. Set `status: done` in scope.md frontmatter
4. Present completion summary
5. Offer: "Delete scope directory? Git history preserves everything."

---

## List

When `/scope list` is invoked:

1. Find all `scopes/*/scope.md` files
2. Read frontmatter from each (status, created, issue_type)
3. Present table:

```
| Scope | Status | Type | Created |
|-------|--------|------|---------|
| auth-system | active | Feature | 2026-03-01 |
| api-refactor | draft | Initiative | 2026-03-10 |
```
