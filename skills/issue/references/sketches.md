# Implementation sketches — patterns

Guidance for the code that appears in `# Implementation plan`. Sketches are illustrative, not literal — they bind **shape** (signatures, module structure, error flow), not bodies.

## The one rule: match the repo

A sketch must read as if someone fluent in *this* codebase wrote it. Before sketching, learn the repo's idioms (`gestalt map`/`analyze`, `/loqui`, `CLAUDE.md`/`AGENTS.md`, a couple of neighbouring modules) and mirror them — naming grammar, error handling, how modules expose their public surface, how dependencies are wired. **Do not import a pattern the codebase doesn't already use.** A sketch that imposes a foreign stack is a blocking finding at the review gate.

## What a sketch shows

- **Public surface first.** The signatures a caller sees — function/method/endpoint shapes with their input and output types — before any internals.
- **Then internals.** The main flow or algorithm, in the repo's idiom (its loop/iteration constructs, its composition style). Phase-by-phase comments are fine; keep them to one line each.
- **Then types.** The domain types and identifiers introduced, in the repo's type vocabulary.
- **Then errors.** The failure modes and how they surface at the boundary, following the repo's error convention.
- **Then wiring.** How the piece is constructed and its dependencies are supplied — at the repo's composition root, not scattered through call sites.

Show signatures and shapes, never full bodies. The implementer writes the bodies.

## Prefer idiomatic constructs

Reach for the language's and the repo's idiomatic stdlib / combinators over hand-rolled equivalents — but only the ones the codebase already uses. Don't extract a helper purely to deduplicate boilerplate; extract only when it names a real intent.

## What NOT to put in sketches

- Implementation bodies past the shape — leave bodies to the implementer.
- Defensive validation on values already parsed/typed at the boundary (re-checking guaranteed fields, optional-chaining around non-nullable values).
- Test doubles written against a mocking library when the repo uses a different doubling strategy — match the repo's testing approach.
- Type casts or escape hatches where the language offers proper narrowing.
- Helper extraction motivated only by line count or DRY.
- Divider comments (`// ---`) and other decorative noise.
- Variable names referencing data structures (`tableMap`, `nodeArray`) — name by domain concept.
- Stub or placeholder nodes/edges standing in for real ones.

## When sketching the test plan in `Definition of done`

- State the doubling strategy the repo uses for unexercised collaborators (whatever the codebase's convention is — don't introduce a new one).
- Call out which tests need live/integration resources versus pure unit coverage.
- End with the project's check command (typecheck + lint + tests).
