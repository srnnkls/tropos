# Issue template

Body sections use `#` headings; nested subsections step down to `##`, `###`.

## Title

Per [Template](../SKILL.md#template); module is the top-level concern, summary a noun phrase without trailing period.

## Body sections (in order)

### `# Goal` (required)

One paragraph: what the issue produces and why. Relationships: [Issue metadata](../SKILL.md#issue-metadata-type-parent-dependencies).

### `# Context` (optional)

Only when the issue builds on prior work the reader must know: what has landed and what is missing, as a delta.

### `# Layout` (architecture / service-level work only)

Fenced ASCII tree of the changed files, grouped by directory, one-line comment per file; mark untouched files in the same module `# unchanged`.

Only for planning or reshaping architecture at module / service / package level (new module or service, directory restructure, cross-cutting refactor); never for changes confined to one module that add or move no modules or public APIs, bug fixes, small enhancements, doc/tooling tweaks, test additions, dependency bumps, or follow-ups to an already-laid-out module.

### `# Implementation plan` (required for non-trivial issues)

`##` subsection per applicable construct, named for the repo's constructs, in this order:

- `## Interface` — function/method/endpoint signatures
- `## Core logic` — main flow or algorithm
- `## Data types` — domain types, identifiers, shapes
- `## Errors` — failure modes and how they surface
- `## Dependencies` — injected collaborators and inputs

Name phases by action (`## Fixpoint BFS for X`), not "Step 1 / Step 2". Code per [sketches.md](sketches.md). Trivial issues: a `# Plan` paragraph or nothing.

### `# Constraints` (when design rules bind the implementer)

Bullet list of binding design rules, citing the convention or prior decision each comes from.

### `# What landed where` (optional)

Only for partially merged work; commits by short SHA + subject.

### `# Follow-up` (optional)

Only for already-existing issues that pick up split-out scope.

### `# Definition of done` (required)

`- [ ]` items, each testable and binary, ending with the applicable toolchain gates (typecheck / lint / unit / integration).

## Section selection by issue type

| Issue type | Required | Optional |
|---|---|---|
| Architecture-level Feature (new module / new service) | Goal, Layout, Implementation plan, Definition of done | Context, Constraints, What landed where, Follow-up |
| Architecture-level refactor (module boundary restructure) | Goal, Layout, Implementation plan, Definition of done | Context (usually yes), Constraints, What landed where |
| Non-architecture Feature / Task (behavior change inside an existing module) | Goal, Implementation plan, Definition of done | Context, Constraints, Follow-up — no Layout |
| Bug fix | Goal, Definition of done | Context (repro), Implementation plan (if non-obvious) — no Layout |
| Doc / tooling tweak | Goal, Definition of done | Implementation plan — no Layout |

## Header conventions

- Atx headers only; one blank line above and below each.
- Inline code in headers only when the symbol is the subject.
- GFM tables, alignment colons only for numbers.
- Fenced code blocks with a language tag.

## Cross-referencing

- Issues: `#<number>`, never the URL.
- File paths in prose: backticks, with `:line` or `:start-end`.
- Repo paths: full from repo root, no leading `./`.

## Reference issues

Exemplars: `gh issue view <n>`; copy shape, not the `##` top level of older issues.
