# Implementation sketches — patterns

Applies to code in `# Implementation plan`.

## The one rule: match the repo

Apply the [repository-orientation contract](../../../instructions/AGENTS.md#tools-and-context), then mirror naming, error handling, public surfaces, and dependency wiring from the `code.style` providers ([code slots](../../code/SKILL.md#slots)), `CLAUDE.md` / `AGENTS.md`, and neighbouring modules. Use no pattern, stdlib facility, or combinator the codebase does not already use.

## What a sketch shows

Signatures and shapes, never full bodies, in order:

1. Public surface — caller-visible signatures with input and output types.
2. Internals — main flow in the repo's idiom; phase comments one line each.
3. Types — domain types and identifiers in the repo's type vocabulary.
4. Errors — failure modes at the boundary, per the repo's error convention.
5. Wiring — construction and dependency supply at the composition root.

## What NOT to put in sketches

- Defensive validation of values already parsed/typed at the boundary.
- Test doubles from a mocking library the repo does not use.
- Type casts or escape hatches where the language offers narrowing.
- Helpers extracted only for line count or DRY.
- Hand-rolled equivalents of stdlib or combinators the codebase uses.
- Divider comments (`// ---`).
- Names after data structures (`tableMap`, `nodeArray`) instead of domain concepts.
- Stub or placeholder nodes/edges.

## When sketching the test plan in `Definition of done`

- State the repo's doubling strategy for unexercised collaborators.
- Mark tests needing live/integration resources versus pure unit.
- End with the project's check command (typecheck + lint + tests).
