---
created: ${DATE}
status: draft
issue_type: ${ISSUE_TYPE}
---

# ${SCOPE_NAME}

## Goal

${OUTCOME_AND_WHY}

## Non-Goals

- ${ADJACENT_CHANGE_LEFT_UNTOUCHED}

## Invariants

Existing design this change MUST preserve. Changing one requires a scope update.

| ID | Invariant | Check |
|----|-----------|-------|
| INV-1 | ${PINNED_ARCHITECTURE_LAYOUT_OR_OWNERSHIP} | ${RULE_TEST_OR_REVIEW_ITEM} |

## Conventions

Every axis resolves to a provider rule, a decision stated here, or `n/a`. The exemplar is the existing code new code mirrors.

| Axis | Resolution | Exemplar |
|------|------------|----------|
| Data & types | ${PROVIDER_OR_DECISION} | `${FILE}` |
| Errors | ${PROVIDER_OR_DECISION} | `${FILE}` |
| Effects | ${PROVIDER_OR_DECISION} | `${FILE}` |
| State | ${PROVIDER_OR_DECISION} | `${FILE}` |
| Dependencies & boundaries | ${PROVIDER_OR_DECISION} | `${FILE}` |
| Naming | ${PROVIDER_OR_DECISION} | `${FILE}` |
| Config & tooling | ${PROVIDER_OR_DECISION} | `${FILE}` |
| Testing | ${PROVIDER_OR_DECISION} | `${FILE}` |
| Prose & output | ${PROVIDER_OR_DECISION} | `${FILE}` |

## Decisions

- AD-1: ${DECISION}; rejected ${ALTERNATIVE}: ${REASON}

## User Stories

> Include when: Initiative issue type

- US001 (P1): ${USER_STORY}; independent test: ${HOW_TO_TEST_INDEPENDENTLY}

## Context

### Key Files

| File | Lines | Role |
|------|-------|------|
| `${FILE_PATH}` | ${LINE_RANGE} | ${ROLE} |

### Constraints

- ${CONSTRAINT}

<!-- Include when: User opted in to "Data Model" -->
### Data Model

| Entity | Purpose | Key Fields |
|--------|---------|------------|
| ${ENTITY} | ${PURPOSE} | ${FIELDS} |

## Requirements

### Functional Requirements

- FR-1: ${SUBJECT} MUST ${BEHAVIOR}

### Technical Requirements

- TR-1: ${SUBJECT} MUST ${PROPERTY}

## Acceptance Criteria

- [ ] AC-1 (FR-1): Given ${PRECONDITION}, when ${ACTION}, then ${RESULT}

## API Contract

> Include when: Feature/Initiative involves API changes

| Method | Path | Purpose |
|--------|------|---------|
| ${METHOD} | ${PATH} | ${PURPOSE} |

## Verification

- `${COMMAND}`: ${WHAT_IT_PROVES}
