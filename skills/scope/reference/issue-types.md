# Issue Type Definitions

| | Initiative | Feature | Task | Exploratory |
|---|---|---|---|---|
| Scope | Strategic (months) | Capability (weeks) | Implementation (days) | Unknown |
| Question limit | 5 | 5 | 3 | 3 (to classify) |
| Taxonomy | 6 areas (no Edge Cases) | Full (7 areas) | Scope, Behavior, Integration | Minimal until classified |
| Validation focus | Scope, Integration, Constraints | Behavior, Edge Cases, Integration | Behavior, Integration | — |

Exploratory: gather context from files, ask 3 clarifying questions about scope, recommend a type, and on confirmation restart with it.

## Taxonomy Areas by Type

| Area | Initiative | Feature | Task |
|------|-----------|---------|------|
| Scope | Primary | Primary | Primary |
| Behavior | Secondary | Primary | Primary |
| Data Model | Secondary | Primary | N/A |
| Constraints | Primary | Secondary | N/A |
| Edge Cases | N/A | Primary | N/A |
| Integration | Primary | Primary | Primary |
| Terminology | Secondary | Secondary | N/A |

Primary: ask if uncovered. Secondary: ask after primary areas, within the question limit. N/A: skip.

## Selection Guidance

| Choose | When |
|---|---|
| Initiative | Multiple distinct capabilities; quarterly; several people; business goal needs coordination |
| Feature | One user-facing capability; sprint-to-sprint; tasks are implementation details with clear combined value |
| Task | Single concrete deliverable; a day or two; well-defined; part of an existing Feature |
| Exploratory | Unclear type; current state must be understood first; ambiguous or open-ended request |

## SDD Integration Summary

Constitution check: Initiatives only. Gate applicability: [SDD gates](sdd-gates.md). Markers: Initiative tracked, resolved before task-dispatch; Feature tracked, non-blocking; Task minimal tracking. Documents and sections per type: [Step 4](../SKILL.md#step-4-create-directory-and-documents).
