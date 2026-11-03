# Question Taxonomy Reference

## Validation Loop

1. Settle facts before asking: dispatch a subagent for every gap the repository, documentation, or tools can answer. The user receives only questions of intent and decision, never implementation details they cannot judge.
2. Order uncovered (`partial`/`missing`) areas by [Impact × Uncertainty](#prioritization-heuristic), Scope first. Hold back a question whose answer depends on one still open.
3. Ask one area's questions per batch, with options.
4. [Re-evaluate](#re-evaluation-between-batches) remaining questions.
5. Repeat until the [question limit](issue-types.md) is reached, no question scoring 6 or more remains, or the user signals "enough clarification".
6. Record every gap left unasked under `assumptions` in `validation.yaml` with the default taken; set `load_bearing: true` when a different answer would change tasks, interfaces, or the data model.

## Question Format

Each question in a batch:

:::user-question{header="[Area]" question="First question about [area]?"}
- Option A: [implication]
- Option B: [implication]
- Option C: [implication]
:::

Allow multiple answers only when they make sense; headers are the area name, max 12 chars.

A batch holds at most 3 questions; every question counts against the issue type's [question limit](issue-types.md).

When codebase patterns, industry standards, or project conventions favor one option, list it first and append "(Recommended)" to its label.

## Area Templates

Ask Design questions only when the user selected Design in the SDD opt-ins (Step 3.5).

Conventions: resolve each axis the change touches from the `code.style`, `implement.approach`, and `test.approach` providers and the nearest existing code before asking; ask only where they are silent, conflict, or the user's intent may deviate. Ask which existing design the change must keep, and record each answer as an invariant with its check.

Option templates (header = area; each list ends with the None option):

| Area | Question | Options (choice - trade-off) | None |
|---|---|---|---|
| Scope | What boundaries define this [initiative/feature/task]? | Narrow: [minimal scope] - Faster delivery, less complexity; Balanced: [moderate scope] - Covers core needs, reasonable timeline; Comprehensive: [broad scope] - Complete solution, longer timeline | Keep scope as currently described |
| Behavior | How should [component] handle [scenario]? | Strict: [fail fast behavior] - Clear feedback, no ambiguity; Lenient: [permissive behavior] - Flexible, may mask issues; Configurable: [user chooses] - Most flexible, more complexity | Use standard/existing behavior patterns |
| Data Model | What structure should [entity] have? | Minimal: [few fields] - Simple, easy to extend later; Standard: [common fields] - Covers typical use cases; Rich: [many fields] - Comprehensive, more upfront work | Use existing patterns from codebase |
| Constraints | What constraints should guide this design? | Performance-first: [speed/efficiency focus] - May sacrifice flexibility; Compatibility-first: [integration focus] - May sacrifice performance; Simplicity-first: [minimal complexity] - May sacrifice features | No specific constraints beyond standard practices |
| Edge Cases | How should [component] handle [edge case]? | Error: Fail with clear message - Explicit, no hidden behavior; Fallback: Use default/safe value - Graceful, may mask issues; Skip: Ignore silently (if safe) - Simplest, may confuse users | Handle like any other case (no special treatment) |
| Integration | How should [new component] integrate with [existing system]? | Direct: Tight coupling - Simple, fast, harder to change later; Adapter: Interface layer - Decoupled, more code; Event-based: Async communication - Loosely coupled, more complex | Standalone (no integration needed) |
| Terminology | What should we call [concept]? | [Term A]: Matches [existing usage] - Consistent with codebase; [Term B]: More precise - Clearer meaning, new convention; [Term C]: Industry standard - Familiar to newcomers | Use whatever fits naturally |
| Conventions | How should [axis] work in [component]? | Provider: [rule from the provider] - Consistent with existing guidance; Mirror: follow [exemplar file] - Consistent with nearest existing code; Deviate: [decision] - Recorded as a scope decision | Provider default applies |
| Design | What design aspects need exploration? | Alternatives: Rejected approaches need documenting - Capture reasoning; Invariants: Correctness properties to maintain - Enable test linkage; Complexity: Before/after comparison needed - Justify the change | Design reasoning is straightforward |

## Prioritization Heuristic

| Factor | High (3) | Medium (2) | Low (1) |
|--------|----------|------------|---------|
| Impact | Affects architecture | Affects implementation | Affects details |
| Uncertainty | No information | Partial information | Clear from context |

Ask in descending score: 9 first, then 6. Record lower scores as assumptions instead of asking.

## Re-evaluation Between Batches

- Skip pending questions an answer made irrelevant.
- When a custom answer spans multiple areas, add a focused follow-up on that ambiguity to the next batch.
