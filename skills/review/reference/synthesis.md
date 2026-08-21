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

- Deduplicate across all completed configured agents within each role

### 4. Merge Issues Across Roles

- Deduplicate by location + description similarity
- Preserve role attribution

### 4.5 Triage for Validity

Reviewer output is evidence, not a verdict. Every merged issue clears this bar before it
reaches gate aggregation; the synthesizer owns the disposition.

Accept an issue only when it names a concrete failure mode checkable against the reviewed
artifact — an input that yields the wrong output, a check that cannot fire, a false failure
for a conformant implementation. Verify the gate-blocking ones against the artifact before
they fail a gate; an issue that survives only as prose is not yet an issue.

Disposition these as `residual` rather than opening a fix round:

- ever-narrower edge cases with no reachable input
- speculative hardening of a check that already has falsification evidence
- questions an earlier round or another reviewer already grounded
- the design restated as a defect
- rewrites of conformant code to a different but equivalent shape

`found_by` count is agreement, not validity — reviewers sharing a wrong assumption about the
requirements agree loudly. A single verified issue outranks three unverified concurring ones.

Report volume tracks reasoning effort, not defect density, and high-effort reviewers reliably
produce refinement spirals past the first round. Converge in one fix round unless a later
round surfaces a new verified failure mode; round count is a cost, not a quality signal.

### 4.6 Convergence

Two fix rounds per subject. A third round opens only for a verified failure mode in a component
no prior round examined — never for a narrower variant of something already fixed. At that point,
stop and hand the user the surviving `residual` list with a recommendation, rather than dispatching
again.

Batch by mechanism, not by assertion. When two or more issues touch the same state machine —
publication, sealing, invalidation, recovery, verification, any ordered protocol over persisted or
shared state — do not open a fix round on the first one. Enumerate that machine's states and
transitions, sweep it once, and fix the whole set together. Rediscovering an adjacent state three
rounds later is a synthesis failure, not a reviewer win.

An issue whose `suggestion` carries `needs decision:` does not enter a fix round. Surface it to the
user with the constraint that forces it; a fix agent must never invent public API surface to close
a finding.

Apply the finding bar's sufficiency cutoff at the gate too: the scope ships when its documented
guarantees hold under representative falsifiers and confirmed reachable failures are fixed.
Additional permutations, observability, and telemetry precision are `residual` — reason
`deferred_hardening` — until production integration or an observed failure demands them.

### 5. Aggregate Gates

- Each role owns its gates:
  - General: Correctness, Security, Performance
  - Architecture: Architecture
  - Compliance: Style
- Gate fails if ANY harness within the owning role fails it on an issue that cleared triage;
  record which harness(es) failed. A reported failure whose issues all landed in `residual`
  does not fail the gate — record it in `residual` with the reason instead
- For implementation-owned gates, synthesis is eligible only after each execution class actually
  configured for the role has at least one successful report

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
| Performance  | PASS   | pass                 | pass         | —          |
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
## Critical (found by 2+ harnesses — high confidence)
- [C1] SQL injection at src/db/query.py:45
  Role: General | Found by: {reviewer-id}, {reviewer-id}
  Suggestion: Use parameterized queries

## High
- [H1] Missing null check at src/api/handler.ts:112
  Role: General | Found by: {reviewer-id}
  Suggestion: Add guard clause

## Medium
- [M1] Variable 'd' should have descriptive name (naming/5x-rule)
  Role: Compliance | Rule: python/quality.md
  Suggestion: Rename to 'duration_seconds'
```
