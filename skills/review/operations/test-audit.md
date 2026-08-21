# Test Quality Audit

Check tests in `$TARGET` for anti-patterns that produce passing tests with no verification value.

Default target: `tests` (override via argument).

---

## Anti-patterns

### 1. Oracle mirroring

Assertion reflects what code *does*, not what it *should* do — written by reading the implementation.

Signals:
- Expected value computed from same logic as production code
- Swapping a field name or constant leaves test green
- Test would pass with a different (wrong) implementation

### 2. Mock tautology

Test verifies the mock, not the unit under test.

Signals:
- `expect(result).toBe(mockReturnValue)` — asserting the return of a stub came back
- Every dependency mocked; nothing real under test
- Test passes even if unit forwards inputs unchanged

### 3. Testing the framework

Test exercises dependency or framework behavior, not the code the author touched.

Signals:
- Asserts constructor ran / library was called with inputs passed in
- Would pass against a stub that delegates directly to the dependency
- No application logic between input and assertion

### 4. Trivial assertions

Checks something structurally guaranteed — no domain logic exercised.

Signals:
- `result is not None` / `len(result) > 0` without checking content
- Asserts type rather than value
- "Obviously true given the types" — no behavior under test

### 5. Defective oracle

Test consumes the wrong signal, leaks state between cases, or passes for a reason unrelated to the
behavior it names — it can accuse a correct implementation or absolve a broken one.

Signals:
- Consumes a different injected fault/fixture than the one it names
- Marker, temp, or global state carried over from a previous case
- Passes when the named behavior is reverted

---

## Not an anti-pattern

Do not report thin coverage as a defect. A guarantee covered by a small set of representative
falsifiers is sufficient; more permutations of the same guarantee are deferred work. Flag a
*missing guarantee* — no test can fail if this documented behavior breaks — never a missing
permutation, and never ask for exhaustive enumeration of an input, syscall, or interleaving space.

---

## Workflow

1. `find ${TARGET:-tests} -type f` — enumerate test files
2. Read each file; scan each test function
3. Flag which anti-pattern(s) apply using the signals above
4. Report

---

## Output Format

```
## Oracle mirroring (N)
- `path/to/test.ts` > `test_name` — <one-line reason>; fix: <direction>

## Mock tautologies (N)
- ...

## Framework tests (N)
- ...

## Trivial assertions (N)
- ...

## Defective oracles (N)
- ...

## Clean (N tests, no issues)
```

Skip empty categories. No prose between sections. One fix-direction per finding.
