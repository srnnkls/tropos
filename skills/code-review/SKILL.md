---
name: code-review
description: Code review methodology. Use when reviewing code locally or preparing for a PR review.
---

# Code Review Skill

Multi-perspective code review using parallel subagent dispatch for comprehensive analysis.

> **Reference:** See [reference/roles/](reference/roles/) for reviewer concerns, [reference/harnesses/](reference/harnesses/) for dispatch configuration, [reference/report.md](reference/report.md) for YAML schemas, [reference/playbook.md](reference/playbook.md) for edge case handling.

---

## Reviewer Cascade

Three roles with distinct, non-overlapping concerns. Roles × harnesses dispatch in parallel.

### Roles

| Role | Concern | Primary Gates | Skill |
|------|---------|---------------|-------|
| **General** | Correctness, security, edge cases | Correctness, Security, Performance | `code-review` |
| **Architecture** | Structural impact, coupling, hotspots | Architecture | `gestalt` |
| **Compliance** | Language idioms, naming, patterns | Style | `loqui` |

### Harnesses

| Harness | Type | Characteristics |
|---------|------|-----------------|
| **Claude** | Task (native subagent) | Context-aware, tool access, codebase access |
| **OpenCode** | Bash (external subprocess) | Fresh perspective, no context, multiple models |

### Roles × Harnesses

| Role | Claude | OpenCode |
|------|--------|----------|
| General | 1 (required) | 0-N (from validation.yaml) |
| Architecture | 1 (required) | — (needs gestalt tools) |
| Compliance | 1 (required) | — (needs loqui file reads) |

**Cascade logic:** General covers breadth (and gets external harness diversity). Architecture goes deep on structure. Compliance goes deep on standards. Each role owns its gates.

---

## When to Use

- Reviewing code changes locally before commit
- Preparing review feedback for a PR
- Final review of a spec implementation
- Analyzing code quality across multiple dimensions

---

## Command

```
/code.review [target]
/code.review --spec <name>
/code.review --rev <ref>
/code.review --path <path>
/code.review --diff
```

**Target types (auto-detected by default):**
- **Spec name** → Final review of spec implementation
- **Git rev** → Review changes in commit(s)
- **Git range** → Review changes between refs
- **Path** → Review file or directory
- **No argument** → Review staged/unstaged changes

**Disambiguation flags (optional):**
- `--spec` → Force spec mode (e.g., spec named "main")
- `--rev` → Force git rev mode (e.g., path named "HEAD")
- `--path` → Force path mode (e.g., directory named "v1.0")
- `--diff` → Force diff mode (staged/unstaged changes)

---

## Workflow

### Step 1: Detect Input Type

**If flag provided, use it directly:**

```
--spec auth-system  → Spec mode (no detection)
--rev main          → Git rev mode (no detection)
--path ./main       → Path mode (no detection)
```

**Otherwise, auto-detect:**

```
Input                    | Detection                           | Mode
-------------------------|-------------------------------------|-------------
auth-system              | ./specs/active/auth-system/ exists  | Spec (final)
HEAD~3                   | Valid git rev                       | Git rev
main..feature            | Valid git range                     | Git range
abc123f                  | Valid commit SHA                    | Git rev
src/auth/                | Path exists                         | Path
(no argument)            | -                                   | Diff
```

**Auto-detection priority:**

1. **Check for spec:** `test -d ./specs/active/{arg}/`
   - If exists → **Spec mode** (final review)
2. **Check for git rev:** `git rev-parse --verify {arg} 2>/dev/null`
   - If valid → **Git rev mode**
3. **Check for git range:** contains `..` and valid refs
   - If valid → **Git range mode**
4. **Check for path:** `test -e {arg}`
   - If exists → **Path mode**
5. **No argument:**
   - Check `git diff --cached` → staged changes
   - Check `git diff` → unstaged changes
   - If neither → ask user

**Ambiguity examples:**
```bash
# "main" could be spec, branch, or directory
/code.review main           # Auto-detect (spec first, then git, then path)
/code.review --spec main    # Force: spec named "main"
/code.review --rev main     # Force: git branch "main"
/code.review --path main    # Force: directory named "main"
```

### Step 2: Load Review Context

**Spec mode:**
```
Read (in parallel):
  ./specs/active/<spec>/spec.md        # Requirements
  ./specs/active/<spec>/tasks.yaml     # Task definitions
  ./specs/active/<spec>/review.yaml    # Batch review history
  ./specs/active/<spec>/validation.yaml # Review config + reviewers
```

