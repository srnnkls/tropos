# Verification Before Completion

**Core principle:** Evidence before claims, always.

---

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

---

## The Gate Function

```
BEFORE claiming any status:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

---

## Common Verification Requirements

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check |
| Build succeeds | Build command: exit 0 | Linter passing |
| Bug fixed | Test symptom: passes | Code changed |
| Regression test | Red-green verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

---

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- ANY wording implying success without running verification

---

## Key Patterns

**Tests:**
```
DO:   [Run test] [See: 34/34 pass] "All tests pass"
DON'T: "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
DO:   Write -> Run (pass) -> Revert fix -> Run (MUST FAIL) -> Restore -> Run (pass)
DON'T: "I've written a regression test" (without red-green)
```

**Build:**
```
DO:   [Run build] [See: exit 0] "Build passes"
DON'T: "Linter passed" (linter != compiler)
```

**Requirements:**
```
DO:   Re-read plan -> Create checklist -> Verify each -> Report
DON'T: "Tests pass, phase complete"
```

**Agent delegation:**
```
DO:   Agent reports -> Check VCS diff -> Verify changes -> Report
DON'T: Trust agent report
```

---

## When to Apply

**ALWAYS before:**
- ANY success/completion claims
- ANY expression of satisfaction
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

---

## Integration

**Use with:**
- `test` - Run tests before claiming they pass
- `implement` (debug operation) - Verify fix before claiming bug resolved
- `implement` (execute operation) - Verify each task before marking complete
- `git worktree` - Verify baseline before and after
