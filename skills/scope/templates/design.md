# Design: ${SCOPE_NAME}

---

## Problem

| Metric | Current | Target |
|--------|---------|--------|
| ${METRIC} | ${CURRENT_VALUE} | ${TARGET_VALUE} |

${PROBLEM_NARRATIVE}

---

## Alternatives

### ${ALTERNATIVE_A}

${DESCRIPTION}

**Rejected:** ${SPECIFIC_REASON}

### ${ALTERNATIVE_B}

${DESCRIPTION}

**Rejected:** ${SPECIFIC_REASON}

### Selected: ${CHOSEN_APPROACH}

${WHY_THIS_WINS}

---

## Invariants

<!--
Correctness properties the design must maintain.
ID each invariant for test linkage in Verification section.
-->

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| INV-1 | ${PROPERTY} | ${HOW_ENFORCED} |
| INV-2 | ${PROPERTY} | ${HOW_ENFORCED} |

---

## Complexity

| Dimension | Before | After | Delta |
|-----------|--------|-------|-------|
| ${DIMENSION} | ${BEFORE} | ${AFTER} | ${DELTA} |

---

## Verification

### Test Cases

| Test | Validates | Expected |
|------|-----------|----------|
| ${TEST_DESCRIPTION} | INV-1 | ${EXPECTED_OUTCOME} |
| ${TEST_DESCRIPTION} | INV-2 | ${EXPECTED_OUTCOME} |

---

## Design Notes

- ${NOTE}