**Git rev/range mode:**
```bash
git show <rev>              # Single commit
git diff <range>            # Range (e.g., main..feature)
git log --oneline <range>   # Commit messages for context
```

**Path mode:**
```bash
# Read file(s) at path
# If directory, find changed files or all files
```

**Diff mode:**
```bash
git diff --cached           # Staged changes (preferred)
git diff                    # Unstaged changes (fallback)
```

### Step 3: Select Reviewers

**Spec mode:** Use config from `validation.yaml` (no prompt):

```yaml
review_config:
  reasoning_effort: high
  roles:
    general: true       # always true
    architecture: true   # gestalt-based structural review
    compliance: true     # loqui-based standards review
  harnesses:
    - openai/gpt-5.3-codex           # OpenCode harness for General role
    - google/gemini-3-pro-preview     # OpenCode harness for General role
```

**Other modes:** Use **AskUserQuestion**:

**Question 1:** Select roles:
```
Header: Roles
Question: Which review roles should analyze this code?
multiSelect: true
Options:
- general: General — correctness, security, performance (Recommended)
- architecture: Architecture — structural analysis via gestalt (Recommended)
- compliance: Compliance — language standards via loqui (Recommended)
```

**Default selection:** general, architecture, compliance

**Question 2:** Select OpenCode harnesses for General role:
```
Header: Harnesses
Question: Which external models should run the General review?
multiSelect: true
Options:
- openai-gpt5.3-codex: OpenAI GPT-5.3 Codex — code-specialized (Recommended)
- openai-gpt5.2-pro: OpenAI GPT-5.2 Pro — extended capabilities
- gemini-3-pro: Google Gemini 3 Pro — advanced reasoning
- none: Claude only — no external harnesses
```

**Default selection:** openai-gpt5.3-codex

**Question 3:** Select reasoning effort (if OpenCode harnesses selected):
```
Header: Reasoning
Question: What reasoning effort level for OpenCode harnesses?
multiSelect: false
Options:
- low: Quick responses, minimal deliberation
- medium: Balanced reasoning (Recommended)
- high: Deep analysis, thorough deliberation
- xhigh: Maximum reasoning (GPT-5.2 only)
```

**Default:** medium

**Dispatch mapping:**

| Role | Harness | Tool | Dispatch |
|------|---------|------|----------|
| General | Claude | Task | `subagent_type="general-purpose"`, `model="opus"` |
| General | OpenCode | Bash | `opencode run --model "{model}" --variant {reasoning}-medium` |
| Architecture | Claude | Task | `subagent_type="task-reviewer"`, `model="opus"` + gestalt |
| Compliance | Claude | Task | `subagent_type="task-reviewer"`, `model="opus"` + loqui |

### Step 4: Dispatch Reviewers in Parallel

**CRITICAL:** Dispatch ALL role × harness combinations in the SAME message for true parallelism.

**Dispatch:**

```
# Single message — all in parallel:

# General role — Claude harness [required]
Task(
  subagent_type="general-purpose",
  model="opus",
  prompt=general_review_prompt
)

# General role — OpenCode harnesses [0-N from config]
Bash(run_in_background=true):
  timeout 1200 opencode run --model "openai/gpt-5.3-codex" --variant {reasoning}-medium "{general_review_prompt}"
Bash(run_in_background=true):
  timeout 1200 opencode run --model "google/gemini-3-pro-preview" --variant {reasoning}-medium "{general_review_prompt}"

# Architecture role — Claude harness [required]
Task(
  subagent_type="task-reviewer",
  model="opus",
  prompt=architecture_review_prompt
)

# Compliance role — Claude harness [required]
Task(
  subagent_type="task-reviewer",
  model="opus",
  prompt=compliance_review_prompt
)
```

---

**General Review Prompt:**

```
You are reviewing code for correctness, security, and performance.

**First:** Invoke the `code-review` skill for review methodology.

## Code to Review
[Include diff or file contents]

## Context
[Git commit message, PR description, or spec requirements]

## Review Focus
Evaluate against these gates:

1. **Correctness** - Logic errors, edge cases, error handling, type safety
2. **Performance** - Efficiency, data structures, unnecessary work
3. **Security** - Input validation, secrets, injection risks

Leave architecture and style to specialized reviewers.

## Output Format
[Standard reviewer_report YAML - see reference/report.md]
```

**Architecture Review Prompt:**

