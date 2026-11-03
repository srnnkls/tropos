# Dispatch Protocol

## Route Definition Format

| Pattern | Route | Action |
|---|---|---|
| match condition | route name (optional column) | `Invoke $skill`, `Read and follow`, or `See section` |

## Dispatch Algorithm

1. Match `$ARGUMENTS` against the routes in order; the first match wins.
2. No match: ask the user with the fallback menu.
3. Invoke the matched or selected target skill, read and follow the linked document, or follow the in-file or cross-file reference; the target owns further interaction.

Route only; do not duplicate target logic.

## Fallback Menu Format

A `:::user-question` block headed by the skill name, asking what to do, with one `- Label: Description` option per route.
