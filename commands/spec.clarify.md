---
description: Resolve markers in validation.yaml interactively
---

Resolve unresolved markers in the active spec's validation.yaml.

**User's request:**
```text
$ARGUMENTS
```

**Flow:**
1. Find active spec in `./specs/active/*/`
2. Invoke `spec-clarify` skill

**Use when:**
- Pre-implementation gate check reports unresolved markers
- Clarifying ambiguous requirements discovered post-validation
- Before task-dispatch for Initiative specs with blocking markers
