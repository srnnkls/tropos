---
name: code
description: Code domain. Composes with implement, review, and test skills for code-specific operations.
argument-hint: "[operation] [target]"
metadata:
  type: domain
---

## Pre-loaded Context

Git status:
!`git status --short 2>/dev/null`

Languages detected:
!`find . -maxdepth 3 -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.ts" -o -name "*.js" 2>/dev/null`

# Code Domain

Composes generic skills (`implement`, `review`, `test`) with code-specific context.

> [dispatch/protocol.md](../dispatch/protocol.md)

---

## Auto-Detect Rules

Parse `$ARGUMENTS` in order:

| Pattern | Route | Action |
|---|---|---|
| `implement [target]` | Implement | `Skill(implement, $REST)` with code context below |
| `review [target]` | Review | `Skill(review, $REST)` with code context below |
| `test [target]` | Test | `Skill(test, $REST)` with code context below |
| No argument | Menu | AskUserQuestion |

---

## Menu Fallback

When no argument, use **AskUserQuestion**:

```
Header: Code
Question: What code operation?
multiSelect: false
Options:
- Implement: Build features with language guidelines and code intelligence
- Review: Multi-perspective code review (correctness, architecture, compliance)
- Test: Test-driven development (RED-GREEN-REFACTOR)
```

**Routing by selection:**

| Selection | Action |
|---|---|
| Implement | `Skill(implement)` with code context below |
| Review | `Skill(review)` with code context below |
| Test | `Skill(test)` with code context below |

---

## Code Context (Injected into Generic Skills)

### For Implement

Language guidelines: `~/.claude/skills/loqui/reference/loqui/languages/{language}/README.md`

```
~/.claude/skills/loqui/reference/loqui/languages/{language}/
├── README.md              # Overview, core principles, anti-patterns checklist
├── quality.md             # Naming, comments, documentation conventions
├── composition.md         # Structuring behavior (classes/functions/modules)
├── modules.md             # Package structure, organization, public APIs
├── errors.md              # Error handling patterns and practices
└── ...                    # Additional language-specific resources
```

Use Read (not Glob) — paths outside cwd require direct reads.

Code intelligence: `gestalt map` for orientation, `gestalt callers`/`callees`/`refs` for symbol navigation.

### For Review

Reviewer Cascade — Three roles with distinct, non-overlapping concerns:

| Role | Concern | Primary Gates | Skill |
|------|---------|---------------|-------|
| **General** | Correctness, security, edge cases | Correctness, Security, Performance | code domain |
| **Architecture** | Structural impact, coupling, hotspots | Architecture | `gestalt` |
| **Compliance** | Language idioms, naming, patterns | Style | `loqui` |

Review reference: [reference/roles/](reference/roles/) for reviewer concerns, [reference/playbook.md](reference/playbook.md) for edge case handling, [reference/checklist.md](reference/checklist.md) for review checklist.

Compliance reviewer loqui path: `~/.claude/skills/loqui/reference/loqui/languages/{language}/`

### For Test

Language-specific test conventions — read loqui language guidelines for test patterns:
- `~/.claude/skills/loqui/reference/loqui/languages/{language}/test.md` (if exists)
- `~/.claude/skills/loqui/reference/loqui/languages/{language}/README.md` for general conventions

---

## Review Workflow

1. **Detect Input Type** — scope, git rev, git range, path, or diff
2. **Resolve Review Target** — pointers for reviewers to load code themselves
3. **Select Reviewers** — via `/review` infrastructure (interactive or from validation.yaml)
4. **Dispatch Reviewers in Parallel** — per role: one Claude `Task` + one `peer` (fans out to all configured external harnesses); never raw codex/gemini
5. **Synthesize Reviews** — per `/review` infrastructure
6. **Write Review Output** — scope review.yaml or ephemeral markdown
7. **Present Review** — gate summary, issues by severity
8. **Recommend Action** — pass/fail guidance

### Reviewer Prompt Templates

All prompts use `review_target` variables. Reviewers load code themselves.

**Variables:** `{diff_cmd}`, `{range}`, `{workdir}`, `{context}`, `{paths}`

**General Review Prompt:**

```
You are the GENERAL reviewer. Your gates: Correctness, Security, Performance.

## What to Review

Working directory: {workdir}

[if diff_cmd] Run: `{diff_cmd}`
[if paths] Read these files: {paths}

Context: {context}

## Review Focus

1. **Correctness** - Logic errors, edge cases, error handling, type safety
2. **Performance** - Efficiency, data structures, unnecessary work
3. **Security** - Input validation, secrets, injection risks

Leave architecture and style to specialized reviewers.

## Output Constraint
Your ENTIRE final message must be ONLY the YAML report below.
No prose, no explanation, no summary. The full subagent conversation gets embedded
into the parent session context — every extra token costs budget.

## Output Format
Standard reviewer_report YAML - see reference/report.md
```

**Architecture Review Prompt:**

