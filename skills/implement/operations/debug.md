# Bounded Debugging

Find one reachable trigger and wrong outcome, then fix the narrowest shared source through the strict RED → GREEN → review pipeline.

## Boundary

Run `gestalt map` as the first repository action. Investigation continues only while it resolves a blocking unknown for the reported failure.

Do not enumerate every caller, usage, reference implementation, difference, environment permutation, or boundary. Do not add diagnostic instrumentation at every layer.

## 1. Reproduce

1. Read the actual error and directly relevant stack frames.
2. Run the smallest reliable reproducer once.
3. Record the trigger, observed wrong outcome, and directly responsible boundary.

When the failure does not reproduce, report the missing evidence needed. Do not broaden into speculative investigation.

## 2. Trace to the Responsible Source

Trace backward only while the current frame cannot explain the bad value or state.

- Use a named `gestalt callers`, `callees`, or `refs` query when the immediate relationship is unresolved.
- Use bounded `rg` only to confirm exact names or text after Gestalt.
- Stop when one source explains the reachable trigger and wrong outcome.
- Fix the narrowest shared source. Inspect sibling callers only when the proposed shared change gives them a concrete affected behavior.

If static evidence cannot locate the break, add one temporary probe at the suspected boundary, run the reproducer once, then remove the probe. Another probe requires evidence that the suspected boundary changed.

## 3. Falsify One Hypothesis

State one hypothesis and one observation that would disprove it. Run the smallest check that separates the hypothesis from a plausible alternative.

A failed hypothesis may open one revised attempt using the new evidence. After two hypotheses or two fix rounds for the same subject, surface the unresolved decision instead of continuing.

## 4. Fix Through Strict TDD

Once the source is identified:

1. dispatch a tester for the minimal reproducer under `skills/test/SKILL.md` ceilings;
2. verify RED once;
3. dispatch an implementer for the narrowest shared fix;
4. verify GREEN once;
5. run one concurrent Phase C review wave.

Add a guard at the earliest shared trust boundary. Another guard requires a distinct reachable failure at a distinct boundary.

## Stop Condition

Stop when the reproducer passes, directly affected native validation passes, review clears, and no known blocker remains. Adjacent anomalies, speculative hardening, broader telemetry, and additional confidence runs are deferred.

## Reference

- [root-cause-tracing.md](../reference/root-cause-tracing.md) — bounded call-chain tracing
- [../reference/finding-bar.md](../../review/reference/finding-bar.md) — reachable-failure and sufficiency rules