```
You are performing a structural architecture review using gestalt code intelligence.

**First:** Invoke the `gestalt` skill.

## Code to Review
[Include diff or file contents]

## Gestalt Commands (run these)

1. `gestalt analyze` — Current architecture: hotspots, seams, coupling
2. `gestalt diff {base}..HEAD` — Definition-level changes
3. `gestalt diff {base}..HEAD --verbose` — Impact propagation layers
4. Run additional gestalt commands as needed:
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

## Output Format
[Architecture reviewer_report YAML - see reference/report.md#architecture-role-structural_analysis]
```

**Compliance Review Prompt:**

```
You are performing a language-standards compliance review using loqui guidelines.

**First:** Invoke the `loqui` skill.

## Code to Review
[Include diff or file contents]

## Loqui Guidelines (read these for each language in the diff)

1. Detect language(s) from file extensions
2. Read `~/.claude/skills/code-implement/resources/loqui/languages/{language}/README.md`
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

## Output Format
[Compliance reviewer_report YAML - see reference/report.md#compliance-role-compliance_analysis]
```

**Spec Mode Final Review Prompt (all reviewers):**

Append to each reviewer's prompt:

```
## Final Review Context
You are performing a FINAL REVIEW of a complete spec implementation.

### Spec Requirements
[Include spec.md content]

### Tasks Implemented
[Include tasks.yaml]

### Batch Review History
[Summarize from review.yaml]

### Deferred Issues
[List medium-severity issues from batch reviews]

### Additional Focus
- Spec Compliance — All requirements met? Acceptance criteria satisfied?
- Deferred Issues — Address or document remaining issues
- Integration — Components work together? No regressions?
- Test Coverage — All behaviors tested?
```

### Step 5: Synthesize Reviews

After all reviewers complete:

1. **Parse reports** - Extract YAML from all outputs (including `structural_analysis` and `compliance_analysis` sections)
2. **Merge issues:**
   - Deduplicate by location + description similarity
   - Combine issues flagged by multiple reviewers (higher confidence)
   - Note which reviewer(s) found each issue
   - Preserve specialized findings (coupling delta, loqui rule violations) as-is
3. **Aggregate gates:**
   - Each role owns its gates — gate verdict comes from the owning role
   - Within a role, gate fails if ANY harness fails it
   - On failure, record which harness(es) failed
4. **Prioritize by severity:**
   - Critical → High → Medium
   - Within severity, group by gate

### Step 6: Write Review Output

**Spec mode** → `./specs/active/<spec>/review.yaml`:

```yaml
final_review:
  status: completed
  timestamp: <ISO_TIMESTAMP>
  reviewers: [...]
  gates: { correctness: pass, style: pass, ... }
  spec_compliance:
    all_tasks_complete: true
    acceptance_criteria_met: true
    edge_cases_handled: true
  issues: [...]
  strengths: [...]
  recommendation: ready_to_merge | changes_requested

readiness:
  all_batches_reviewed: true
  critical_issues_resolved: true
  high_issues_resolved: true
  final_review_passed: true
  tests_passing: true
```

**Other modes** → `~/.claude/reviews/<generated-name>.md` (ephemeral):

```bash
# Generate review name based on input type
mkdir -p ~/.claude/reviews

# Git rev:    review-abc123f-2026-01-22T14-30.md
# Git range:  review-main..feature-2026-01-22T14-30.md
# Path:       review-src-auth-2026-01-22T14-30.md
# Diff:       review-staged-2026-01-22T14-30.md
```

**Ephemeral review format (Markdown):**

```markdown
# Code Review: <target>

**Date:** 2026-01-22T14:30:00Z
**Reviewers:** claude-opus, opencode-codex
**Target:** HEAD~3 | main..feature | src/auth/ | staged changes

## Gate Summary

| Gate         | Status | Claude | Codex  |
|--------------|--------|--------|--------|
| Correctness  | PASS   | pass   | pass   |
| Style        | PASS   | pass   | pass   |
| Performance  | PASS   | pass   | pass   |
| Security     | FAIL   | fail   | pass   |
| Architecture | PASS   | pass   | pass   |

## Issues

### Critical
- **[C1]** SQL injection in user input (Security)
  - Location: src/db/query.py:45
  - Found by: claude-opus
  - Suggestion: Use parameterized queries

### High
...

### Medium
...

## Strengths
- Clean separation of concerns
- Good error messages

## Recommendation
Address critical issues before proceeding
```

Reviews are stored ephemerally like Claude's internal plans - useful for reference but not committed to the repo.

### Step 7: Present Review

**Gate Summary Table (by role):**