```
You are the ARCHITECTURE reviewer. Your gate: Architecture.

## What to Review

Working directory: {workdir}

[if diff_cmd] Run: `{diff_cmd}`
[if paths] Read these files: {paths}

Context: {context}

## Structural Analysis (run these from {workdir})

1. `gestalt analyze` — Current architecture: hotspots, seams, coupling
2. [if range] `gestalt diff {range}` — Definition-level changes
3. [if range] `gestalt diff {range} --verbose` — Impact propagation layers
4. Additional as needed:
   - `gestalt callers <symbol>` for changed symbols with high fan-in
   - `gestalt callees <symbol>` for changed symbols with high fan-out
   - `gestalt rank --file <changed-file>` for centrality shifts

## Review Focus

1. **Coupling** — Did changes increase inter-module coupling?
2. **Hotspots** — Did changes create new high-centrality symbols?
3. **Cycles** — Did changes introduce dependency cycles?
4. **Seams** — Do changes respect existing cluster boundaries?
5. **Impact** — How far do changes propagate through the call graph?

Leave correctness, security, and style to other reviewers.

## Output Constraint
Your ENTIRE final message must be ONLY the YAML report below.
No prose, no explanation, no summary. The full subagent conversation gets embedded
into the parent session context — every extra token costs budget.

## Output Format
Architecture reviewer_report YAML - see reference/report.md
```

**Compliance Review Prompt:**

```
You are the COMPLIANCE reviewer. Your gate: Style.

## What to Review

Working directory: {workdir}

[if diff_cmd] Run: `{diff_cmd}`
[if paths] Read these files: {paths}

Context: {context}

## Loqui Guidelines (read these for each language in the diff)

1. Detect language(s) from file extensions
2. Read loqui language guidelines from:
   `./skills/loqui/reference/loqui/languages/{language}/README.md`
3. Read topic files relevant to the changes:
   - quality.md — naming, comments, documentation
   - composition.md — structuring behavior
   - modules.md — package structure, public APIs
   - errors.md — error handling patterns

## Review Focus

1. **Naming** — Do names follow loqui conventions? 5x rule applied?
2. **Composition** — Composition over inheritance? Proper behavior structuring?
3. **Modules** — Feature-based organization? Clean public APIs?
4. **Errors** — Language-idiomatic error handling?
5. **Anti-patterns** — Any items from the language README checklist?

Leave correctness, security, and performance to other reviewers.

## Output Constraint
Your ENTIRE final message must be ONLY the YAML report below.
No prose, no explanation, no summary. The full subagent conversation gets embedded
into the parent session context — every extra token costs budget.

## Output Format
Compliance reviewer_report YAML - see reference/report.md
```

**Scope Mode Appendix (appended to each reviewer's prompt):**

For `mode: scope-batch` (batch review), append:

```
## Batch Context

Tasks in this batch: {task_ids}
Scope directory: {scope_dir}

Read `{scope_dir}/tasks.yaml` for task requirements.
Read `{scope_dir}/review.yaml` for prior batch review history.
```

For `mode: scope-final` (final review), append:

```
## Final Review Context

You are performing a FINAL REVIEW of a complete scope implementation.

Scope directory: {scope_dir}

Read these files for full context:
- `{scope_dir}/scope.md` — requirements and acceptance criteria
- `{scope_dir}/tasks.yaml` — all tasks and their status
- `{scope_dir}/review.yaml` — batch review history and deferred issues

Additional focus:
- Scope Compliance — All requirements met? Acceptance criteria satisfied?
- Deferred Issues — Address or document remaining issues
- Integration — Components work together? No regressions?
- Test Coverage — All behaviors tested?
```

---

## Command

```
/code [operation] [target]
/code implement [target]
/code review [target]
/code review --scope <name>
/code review --final <name>
/code review --rev <ref>
/code review --path <path>
/code review --diff
/code test [target]
```

---

## Gates

| Gate | What It Checks |
|------|----------------|
| **Correctness** | Logic errors, edge cases, error handling, type safety |
| **Style** | Naming conventions, formatting, readability, idioms |
| **Performance** | Efficiency, data structures, unnecessary computation |
| **Security** | Input validation, secrets exposure, injection risks |
| **Architecture** | Design patterns, coupling, separation of concerns |

---

## Issue Areas

| Area | Covers |
|------|--------|
| `logic` | Control flow, algorithms, conditionals |
| `error_handling` | Exceptions, error states, recovery |
| `type_safety` | Type correctness, nullability |
| `naming` | Variable, function, class names |
| `formatting` | Code layout, indentation, spacing |
| `efficiency` | Time/space complexity, caching |
| `validation` | Input checking, sanitization |
| `secrets` | Credentials, keys, tokens |
| `coupling` | Dependencies, interfaces |
| `testing` | Test coverage, testability |

---

## Integration

**Related skills:**
- `implement` - Generic implementation methodology and scope execution pipeline
- `review` - Generic review infrastructure (models, harnesses, reports, synthesis)
- `test` - Generic TDD methodology
- `gestalt` - Architecture reviewer uses for structural analysis
- `loqui` - Compliance reviewer uses for language guidelines

---

## Reference

- [reference/roles/general.md](reference/roles/general.md) - General role (correctness, security, performance)
- [reference/roles/architecture.md](reference/roles/architecture.md) - Architecture role (coupling, hotspots, cycles, seams)
- [reference/roles/compliance.md](reference/roles/compliance.md) - Compliance role (naming, composition, modules, errors)
- [reference/playbook.md](reference/playbook.md) - Edge case handling
- [reference/checklist.md](reference/checklist.md) - Review checklist
- `/review` [reference/models.md](../review/reference/models.md) - Available models
- `/review` [reference/harnesses.md](../review/reference/harnesses.md) - Harness dispatch templates
- `/review` [reference/report.md](../review/reference/report.md) - YAML report schemas
- `/review` [reference/synthesis.md](../review/reference/synthesis.md) - Synthesis algorithm
