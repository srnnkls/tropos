# Bounded Debugging

Find one reachable trigger and wrong outcome, then fix the narrowest shared source through the strict RED → GREEN → review pipeline.

## Boundary

Apply the repository-orientation contract in [AGENTS.md](../../../instructions/AGENTS.md#tools-and-context). Investigation continues only while it resolves a blocking unknown for the reported failure.

Do not add diagnostic instrumentation at every layer.

## 1. Reproduce

1. Read the actual error and directly relevant stack frames.
2. Run the smallest reliable reproducer once.
3. Record the trigger, observed wrong outcome, and directly responsible boundary.

When the failure does not reproduce, report the missing evidence needed. Do not broaden into speculative investigation.

## 2. Diagnose

Apply [root-cause-tracing.md](../reference/root-cause-tracing.md). It owns bounded Gestalt/`rg` use, hypothesis limits, temporary probes, the shared-source cutoff, and unresolved-evidence reporting.

## 3. Fix Through Strict TDD

Once the source is identified:

1. dispatch a tester for the minimal reproducer under the [test skill](../../test/SKILL.md) ceilings;
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
