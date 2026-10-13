# Dispatch Protocol

## Route Definition Format

| Pattern | Route | Action |
|---|---|---|
| match condition | route name (optional column) | `Skill()`, `Invoke $skill`, `Read and follow`, or `See section` |

## Dispatch Algorithm

1. Match `$ARGUMENTS` against the routes in order; the first match wins.
2. No match: present the fallback menu through AskUserQuestion.
3. Invoke the matched or selected target skill (`Skill(name, args)`), read and follow the linked document, or follow the in-file or cross-file reference; the target owns further interaction.

Route only; do not duplicate target logic.

## Fallback Menu Format

```
Header: [Skill Name]
Question: [What would you like to ___?]
multiSelect: false
Options:
- Label: Description
- ...
```
