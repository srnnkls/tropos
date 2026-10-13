# Root-Cause Tracing

Trace only to the source that explains one reachable trigger and wrong outcome.

## Use When

The error surfaces below the boundary that supplied the bad value, the responsible caller is unclear, or the fix site may be a symptom.

## Process

1. State the observed trigger and wrong outcome.
2. Identify the operation that produced it.
3. Name the concrete input or state that made it wrong.
4. When the current frame cannot explain that input, follow one caller/data edge backward (a caller, callee, or reference query for the named symbol; bounded `rg` for exact text).
5. Stop at the first source that fully explains the failure and owns the invariant. Do not enumerate the repository.

## Instrumentation

Only when static evidence cannot distinguish two adjacent boundaries: add one temporary probe before the suspected transition capturing only the deciding value/state, run the reproducer once, remove the probe. No stack dumps, broad logging, telemetry, or per-component probes.

## Fix Placement

Fix the narrowest shared source. Check another caller only when the shared fix gives it a concrete affected behavior. Validate at the earliest shared trust boundary; a second guard requires a distinct reachable failure at another boundary.

## Cutoff

One revised hypothesis may follow a falsified first. After two hypotheses for the same subject, report the unresolved evidence or decision. Fix-round limits: [review synthesis](../../review/reference/synthesis.md).
