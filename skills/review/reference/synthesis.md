# Review Synthesis

## Algorithm

### 1. Parse Reports

Extract YAML from every reviewer output, including role extensions (`structural_analysis`, `compliance_analysis`, `abstraction_analysis`).

### 2. Group by Role

Aggregate the results of all configured host-native and external agents within each [code review role](../../code/SKILL.md#review-roles) first.

### 3. Merge Issues Within Role

Deduplicate by shared failure mechanism plus reachable trigger and wrong outcome. Preserve every reviewer attribution.

### 4. Merge Issues Across Roles

Apply the same key across roles. Similar prose or a shared location alone does not make two findings equivalent.

### 4.5 Triage for Validity

The synthesizer, not the reviewer, dispositions every merged issue before gate aggregation, applying the canonical [finding bar](finding-bar.md):

- An execution finding missing `trigger` or `wrong_outcome` is schema-invalid and cannot fail a gate.
- Accept a complete issue only when its failure mode is checkable against the reviewed artifact: an input that yields the wrong output, a check that cannot fire, or a false failure for a conformant implementation.
- Verify gate-blocking issues against the artifact before aggregation.
- An issue the finding bar rejects becomes `residual` with the matching reason and evidence and never opens a fix round.
- `found_by` count is agreement, not validity; a single verified issue outranks unverified agreement.

### 4.6 Fix and Re-review Protocol

Initial review fan-out ends at synthesis. A fix round is one grouped mutation wave over the mechanism groups admitted under the finding bar, the existing focused/native checks once against the combined fixed tree, and one targeted re-review report. Rediscovering an adjacent state in a later round is a synthesis failure.

Targeted re-review verifies admitted findings only:

- require exactly one successful configured reviewer total — not one per role, gate, execution class, harness, finding, or fix group;
- prefer an eligible original finder of the highest-severity surviving issue; otherwise the first active compatible reviewer in the immutable routing snapshot;
- assign only the gates of the admitted findings and provide their exact IDs and issue records, the fix diff, implicated requirements, and existing validation evidence;
- ask only whether each recorded trigger still produces its recorded wrong outcome; no role fan-out, no search for new findings;
- if the reviewer produces no eligible report, make at most one replacement attempt: retry it once or substitute one other compatible reviewer, never a set;
- an unrelated observation becomes `residual` and opens no fix round.

At most two fix rounds per subject. After the second targeted re-review, stop dispatching: keep surviving admitted findings blocking and hand the user their exact evidence plus a recommendation.

Route an admitted `needs decision:` finding to the user with its forcing constraint; it never enters a fix round.

### 5. Aggregate Gates

- Each role owns the gates the [code review roles](../../code/SKILL.md#review-roles) assign it.
- A gate fails if any harness within the owning role fails it on an issue that cleared triage; record which harness(es) failed. A reported failure whose issues all landed in `residual` does not fail the gate; record it in `residual` with the reason.
- Aggregate only reports admitted by the [canonical result gate](harnesses.md#results).

### 6. Aggregate Severity

Issue severity is the highest across all harnesses.

### 7. Prioritize

Critical → High → Medium; within a severity, group by gate.

## Gate Summary Table Format

```
| Gate         | Status | General              | Architecture | Compliance | Abstractions |
|--------------|--------|----------------------|--------------|------------|--------------|
| Correctness  | PASS   | pass                 | —            | —          | —            |
| Style        | PASS   | —                    | —            | pass       | —            |
| Performance  | PASS   | pass                 | —            | —          | —            |
| Security     | FAIL   | fail (Claude)        | —            | —          | —            |
| Architecture | PASS   | —                    | pass         | —          | —            |
| Abstractions | PASS   | —                    | —            | —          | pass         |
```

`—` = not in scope for this role. On failure, the parenthetical names the failing harness(es).

## Structural Analysis Summary (Architecture Role)

```
Coupling: stable | New hotspots: 0 | Cycles: 0 | Impact radius: 3
```

## Compliance Analysis Summary (Compliance Role)

```
Languages: python | Rules: 12 | Violations: 1
```

## Abstraction Analysis Summary (Abstractions Role)

```
Definitions checked: 7 | Owners found: 1 | Misfits: 0
```

## Issue Presentation Format

```
## Critical
- [C1] src/db/query.py:45
  Trigger: Untrusted search text reaches query construction
  Wrong outcome: The text changes the SQL statement
  Found by: {reviewer-id}, {reviewer-id}
  Suggestion: Use parameterized queries

## High
- [H1] …

## Medium
- [M1] …
```
