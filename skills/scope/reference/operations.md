# Scope Operations

Simple sub-operations for done and list.

Scope directories live under one of three lifecycle dirs: `scopes/draft/<name>/`, `scopes/active/<name>/`, or `scopes/done/<name>/`. A scope name is unique across states.

---

## Done

When `/scope done <name>` is invoked:

1. Locate scope across `scopes/{draft,active,done}/<name>/`
2. Read `tasks.yaml` and check all tasks are done
3. If tasks remain: warn and ask to proceed or update first
4. Set `status: done` in scope.md frontmatter
5. Move directory: `git mv scopes/<state>/<name> scopes/done/<name>` (or `mv` if untracked). Skip if already in `done/`.
6. Present completion summary
7. Offer: "Delete scope directory? Git history preserves everything."

---

## List

When `/scope list` is invoked:

1. Find all `scopes/*/*/scope.md` files (state dir + scope name)
2. Read frontmatter from each (status, created, issue_type)
3. Present table — group by lifecycle state for readability:

```
| Scope | Status | Type | Created |
|-------|--------|------|---------|
| auth-system | active | Feature | 2026-03-01 |
| api-refactor | draft | Initiative | 2026-03-10 |
```

The `Status` column should match the parent directory (`draft`/`active`/`done`); flag any drift between frontmatter and parent dir.
