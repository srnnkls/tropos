# Finding Bar

Materialized verbatim into every reviewer prompt. It defines what counts as a finding, how to
group findings, and what to leave out.

---

## Admission

A finding states both, or it is not a finding:

- **Trigger** — a concrete input, interleaving, or crash point reachable from a public entry
  point or a documented failure mode of this artifact.
- **Wrong outcome** — what the artifact then does that it must not: wrong value returned, a
  check that cannot fire, data lost or silently rolled back, a stated contract violated, hot-path
  work the performance model excludes.

"Could be unsafe if", "should also handle", "consider hardening" name neither. Drop them.

## Enumerate once, report once

When the change touches a state machine — publication, sealing, invalidation, recovery,
verification, any ordered protocol over persisted or shared state — enumerate its states and
transitions **before** writing findings, then report every defect in that machine as ONE grouped
finding listing the affected transitions.

One transition per round is the most expensive review failure mode there is: it buys a fix round
per assertion instead of a fix round per machine.

The same holds for a defective test: report the defect and the smallest correcting assertion.
Never request exhaustive enumeration of an input, syscall, or interleaving space.

## Fix sizing

`suggestion` is the smallest change that removes the failure mode, applied at the shared root
rather than once per caller. When removing it needs a new type, wrapper, trait, public signature,
or API surface, prefix the suggestion with `needs decision:` and describe the constraint instead
of prescribing the design — that call belongs to the orchestrator.

## Sufficiency cutoff

The bar for the reviewed scope is: the documented guarantees hold under a small set of
representative falsifiers, and every confirmed reachable failure is fixed. That is done — not a
floor to build on.

Coverage of a further permutation, another observability hook, a stricter telemetry contract, or
tighter provenance formalism is deferred work, not a gate. It earns a finding only when
production integration or an observed failure demands it, and a missing guarantee — not a missing
permutation — is what makes representative coverage insufficient.

## Out of bounds

Report nothing for:

- edge cases with no reachable input; hardening a check that already has falsification evidence
- conformant code rewritten into a different but equivalent shape
- the design restated as a defect
- provenance, label, or telemetry mismatches where the underlying artifact is verifiably correct
  — a wrong label is a relabel, not a rerun, and not a finding unless the claim itself could be
  wrong
- refinements of a finding an earlier round already fixed: the fix either removes the failure
  mode or it does not. If it does not, report the surviving trigger — not a new variant of it

## Volume

Report volume tracks your reasoning effort, not defect density. Five verified findings beat forty
candidates; a candidate that costs a verification round and dies is a net loss, not a free option.
Unsure whether something clears the bar means it doesn't.
