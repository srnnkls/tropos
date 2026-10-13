---
name: clarify
description: Resolve ambiguities interactively with tracked changes. Use when resolving scope markers, ambiguous requirements, ambiguity-scan gaps or code review questions with an audit trail; not for initial scope validation or changing a scope fundamentally.
metadata:
  type: domain
henia:
  auto_invoke: false
  targets:
    claude:
      frontmatter:
        argument-hint: '[context]'
    codex:
      openai:
        interface:
          display_name: Clarify
          short_description: Apply the canonical clarify skill workflow
          default_prompt: Use $clarify for the requested task.
---

# Clarify Skill

Resolve ambiguities by editing the source documents and recording each change.

::::head

## Context Detection

| Context | Detection | Source |
|---------|-----------|--------|
| Scope | a scope's `validation.yaml` exists ([scope location](../scope/SKILL.md#scope-location)) | ambiguity_scan + markers |
| Code Review | a recent review report under `.peer/` | Review issues/questions |
| Standalone | Neither above | User-provided questions |

## Workflow

### Step 1: Load and Scan

- Scope: resolve the scope per [scope location](../scope/SKILL.md#scope-location) and read its `validation.yaml`. Candidates are `ambiguity_scan` areas with `status: partial` or `status: missing` plus markers with `status: open`, deduplicated by area. None → report "No unresolved items" and exit.
- Code review: candidates are the issues marked as needing clarification in the most recent review report under `.peer/` ([`peer path`](../peer/SKILL.md#report-layout--peer)).
- Standalone: ask the user what needs clarification, then run interactive Q&A.

### Step 2: Present Candidates

Per candidate, in the row order of the scope [ambiguity scan](../scope/SKILL.md#step-3-validation-human-in-the-loop) table, use AskUserQuestion:

:::menu{header="${AREA}" question="${DESCRIPTION}"}
- [Generated options based on context]
- Defer: Skip for now
:::

### Step 3: Update Documents Directly

Integrate each resolved clarification into its section of `scope.md` ([template](../scope/templates/scope.md)); never add a "## Clarifications" section.

| Clarification Area | Target Document | Target Section |
|--------------------|-----------------|----------------|
| Scope | scope.md | Goal or Non-Goals |
| Behavior | scope.md | Functional Requirements |
| Data Model | scope.md | Data Model |
| Constraints | scope.md | Constraints |
| Edge Cases | scope.md | Acceptance Criteria |
| Integration | scope.md | Technical Requirements |
| Terminology | scope.md | Context |

### Step 4: Record Clarification Session

Append a session to `clarification_sessions`; `doc_updates` lists every changed file and section:

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

### Step 5: Update Ambiguity Scan Status

Per resolved gap: set `ambiguity_scan.${area}.status` to `clear` and remove the gap from `ambiguity_scan.${area}.gaps`.

### Step 6: Update Markers

Per resolved marker: set `status: resolved` and add `resolution: "${USER_ANSWER}"`.

### Step 7: Re-check Gates (Initiatives Only)

Re-evaluate the gates in `validation.yaml`, update any whose assessment changed, and report gate status.

::::

:::related
- `scope` — creates scopes with ambiguity scans and markers, and clarifies during creation or review
- `implement` — checks for blocking markers before execution
- `code` — clarifies code review findings
:::
