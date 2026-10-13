# Bounded Debugging

Find one reachable trigger and wrong outcome, then fix the narrowest shared source through the strict pipeline.

## Boundary

Orient per [AGENTS.md](../../../instructions/AGENTS.md#tools-and-context). Investigate only while it resolves a blocking unknown for the reported failure.

## 1. Reproduce

1. Read the actual error and directly relevant stack frames.
2. Run the smallest reliable reproducer once.
3. Record the trigger, observed wrong outcome, and responsible boundary.

If it does not reproduce, report the missing evidence and stop.

## 2. Diagnose

Apply [root-cause-tracing.md](../reference/root-cause-tracing.md).

## 3. Fix Through Strict TDD

1. Dispatch a tester for the minimal reproducer under the [test skill](../../test/SKILL.md) ceilings; verify RED once.
2. Dispatch an implementer for the narrowest shared fix; verify GREEN once.
3. Run one concurrent Phase C review wave.

## Stop Condition

Stop when the reproducer passes, directly affected native validation passes, review clears, and no known blocker remains. Defer adjacent anomalies, speculative hardening, broader telemetry, and confidence runs.

## Reference

- [root-cause-tracing.md](../reference/root-cause-tracing.md) — bounded call-chain tracing
- [../reference/finding-bar.md](../../review/reference/finding-bar.md) — reachable-failure and sufficiency rules
