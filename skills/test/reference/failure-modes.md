# Test Failure Modes

This is the single source of truth for test-value rejection. Tester agents, RED gates, and explicit test audits must read this file; they must not copy or paraphrase its list elsewhere.

A test is valuable only when it exercises repository-owned behavior and fails when that behavior is wrong.

## Reject

### Oracle mirroring

Expected values copy the production implementation, reuse its algorithm or constants, or assert current output instead of required output. The test and defect can agree.

### Mock tautology

The assertion proves only that a mock returned its configured value or received the arguments supplied by the test.

### Useless mocks

All meaningful behavior is mocked, leaving no repository-owned logic between input and assertion. Mock only an unavoidable boundary; real repository code must remain inside it.

### Dependency or platform test

The test proves behavior owned by a dependency, framework, language standard library, compiler, runtime, parser, serializer, collection, filesystem, operating system, or external API. Test only the repository's transformation, policy, wiring, or error handling around that boundary.

### Trivial assertion

The assertion checks only non-null, type, non-empty length, callable existence, object construction, or “mock was called” without meaningful domain content.

### Assertion-free execution

The test executes a path but cannot distinguish correct behavior from incorrect behavior.

### Defective oracle

The test consumes the wrong signal, relies on stale or shared state, fails for an unrelated reason, falsely rejects a conforming implementation, or still passes when the named behavior is removed or reversed.

## Mandatory Self-Check

Before reporting RED, answer all four:

1. Which repository-owned behavior does this test exercise?
2. Which plausible wrong implementation does it reject?
3. Are expected values independent of production logic and mock configuration?
4. Would replacing repository logic with a pass-through, constant, or no-op make the test fail?

If any answer is missing or the fourth answer is no, sharpen or delete the test.
