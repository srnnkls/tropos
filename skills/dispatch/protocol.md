# Dispatch Protocol

Generic algorithm for routing skill invocations by argument matching.

---

## Route Definition Format

Each dispatcher defines routes as an ordered table:

| Pattern | Route | Action |
|---|---|---|
| match condition | route name | `Skill()`, `Read and follow`, or `See section` |

---

## Dispatch Algorithm

1. Check `$ARGUMENTS` against auto-detect rules (in order, first match wins)
2. If match → invoke target skill or read operation doc
3. If no match → present AskUserQuestion menu
4. Based on selection → invoke target skill or read operation doc
5. Target skill/operation handles any further interaction

Do NOT duplicate target skill logic. Only route.

---

## Action Types

| Type | Meaning |
|---|---|
| `Skill(name, args)` | Invoke another skill with arguments |
| `Read and follow` | Read the linked document and execute its instructions |
| `See section` / `See reference` | Follow in-file or cross-file reference |

---

## Fallback Menu Format

```
Header: [Skill Name]
Question: [What would you like to ___?]
multiSelect: false
Options:
- Label: Description
- ...
```

Route each selection to its corresponding action via a routing table.
