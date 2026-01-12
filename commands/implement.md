---
description: Execute implementation tasks - routes to task-dispatch for specs, or code/docs-implement for ad-hoc work
---

Determine implementation mode:

**1. Check for specs (draft first, then active):**
- Look in `./specs/draft/*/` for draft specs
- Look in `./specs/active/*/` for active specs

**2. Promote draft specs before implementation:**
- **Draft spec found** → Invoke `spec-promote` skill to move to active, then continue
- **Multiple drafts exist** → Ask which spec to promote and implement

**3. Resolve spec ambiguity (use AskUserQuestion):**
- **Multiple active specs exist** → Ask which spec to use (pre-select based on request context)
- **Request contradicts active spec** → Ask whether to proceed with spec or handle request separately

**4. Route based on context:**

- **Spec exists (now active)** → Summarize parallelization from `dependencies.yaml`, then invoke `task-dispatch` skill
- **No spec, code context** → Invoke `code-implement` skill
- **No spec, docs context** → Invoke `docs-implement` skill

**Parallelization guidance (when spec exists):**
Before dispatching, summarize from `dependencies.yaml`:
- Which tasks can run in parallel (`[P]` marker)
- Phase dependencies that require sequential execution
- Estimated batch structure

Use the Skill tool to invoke the appropriate skill.

**User's request:**
```text
$ARGUMENTS
```
