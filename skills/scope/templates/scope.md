---
created: ${DATE}
status: draft
issue_type: ${ISSUE_TYPE}
---

# ${SCOPE_NAME}

## Goal

${GOAL_DESCRIPTION}

## User Stories

> Include when: Initiative issue type

### P1 (Critical)

- US001: ${USER_STORY_1}
  - **Independent test:** ${HOW_TO_TEST_INDEPENDENTLY}

### P2 (Important)

- US002: ${USER_STORY_2}
  - **Independent test:** ${HOW_TO_TEST_INDEPENDENTLY}

### P3 (Nice to have)

- US003: ${USER_STORY_3}
  - **Independent test:** ${HOW_TO_TEST_INDEPENDENTLY}

## Context

### Key Files

| File | Lines | Description |
|------|-------|-------------|
| `${FILE_PATH}` | ${LINE_RANGE} | ${DESCRIPTION} |

### Architecture Decisions

#### AD-1: ${DECISION_TITLE}

**Context:** ${CONTEXT}

**Decision:** ${DECISION}

**Alternatives:**
- ${ALTERNATIVE_A}: ${TRADE_OFFS}
- ${ALTERNATIVE_B}: ${TRADE_OFFS}

### Constraints

- ${CONSTRAINT}: ${RATIONALE}

<!-- Include when: User opted in to "Tech Decisions" -->
### Tech Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| ${DECISION_AREA} | ${CHOICE} | ${WHY} |

<!-- Include when: User opted in to "Data Model" -->
### Data Model

| Entity | Purpose | Key Fields |
|--------|---------|------------|
| ${ENTITY} | ${PURPOSE} | ${FIELDS} |

## Requirements

### Functional Requirements

- ${FUNCTIONAL_REQ_1}
- ${FUNCTIONAL_REQ_2}

### Technical Requirements

- ${TECHNICAL_REQ_1}
- ${TECHNICAL_REQ_2}

## Acceptance Criteria

- [ ] Given ${PRECONDITION_1}
  When ${ACTION_1}
  Then ${EXPECTED_RESULT_1}

- [ ] Given ${PRECONDITION_2}
  When ${ACTION_2}
  Then ${EXPECTED_RESULT_2}

## API Contract

> Include when: Feature/Initiative involves API changes

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| ${METHOD} | ${PATH} | ${PURPOSE} |

## Implementation Strategy

> Include when: Initiative issue type

### Approach

${APPROACH}

### Phases Overview

- **Phase 1:** ${PHASE_1_GOAL}
- **Phase 2:** ${PHASE_2_GOAL}

## Dependency Graph

> Machine-readable: [dependencies.yaml](dependencies.yaml)

```
Phase 1 (${PHASE_1_NAME})
├── ${TASK_1}
└── ${TASK_2}
```

## Non-Goals

- ${EXPLICIT_NON_GOAL_1}
- ${EXPLICIT_NON_GOAL_2}

## Verification

- ${VERIFICATION_STEP_1}
- ${VERIFICATION_STEP_2}

## Gotchas & Learnings

- ${GOTCHA}

## Open Questions

- [ ] ${QUESTION}
