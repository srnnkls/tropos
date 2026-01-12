---
description: Create spec documents for task
---

Create comprehensive tracking documents for this development task.

**User's request:**
```text
$ARGUMENTS
```

**Flow:**
1. Check for native Claude `/plan` context (if present, use as seed context)
2. Invoke `spec-validate` skill first
3. Then invoke `spec-create` skill with validation results

**Native plan integration:** If `/plan` was used before this command, the goal, approach, and open questions seed the validation taxonomy.
