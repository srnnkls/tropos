# Gestalt Structural Review Protocol

A structured review protocol where the agent uses gestalt commands to build structural understanding, generates targeted questions for the human, and produces a grounded review verdict.

No new gestalt features required — only the existing CLI.

---

## Phase 0: Orient

```bash
gestalt map --tokens 4096
gestalt diff <base>..<target> --format json
```

Parse the diff JSON. Extract:
- List of changed symbols with `change_kind`, `file`, `line`, `callers`, `is_bridge`, `is_root`, `is_leaf`
- Files touched
- Number of additions, modifications, removals, renames

---

## Phase 1: Triage

From the diff JSON, classify the change:

| Classification | Condition | Depth |
|---|---|---|
| **Test-only** | All changed files are test files | Low — spot check |
| **Plumbing** | No bridges, no roots modified, all changes in one community | Spot check |
| **Business logic** | Changed symbols are interior nodes (not bridges, have both callers and callees) | Intent review |
| **Boundary** | Any changed symbol is a bridge, or any root symbol is modified/added | Full review |
| **New service** | Majority of changed symbols are `Added` and form a connected cluster | Architecture review |

Determine from JSON fields: `is_bridge`, `is_root`, `is_leaf`, `change_kind`, callers count.

**Confirm with human** via `AskUserQuestion`:

```
Header: Triage
Question: This PR touches [N] bridge symbols and modifies [M] roots. I'm classifying it as a [CLASSIFICATION] change ([depth]). Does that match?
multiSelect: false
Options:
- Correct: Proceed with [CLASSIFICATION] depth
- [alt classification 1]: Reclassify — provide description of why
- [alt classification 2]: Reclassify — provide description of why
```

Generate the alternative options from the classification table — offer the two most plausible alternatives based on the diff data.

---

## Phase 2: Identify Review Targets

Sort changed symbols by risk priority:

1. **Chain roots** — `is_root: true` and `change_kind: Added` — unvalidated premises
2. **Bridges** — `is_bridge: true` — cross-community connectors
3. **High-caller symbols** — sort by callers count descending — blast radius
4. **Everything else** — ordered by rank within the diff

For the top 3–5 symbols, drill deeper:

```bash
gestalt callers <symbol>          # Who depends on this?
gestalt callees <symbol>          # What does this depend on?
gestalt blame <symbol>            # Who wrote this, when?
gestalt log <symbol> --limit 5    # How has this evolved?
```

Build a structural profile per symbol:
- Caller count and caller locations (files/communities)
- Callee count and whether callees are internal or external
- Authorship: human-written being modified, or agent-generated?
- Stability: last changed yesterday or 6 months ago?

---

## Phase 3: Generate Targeted Questions

For each high-priority symbol, generate questions based on its structural profile. Questions map to failure modes.

### Question templates

**Added chain root:**
> [symbol] was added in this PR and [N] other symbols depend on it (callers: [list]). This is the premise of the change chain.

**Bridge with high callers:**
> [symbol] connects [N] callers across [files]. Its callees include [list]. Changing this symbol affects [domains/files].

**Test alongside production code:**
Run `gestalt callees <test_function>` and `gestalt callees <production_function>`. Compare:
> [test] calls [test_callees]. The function it tests ([prod]) calls [prod_callees]. The test shares [overlap_count] callees with production.

**Zero test callers in diff:**
> [symbol] was modified/added but no test in this diff references it.

**Modified symbol last changed long ago:**
> [symbol] was last changed [date] by [author]. It has [N] callers.

### Presenting questions

Batch questions into `AskUserQuestion` calls (max 4 questions per call). For each question, derive options from the structural profile:

```
Header: [symbol]
Question: [structural context from template above]. [specific question — e.g. "Does this preserve the caller contract?"]
multiSelect: false
Options:
- Yes, correct: [what "correct" means for this symbol — e.g. "Contract preserved, callers updated"]
- No, issue: [the failure mode this question is testing — e.g. "Callers not updated for new signature"]
- Needs investigation: Flag for follow-up before verdict
```

**Rules:**
- Group related symbols into a single `AskUserQuestion` call (up to 4 questions)
- Use multiple calls if >4 questions
- Don't rubber-stamp — wait for all answers before proceeding to Phase 4
- Record each answer for the Phase 5 verdict (resolved vs. unresolved)

---

## Phase 4: Analyze Codebase Context

For files touched by the change, run structural analysis:

```bash
gestalt analyze --file <changed_file_1>
gestalt analyze --file <changed_file_2>
gestalt rank --file <changed_file_1>
```

Check for:
- **Cycles** — any changed symbols in an SCC with >1 member?
- **Dispatchers** — any changed symbols are dispatchers (high fan-out)? Are their callees all correct?
- **Community structure** — do changes stay within existing communities, or introduce new cross-community edges?

Flag structural anomalies:

```
"This change introduces a new cycle between [symbols].
Is this intentional mutual dependency, or accidental coupling?"
```

---

## Phase 5: Verdict

Based on structural analysis, human answers, and code reading, produce:

```markdown
## Review: [target] — [title]

### Triage: [CLASSIFICATION]

### Risk Assessment
- Chain depth: [N] (root: [chain description])
- Bridge symbols modified: [N] ([list])
- Blast radius: [N] callers affected across [N] files
- New cycles introduced: [none|list]
- Untested changes: [N] ([list])

### Questions Resolved
- [x] [question summary] (human confirmed)
- [ ] [unresolved question] — flagged for follow-up

### Structural Signals
- ⚠ [symbol]: [signal description]
- ✓ [symbol]: [positive signal]

### Decision: [APPROVE | REQUEST CHANGES | COMMENT]
Reason: [grounded in structural evidence and human-confirmed facts]
Action: [specific next step if not approving]
```

---

## Key Principle

The agent doesn't review alone. It uses gestalt to identify **where** to look, generates questions that force **domain engagement**, and relies on the human for **semantic judgment**. The protocol makes the agent a structural analyst and question generator, not a judge.

---

## What This Buys Over Naive Review

1. **Starts with structure, not text** — sees change topology before reading code
2. **Asks specific questions** — grounded in caller/callee data, not generic
3. **Quantifies blast radius** — facts the agent cannot infer from the diff alone
4. **Routes the hard questions to the human** — premises, domain accuracy, boundary contracts
5. **Produces a grounded verdict** — references structural evidence and human-confirmed facts