```
| Gate         | Status | General | Architecture | Compliance |
|--------------|--------|---------|--------------|------------|
| Correctness  | PASS   | pass           | —            | —          |
| Style        | PASS   | —              | —            | pass       |
| Performance  | PASS   | pass           | pass         | —          |
| Security     | FAIL   | fail (Claude)  | —            | —          |
| Architecture | PASS   | —              | pass         | —          |
```

`—` = not in scope for this role. On failure, note which harness(es) failed in the issues section.

**Structural Analysis (Architecture role):**

```
Coupling: stable
New hotspots: none
Cycles introduced: none
Impact radius: 3 symbols
```

**Compliance Analysis (Compliance role):**

```
Languages: python
Rules evaluated: 12
Violations: 1 (naming/5x-rule at src/utils.py:23)
```

**Issues by Severity:**

```
## Critical (must fix)
- [C1] SQL injection in user input (Security) at src/db/query.py:45
  Found by: claude-opus
  Suggestion: Use parameterized queries

## High (should fix)
...

## Medium (consider)
...
```

**Spec mode additional output:**

```
### Spec Compliance
- All tasks complete: ✓
- Acceptance criteria met: ✓
- Edge cases handled: ✓

### Deferred Issues
- Resolved: 3
- Remaining: 0
```

### Step 8: Recommend Action

**All gates pass:**
```
Review complete. All gates passed.
Recommendation: Ready to commit/merge
```

**Issues found:**
```
Review complete. 1 gate failed.
Critical: 1, High: 0, Medium: 2
Recommendation: Address critical issues before proceeding
```

**Spec mode (all pass):**
```
Final review complete: auth-system
Recommendation: Ready to merge ✓
Next: Create PR with /pr.create or merge directly
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

## Examples

```bash
# Auto-detected (most common)
/code.review auth-system      # Spec → final review
/code.review HEAD~3           # Git rev → last 3 commits
/code.review main..feature    # Git range → branch diff
/code.review abc123f          # Git rev → specific commit
/code.review src/auth/        # Path → directory
/code.review                  # Diff → staged/unstaged

# Disambiguation flags (when names collide)
/code.review --spec main      # Spec named "main" (not git branch)
/code.review --rev main       # Git branch "main" (not spec/path)
/code.review --path HEAD      # Directory named "HEAD" (not git ref)
/code.review --rev v1.0       # Git tag "v1.0" (not path)
/code.review --diff           # Staged/unstaged changes explicitly
```

---

## Review Storage

| Mode | Location | Persistence |
|------|----------|-------------|
| Spec | `./specs/active/<spec>/review.yaml` | Committed with spec |
| Other | `~/.claude/reviews/<name>.md` | Ephemeral (like plans) |

**Naming convention for ephemeral reviews:**
- `review-<sha>-<timestamp>.md` - Git rev
- `review-<from>..<to>-<timestamp>.md` - Git range
- `review-<path-slug>-<timestamp>.md` - Path
- `review-staged-<timestamp>.md` - Staged changes

---

## Edge Cases

**Spec not found:**
- List available specs in `./specs/active/`
- Suggest closest match if typo likely

**Git rev invalid:**
- Report error, suggest valid refs
- List recent commits for reference

**OpenCode timeout (> 20 minutes):**
- Continue with completed reviews
- Note: "[Reviewer] timed out, partial results"

**No code to review:**
- List recent changed files
- Ask user to specify target

---

## Integration

**Command:** `/code.review [target]`

**Related skills:**
- `gestalt` - Architecture reviewer uses for structural analysis
- `loqui` - Compliance reviewer uses for language guidelines
- `code-implement` - Language-specific patterns to check against
- `pr-review` - GitHub PR workflow (uses this for methodology)
- `code-debug` - Root cause analysis when issues found
- `task-dispatch` - Batch reviews during implementation (Phase C)

---

## Reference

- [reference/roles/general.md](reference/roles/general.md) - General role (correctness, security, performance)
- [reference/roles/architecture.md](reference/roles/architecture.md) - Architecture role (coupling, hotspots, cycles, seams)
- [reference/roles/compliance.md](reference/roles/compliance.md) - Compliance role (naming, composition, modules, errors)
- [reference/harnesses/claude.md](reference/harnesses/claude.md) - Claude harness (native subagent)
- [reference/harnesses/opencode.md](reference/harnesses/opencode.md) - OpenCode harness (external subprocess)
- [reference/report.md](reference/report.md) - YAML report schemas
- [reference/playbook.md](reference/playbook.md) - Edge case handling
- [reference/checklist.md](reference/checklist.md) - Review checklist
