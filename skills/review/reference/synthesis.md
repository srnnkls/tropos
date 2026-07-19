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

### 5. Aggregate Gates

- Each role owns its gates:
  - General: Correctness, Security, Performance
  - Architecture: Architecture
  - Compliance: Style
- Gate fails if ANY harness within the owning role fails it; record which harness(es) failed
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
