# Design: ${SCOPE_NAME}

<!--
Design reasoning for ${SCOPE_NAME}.
Structured analysis between deciding what to build and breaking it into tasks.
All sections optional — include only what adds value.
Code sketches belong in resources/implementation.md, not here.

See reference/quality-model.md for quality patterns from exemplary docs.
-->

---

## Problem

<!--
Quantified current state with evidence.
What's broken, slow, or missing — with numbers.
-->

| Metric | Current | Target |
|--------|---------|--------|
| ${METRIC} | ${CURRENT_VALUE} | ${TARGET_VALUE} |

${PROBLEM_NARRATIVE}

---

## Alternatives

<!--
What was considered and rejected, with specific reasoning.
Each alternative should have a clear rejection rationale.
-->

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

<!--
Before/after comparison showing the change is justified.
-->

| Dimension | Before | After | Delta |
|-----------|--------|-------|-------|
| ${DIMENSION} | ${BEFORE} | ${AFTER} | ${DELTA} |

---

## Verification

<!--
How to confirm the design works.
Link test cases to invariant IDs above.
-->

### Test Cases

| Test | Validates | Expected |
|------|-----------|----------|
| ${TEST_DESCRIPTION} | INV-1 | ${EXPECTED_OUTCOME} |
| ${TEST_DESCRIPTION} | INV-2 | ${EXPECTED_OUTCOME} |

---

## Design Notes

<!--
Edge cases, caveats, subtle decisions.
Things a reviewer or implementer should know.
-->

- ${NOTE}
