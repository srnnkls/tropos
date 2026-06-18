# Issue template

Structural shape only. Section names, ordering, heading levels, and what each section is for. No domain-specific content — drop in the actual subject matter at draft time.

Issue body sections use **first-level (`#`) headings**, with `##` / `###` for nested subsections.

## Title

`<Module> — <short summary>`

- Em-dash (`—`) separator, not a hyphen.
- Module is the top-level concern.
- Summary is a noun phrase, no trailing period.

## Body sections (in order)

### `# Goal` (required)

One paragraph stating what the issue produces and why.

Parent, depends-on, and blocks relationships live on GitHub's native metadata — set them via the skill's GraphQL mutations (`updateIssueIssueType`, `addSubIssue`, `addBlockedBy`) and let GitHub render them in the sidebar and sub-issue tree. The body stays focused on Goal / Implementation plan / Definition of done.

### `# Context` (optional)

Use only when the issue lands on top of prior work that the reader must understand. Document what's already landed and what's still missing — phrased as a delta. Skip for greenfield issues.

### `# Layout` (architecture / service-level work only)

Fenced ASCII tree of the files that change, one-line comment per file describing the change. Group by directory. Mark untouched files in the same module with `# unchanged`.

**Only include Layout when the issue plans or reshapes architecture at the module / service / package level** — new module, new service, directory restructure, cross-cutting refactor. The point of Layout is to pin down *where* structural pieces land before implementation starts.

**Skip Layout for any Feature or Task that is not architecture/service-level**, including:

- Changes confined to an existing file or a small group of files within one module.
- Behavior changes that don't introduce or relocate modules or public APIs.
- Bug fixes, small enhancements, doc/tooling tweaks, test additions, dependency bumps.
- Follow-ups that extend an already-laid-out module (`# Implementation plan` alone is enough).

If file footprint is incidental to the work — don't pad the issue with a Layout tree. Use `# Implementation plan` instead.

### `# Implementation plan` (required for non-trivial issues)

Use `##` subsections for each major construct. Order so a reader can start at the top: public shape first, then internals, then types, then errors, then dependencies.

Common subsections (use only the ones that apply, named for the repo's own constructs):

- `## Interface` — the public shape: function/method/endpoint signatures
- `## Core logic` — the main flow or algorithm
- `## Data types` — the domain types, identifiers, and shapes introduced
- `## Errors` — failure modes and how they surface
- `## Dependencies` — injected collaborators and inputs

Multi-phase work: name the action (`## Fixpoint BFS for X`), not "Step 1 / Step 2".

Code blocks are illustrative — signatures and shapes in the repo's own idioms, not full bodies.

For trivial issues, replace with a `# Plan` paragraph or omit.

### `# Constraints` (when design rules bind the implementer)

Bullet list of design rules. These bind the implementer — not suggestions. Reference the project's relevant conventions or prior decisions where they apply.

### `# What landed where` (optional)

Use only when filing to track work that has already partially merged. Reference commits by short SHA + subject.

### `# Follow-up` (optional)

Forward references to issues that pick up split-out scope. Include only when those issues already exist.

### `# Definition of done` (required)

GitHub-task-list checkboxes (`- [ ]`). Each item testable and binary. End with the toolchain gates that apply (the project's typecheck / lint / unit / integration commands).

## Section selection by issue type

| Issue type | Required | Optional |
|---|---|---|
| Architecture-level Feature (new module / new service) | Goal, Layout, Implementation plan, Definition of done | Context, Constraints, What landed where, Follow-up |
| Architecture-level refactor (module boundary restructure) | Goal, Layout, Implementation plan, Definition of done | Context (usually yes), Constraints, What landed where |
| Non-architecture Feature / Task (behavior change inside an existing module) | Goal, Implementation plan, Definition of done | Context, Constraints, Follow-up — **no Layout** |
| Bug fix | Goal, Definition of done | Context (repro), Implementation plan (if non-obvious) — **no Layout** |
| Doc / tooling tweak | Goal, Definition of done | Implementation plan — **no Layout** |

## Header conventions

- Markdown atx headers (`#`, `##`, `###`); no setext.
- Body top-level sections at `#` (h1). Nested subsections step down to `##`, `###`.
- One blank line above and below every header.
- Inline code in headers only when the symbol is the subject.
- Tables use github-flavored markdown, no alignment colons unless aligning numbers.
- Code blocks are fenced with the language tag.

## Cross-referencing

- Issue references: `#N`, never the full URL.
- File paths in prose: backticks, with `:line` or `:start-end` for ranges.
- Repo paths: full path from repo root, no leading `./`.

## Reference issues

For tone and section content, fetch live exemplars with `gh issue view <n>`. Read them for shape, not heading level (issues authored before the convention shift to `#` use `##`).
