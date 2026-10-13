# Finding Bar

## Admission

A finding states both, or it is not a finding:

- Trigger — a concrete input, interleaving, or crash point reachable from a public entry
  point or a documented failure mode of this artifact.
- Wrong outcome — what the artifact then does that it must not: wrong value returned, a
  check that cannot fire, data lost or silently rolled back, a stated contract violated, hot-path
  work the performance model excludes.

"Could be unsafe if", "should also handle", "consider hardening" name neither. Drop them.

## Abstraction admission

Abstractions findings, each with its evidence:

- Duplicated knowledge: two locations, one in the change, encoding one rule. Trigger: a change to
  that rule; co-change history (`gestalt log` on both locations) evidences it. Wrong outcome: a
  one-sided edit leaves them disagreeing.
- Reimplemented owner: an existing symbol, installed dependency API, or standard library API whose
  contract (results, errors, ordering, mutation) matches on the change's inputs. Wrong outcome: two owners of one
  behavior.
- Misfit: consumers fork, copy, rebuild, or bypass a shared definition. Wrong outcome: its
  behavior split across consumers.
- False coupling: a shared definition whose consumers share no invariant. Trigger: one consumer's
  requirement changes. Wrong outcome: unrelated consumers must change.

Reuse takes a concrete `suggestion` that also removes the superseded code. A new or reshaped
abstraction is `needs decision:`.

## Enumerate once, report once

When the change touches a state machine — publication, sealing, invalidation, recovery,
verification, any ordered protocol over persisted or shared state — enumerate its states and
transitions before writing findings, then report every defect in that machine as one grouped
finding listing the affected transitions, never one transition per round.

For a defective test, report the defect and the smallest correcting assertion. Never request
exhaustive enumeration of an input, syscall, or interleaving space.

## Fix sizing

`suggestion` is the smallest change that removes the failure mode, at the shared root rather than
once per caller. When that needs a new type, wrapper, trait, public signature, or API surface,
prefix it with `needs decision:` and describe the constraint, not the design.

## Sufficiency cutoff

The reviewed scope is done when its documented guarantees hold under a small set of representative
falsifiers and every confirmed reachable failure is fixed. Further permutations, observability
hooks, stricter telemetry contracts, or tighter provenance formalism are deferred work, not a gate;
they earn a finding only when production integration or an observed failure demands it. Only a
missing guarantee, not a missing permutation, makes representative coverage insufficient.

## Out of bounds

Report nothing for:

- edge cases with no reachable input; hardening a check that already has falsification evidence
- conformant code rewritten into a different but equivalent shape
- the design restated as a defect
- provenance, label, or telemetry mismatches where the underlying artifact is verifiably correct,
  unless the claim itself could be wrong
- refinements of a finding an earlier round already fixed; if the fix does not remove the failure
  mode, report the surviving trigger, not a new variant

## Volume

Report volume tracks your reasoning effort, not defect density. Five verified findings beat forty
candidates; a candidate that costs a verification round and dies is a net loss, not a free option.
Unsure whether something clears the bar means it doesn't.
