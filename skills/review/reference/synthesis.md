# Review Synthesis

Algorithm for merging multi-agent review results into a unified report.

---

## Algorithm

### 1. Parse Reports

Extract YAML from all reviewer outputs, including role-specific extensions (`structural_analysis`, `compliance_analysis`).

### 2. Group by Role

Aggregate harness results within each role first:
- General: all configured host-native and/or external agents
- Architecture: all configured host-native and/or external agents
- Compliance: all configured host-native and/or external agents

### 3. Merge Issues Within Role

Deduplicate by shared failure mechanism plus reachable trigger and wrong outcome. Preserve every reviewer attribution.

### 4. Merge Issues Across Roles

Apply the same mechanism/trigger/outcome key across roles. Similar prose or a shared location alone does not make two findings equivalent.

### 4.5 Triage for Validity

Reviewer output is evidence, not a verdict. Every merged issue clears this bar before it reaches gate aggregation; the synthesizer owns the disposition.

An execution finding without both `trigger` and `wrong_outcome` is schema-invalid and cannot fail a gate. Accept a complete issue only when its concrete failure mode is checkable against the reviewed artifact — an input that yields the wrong output, a check that cannot fire, or a false failure for a conformant implementation. Verify gate-blocking issues against the artifact before aggregation; an issue that survives only as prose is not yet an issue.

Anything rejected by the canonical [finding bar](finding-bar.md) becomes `residual` with the matching reason and evidence; it never opens a fix round.

`found_by` count is agreement, not validity. A single verified issue outranks unverified agreement.

### 4.6 Fix and Re-review Protocol

Initial review fan-out ends at synthesis. A fix round is one grouped mutation wave, the existing focused/native checks once against the combined fixed tree, and one targeted re-review report. Re-review verifies admitted findings; it is never a new review wave.

For each targeted re-review:

- require exactly one successful configured reviewer total — not one per role, gate, execution class, harness, finding, or fix group;
- prefer an eligible original finder of the highest-severity surviving issue; otherwise select the first active compatible reviewer in the immutable routing snapshot;
- assign only the gates represented by the admitted findings and provide their exact IDs and issue records, the fix diff, implicated requirements, and existing validation evidence;
- ask only whether each recorded trigger still produces its recorded wrong outcome;
- do not run General, Architecture, or Compliance fan-out and do not search for new findings.

If the selected reviewer fails to produce an eligible report, make at most one replacement attempt: retry that reviewer once or substitute one other compatible reviewer. Never dispatch a set, and accept exactly one successful report. An unrelated observation becomes `residual` and cannot open another fix round.

Two fix rounds maximum per subject. After the second targeted re-review, stop dispatching. Keep surviving admitted findings blocking and hand the user their exact evidence plus a recommendation; never open a third fix or review round.

Open fix rounds for the mechanism groups admitted under the [finding bar](finding-bar.md). Rediscovering an adjacent state later is a synthesis failure, not a reviewer win.

Route an admitted `needs decision:` finding to the user with its forcing constraint; it never enters a fix round.

Apply the finding bar during triage and gate aggregation; it owns grouping, fix sizing, sufficiency, deferred-hardening boundaries, and volume judgment.

### 5. Aggregate Gates

- Each role owns its gates:
  - General: Correctness, Security, Performance
  - Architecture: Architecture
  - Compliance: Style
- Gate fails if ANY harness within the owning role fails it on an issue that cleared triage;
  record which harness(es) failed. A reported failure whose issues all landed in `residual`
  does not fail the gate — record it in `residual` with the reason instead
- Aggregate only reports admitted by the [canonical result gate](harnesses.md#results)

### 6. Aggregate Severity

- Issue severity is the HIGHEST across all harnesses
- Critical by any harness = Critical overall

### 7. Prioritize

- Critical → High → Medium
- Within severity, group by gate

---

## Gate Summary Table Format

```
| Gate         | Status | General              | Architecture | Compliance |
|--------------|--------|----------------------|--------------|------------|
| Correctness  | PASS   | pass                 | —            | —          |
| Style        | PASS   | —                    | —            | pass       |
| Performance  | PASS   | pass                 | —            | —          |
| Security     | FAIL   | fail (Claude)        | —            | —          |
| Architecture | PASS   | —                    | pass         | —          |
```

`—` = not in scope for this role. On failure, parenthetical = which harness(es) failed.

---

## Structural Analysis Summary (Architecture Role)

```
Coupling: stable | New hotspots: 0 | Cycles: 0 | Impact radius: 3
```

## Compliance Analysis Summary (Compliance Role)

```
Languages: python | Rules: 12 | Violations: 1
```

---

## Issue Presentation Format

```
## Critical
- [C1] src/db/query.py:45
  Trigger: Untrusted search text reaches query construction
  Wrong outcome: The text changes the SQL statement
  Found by: {reviewer-id}, {reviewer-id}
  Suggestion: Use parameterized queries

## High
- [H1] src/api/handler.ts:112
  Trigger: A request omits the optional account object
  Wrong outcome: The handler dereferences null and returns 500
  Found by: {reviewer-id}
  Suggestion: Add the boundary guard

## Medium
- [M1] src/jobs/runner.py:18
  Trigger: A failed job is retried
  Wrong outcome: The retry log loses the job identifier
  Found by: {reviewer-id}
  Suggestion: Preserve the identifier in the retry event
```
