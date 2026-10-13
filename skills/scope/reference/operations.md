# Scope Operations

Locate scopes per [Scope Location](../SKILL.md#scope-location).

## Done

For [scope](../SKILL.md) with `done <name>`:

1. Read `tasks.yaml`. If any task is not done, warn and ask whether to proceed or update first.
2. Set `status: done` in scope.md frontmatter.
3. Unless already in `done/`, run `git mv scopes/<state>/<name> scopes/done/<name>` (`mv` if untracked).
4. Present a completion summary.
5. Offer: "Delete scope directory? Git history preserves everything."

## List

For [scope](../SKILL.md) with `list`: read `status`, `created`, `issue_type` from every `scopes/*/*/scope.md` and present a table grouped by state:

```
| Scope | Status | Type | Created |
|-------|--------|------|---------|
```

Flag any scope whose frontmatter `status` differs from its parent directory.
