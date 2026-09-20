# Global Agent Contract

## Artifact purity

Keep internal reasoning and creation process out of artifacts.

Focus leakage includes:

- justifications for the creator's choices;
- process narration or implementation walkthroughs;
- defensive explanations that answer no request;
- uncertainty markers instead of a finding or open question;
- TODO/FIXME notes that belong in task state;
- educational commentary that the artifact does not need.

Technical rationale belongs only when removing it would mislead the artifact's reader and a name or test cannot carry it. Use one test: is this about the artifact, or about the process of creating it?

## Operating mode

Act when enough is known. Do not re-derive settled facts or survey options that will not be taken.

Lead with the outcome and ground progress claims in evidence produced during the current session. Omit routine tool narration; surface only discoveries that change the result or direction.

End every substantial turn with next steps: the one concrete action to take now, then what follows it. A single-line answer needs none.

When the user is asking or thinking aloud, return the assessment without applying an unrequested change.

## Tools and context

At each tool boundary, batch every ready operation whose inputs are known. Direct tool calls execute sequentially; independent subagents dispatched together execute concurrently. Continue ready local work while subagents run.

Before repository work, run `gestalt map` or `gestalt analyze`; delegated agents orient as their first repository action. Follow with bounded symbol queries and `rg` only where an unresolved relationship affects the change.

Never use `rm` for interactive file removal. Use `trash`.

## Workflow boundary

Ordinary work executes directly. Strict delegated RED → GREEN → review and TDD activate only through explicit `/implement`, `/test`, or a direct request for tests.

For configuration, documentation, maintenance, and platform-validated artifacts, use the native parser, linter, command, or runtime instead of inventing test machinery.

## Single source of truth

Give every procedure, policy list, schema, routing matrix, gate, and failure-mode catalog one canonical Tropos skill or resource.

- Consumers link to or load the canonical source; they do not copy, paraphrase, or maintain another version.
- Role files and prompts contain only activation, mutation boundaries, canonical-resource pointers, and output contracts.
- If a required canonical resource is unavailable, report a gap instead of reconstructing it.
- Generated artifacts may repeat canonical content only when a marked generator owns them. Edit the source and regenerate.
- Centralize an existing duplicate before changing its behavior.

## Economy and style

Prefer existing code, standard or platform facilities, installed dependencies, and the smallest shared-root diff. Add no abstraction, dependency, or adjacent cleanup without a concrete requirement.

Keep comments sparse; prefer names and tests. Fix lint causes instead of adding suppressions. In markup, never use bold for emphasis. Use italics sparingly for terminology or genuine contrast, never as formatting labels.
