---
name: clarify
description: Resolve ambiguities interactively with tracked changes. Works with scope, code review, and other skills.
metadata:
  type: domain
---

# Clarify Skill

Resolve ambiguities by updating documents directly with tracked changes. Context-aware: adapts to scopes, code reviews, or standalone use.

---

## When to Use

**Use for:**
- Resolving markers before dispatch (especially for Initiatives)
- Clarifying ambiguous requirements discovered post-validation
- Addressing gaps identified in ambiguity_scan
- Resolving questions from code review findings
- Any interactive clarification with audit trail

**Don't use for:**
- Initial validation (handled during `/scope` creation)
- Changing fundamental scope (re-run `/scope`)

---

## Context Detection

The skill auto-detects context based on what's available:

| Context | Detection | Source |
|---------|-----------|--------|
| **Scope** | `./scopes/*/validation.yaml` exists | ambiguity_scan + markers |
| **Code Review** | Recent `~/.claude/reviews/*.md` | Review issues/questions |
| **Standalone** | Neither above | User-provided questions |

---

## Workflow

### Step 1: Load and Scan

**Scope context:**
1. Find scope in `./scopes/*/`
2. Read `validation.yaml` from scope directory
3. Run ambiguity scan:
   - Check `ambiguity_scan` section for areas with `status: partial` or `status: missing`
   - These become clarification candidates alongside open markers
4. Collect open markers where `status: open`
5. Merge candidates: ambiguity gaps + open markers (deduplicate by area)
6. If no candidates: report "No unresolved items" and exit

**Code review context:**
1. Find most recent review in `~/.claude/reviews/`
2. Extract issues marked as needing clarification
3. Present as candidates

**Standalone:**
1. Ask user what needs clarification
2. Proceed with interactive Q&A

### Step 2: Present Candidates

For each candidate (prioritized by impact), use AskUserQuestion:

```
Header: ${AREA}
Question: ${DESCRIPTION}
multiSelect: false
Options:
- [Generated options based on context]
- Defer: Skip for now
```

**Prioritization:** Scope > Behavior > Data Model > Constraints > Edge Cases > Integration > Terminology

### Step 3: Update Documents Directly

When a clarification is resolved, update the relevant section in the source document:

| Clarification Area | Target Document | Target Section |
|--------------------|-----------------|----------------|
| Scope | scope.md | Requirements, Scope |
| Behavior | scope.md | Requirements, Behavior |
| Data Model | scope.md | Data Model |
| Constraints | scope.md | Constraints |
| Edge Cases | scope.md | Edge Cases |
| Integration | scope.md | Integration Points |
| Terminology | scope.md | Terminology |

**Update approach:**
1. Read the target section
2. Integrate the clarification naturally into existing content
3. Do NOT create a separate "## Clarifications" section

### Step 4: Record Clarification Session

Create a new session entry in `clarification_sessions`:

```yaml
clarification_sessions:
  - id: S00${N}
    timestamp: ${ISO_TIMESTAMP}
    source: clarify  # or scope-review, code review if invoked from there
    questions:
      - id: Q001
        question: "${QUESTION}"
        answer: "${ANSWER}"
        area: ${TAXONOMY_AREA}
        doc_updates:
          - file: scope.md
            section: Requirements
            action: modified
```

**doc_updates** tracks exactly which files/sections changed for audit trail.

### Step 5: Update Ambiguity Scan Status

For each resolved clarification from ambiguity gaps:

1. Update `ambiguity_scan.${area}.status` to `clear`
2. Remove the resolved gap from `ambiguity_scan.${area}.gaps`

### Step 6: Update Markers

For each resolved marker:

1. Change `status: open` to `status: resolved`
2. Add `resolution: "${USER_ANSWER}"`

### Step 7: Re-check Gates (Initiatives Only)

For Initiative specs:

1. Re-evaluate gates in validation.yaml
2. Update gate status if resolution changes assessment
3. Report gate status

---

## Doc Update Mapping

| Source | Target File | Target Section |
|--------|-------------|----------------|
| Scope gap | scope.md | ## Requirements or ## Scope |
| Behavior gap | scope.md | ## Requirements / Behavior subsection |
| Data Model gap | scope.md | ## Data Model |
| Constraints gap | scope.md | ## Constraints |
| Edge Cases gap | scope.md | ## Edge Cases |
| Integration gap | scope.md | ## Integration Points |
| Terminology gap | scope.md | ## Terminology |

---

## Example Session

```
[Load validation.yaml]
[Run ambiguity scan]
- scope: partial (1 gap)
- data_model: missing (2 gaps)
[Check markers]
- M001 (Constraints): open

Candidates:
1. Scope: "User role boundaries unclear"
2. Data Model: "Schema for notifications not defined"
3. Data Model: "Retention policy not specified"
4. Constraints: "Authentication method not specified"

---
Header: Scope
Question: What user roles exist and what are their boundaries?

Options:
- Admin/User: Two-tier with admin full access
- Role-based: Granular permissions per feature
- Defer: Skip for now

User selects: Admin/User

[Update scope.md#requirements]
Added: "Two-tier role system: Admin (full access), User (standard permissions)"

[Record session]
clarification_sessions:
  - id: S001
    timestamp: 2025-01-15T10:30:00Z
    source: clarify
    questions:
      - id: Q001
        question: "What user roles exist and what are their boundaries?"
        answer: "Two-tier: Admin (full access), User (standard permissions)"
        area: scope
        doc_updates:
          - file: scope.md
            section: Requirements
            action: modified

[Update ambiguity_scan]
scope:
  status: clear
  gaps: []

---
Header: Constraints
Question: Which authentication method should be used?
...
```

---

## Integration

**Command:** `/clarify [context]`

**Invoked from:**
- `scope` - Clarify during scope creation or review
- `code review` - Clarify code review findings
- `dispatch` - Resolve blocking markers before dispatch

**Related skills:**
- `scope` - Creates scopes with ambiguity_scan and markers
- `dispatch` - Checks for blocking markers before dispatch
