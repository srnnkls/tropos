# Question Taxonomy Reference

## Validation Loop

1. Order uncovered (`partial`/`missing`) areas by [Impact × Uncertainty](#prioritization-heuristic).
2. Ask one area's questions per AskUserQuestion batch, with options.
3. [Re-evaluate](#re-evaluation-between-batches) remaining questions.
4. Repeat until the question limit is reached, all primary areas are covered, or the user signals "enough clarification".

## Question Format

Batch format:

```
AskUserQuestion with questions array:

[
  {
    question: "First question about [area]?",
    header: "[Area]",
    multiSelect: false,
    options: [
      { label: "Option A", description: "[implication]" },
      { label: "Option B", description: "[implication]" },
      { label: "Option C", description: "[implication]" }
    ]
  },
  ...
]
```

Set `multiSelect: true` only when multiple answers make sense; headers are the area name, max 12 chars.

Batch limits:
- Tasks: up to 3 questions per batch, up to 3 batches
- Features/Initiatives: up to 4 questions per batch (AskUserQuestion max), up to 7 batches

When codebase patterns, industry standards, or project conventions favor one option, list it first and append "(Recommended)" to its label.

## Area Templates

Ask Design questions only when the user selected Design in the SDD opt-ins (Step 3.5).

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
| Design | What design aspects need exploration? | Alternatives: Rejected approaches need documenting - Capture reasoning; Invariants: Correctness properties to maintain - Enable test linkage; Complexity: Before/after comparison needed - Justify the change | Design reasoning is straightforward |

## Prioritization Heuristic

| Factor | High (3) | Medium (2) | Low (1) |
|--------|----------|------------|---------|
| Impact | Affects architecture | Affects implementation | Affects details |
| Uncertainty | No information | Partial information | Clear from context |

Ask in descending score: 9 first, then 6, then lower scores while questions remain.

## Re-evaluation Between Batches

- Skip pending questions an answer made irrelevant.
- When a custom answer spans multiple areas, add a focused follow-up on that ambiguity to the next batch.
