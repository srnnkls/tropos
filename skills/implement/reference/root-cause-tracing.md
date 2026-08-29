# Root-Cause Tracing

Trace only far enough to identify the source that explains one reachable trigger and wrong outcome.

## Use When

- the error appears below the boundary that supplied the bad value or state;
- a stack trace leaves the responsible caller unclear; or
- the proposed fix site may be a symptom rather than the shared source.

## Process

1. State the observed trigger and wrong outcome.
2. Identify the immediate operation that produced it.
3. Ask what concrete input or state made that operation wrong.
4. Follow one caller/data edge backward when the current frame cannot explain that input.
5. Stop at the first source that fully explains the failure and owns the invariant.

Use `gestalt callers`, `callees`, or `refs` for the named symbol when the edge is unclear. Confirm exact text with bounded `rg`. Do not enumerate the repository or continue upward after the responsible invariant is known.

## Instrumentation

When static evidence cannot distinguish two adjacent boundaries, add one temporary probe immediately before the suspected transition. Capture only the value/state needed to choose between them, run the reproducer once, then remove the probe.

Do not add stack dumps, broad logging, telemetry, or probes at every component by default.

## Fix Placement

Fix the narrowest shared source that explains the failure. Check another caller only when the shared fix gives it a concrete affected behavior. Add validation at the earliest shared trust boundary; a second guard requires a distinct reachable failure at another boundary.

## Cutoff

One revised hypothesis may follow a falsified first hypothesis. After two hypotheses or two fix rounds for the same subject, report the unresolved evidence or decision. Do not continue with narrower variants of the same failure mechanism.
