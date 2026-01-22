---
name: code-review
description: Code review methodology. Use when reviewing code locally or preparing for a PR review.
---

# Code Review Skill

Multi-perspective code review using parallel subagent dispatch for comprehensive analysis.

> **Reference:** See [reference/roles/](reference/roles/) for reviewer personas, [reference/report-format.md](reference/report-format.md) for YAML schemas, [reference/playbook.md](reference/playbook.md) for edge case handling.

---

## When to Use

- Reviewing code changes locally before commit
- Preparing review feedback for a PR
- Analyzing code quality across multiple dimensions
- Getting diverse perspectives on implementation choices

---

## Workflow

### Step 1: Identify Code to Review

1. Parse target from argument (e.g., `/code.review src/auth/`)
2. If no argument: use staged changes (`git diff --cached`)
3. If no staged changes: use unstaged changes (`git diff`)
4. If no changes: ask user to specify file/directory

### Step 2: Detect Language and Load Guidelines

1. Identify primary language(s) from file extensions
2. Load language-specific patterns from `code-implement` skill if available
3. Note project conventions from CLAUDE.md

### Step 3: Select Reviewers

Use **AskUserQuestion** with multiSelect to choose reviewers:

```
Header: Reviewers
Question: Which reviewers should analyze this code?
multiSelect: true
Options:
- claude-opus: Claude Opus - native subagent, context-aware, codebase access
- claude-sonnet: Claude Sonnet - faster native review
- openai-gpt5.2: OpenAI GPT-5.2 - base model
- openai-gpt5.2-codex: OpenAI GPT-5.2 Codex - code-specialized
- openai-gpt5.2-pro: OpenAI GPT-5.2 Pro - extended capabilities
- gemini-3-flash: Google Gemini 3 Flash - fast, efficient
- gemini-3-pro: Google Gemini 3 Pro - advanced reasoning
```

**Default selection:** claude-opus, openai-gpt5.2-codex

**Model mapping to commands:**
- `claude-opus` → Task tool with `model: "opus"`
- `claude-sonnet` → Task tool with `model: "sonnet"`
- `openai-gpt5.2` → `opencode run --model "openai/gpt-5.2"`
- `openai-gpt5.2-codex` → `opencode run --model "openai/gpt-5.2-codex"`
- `openai-gpt5.2-pro` → `opencode run --model "openai/gpt-5.2-pro"`
- `gemini-3-flash` → `opencode run --model "google/gemini-3-flash-preview"`
- `gemini-3-pro` → `opencode run --model "google/gemini-3-pro-preview"`

### Step 4: Dispatch Reviewers in Parallel

**CRITICAL:** Dispatch all selected reviewers in the same message for true parallelism.

**Review Prompt Template:**

```
You are reviewing code for quality, correctness, and maintainability.

## Code to Review
[Include diff or file contents]

## Language
{LANGUAGE}

## Review Focus
Evaluate against these gates:

1. **Correctness** - Logic errors, edge cases, error handling, type safety
2. **Style** - Naming, formatting, idioms, readability
3. **Performance** - Efficiency, data structures, unnecessary work
4. **Security** - Input validation, secrets, injection risks
5. **Architecture** - Design patterns, coupling, separation of concerns

## Output Format
Return a YAML report:

```yaml
reviewer_report:
  reviewer: {REVIEWER_ID}
  gates:
    correctness:
      status: pass | fail
      issues: []
    style:
      status: pass | fail
      issues: []
    performance:
      status: pass | fail
      issues: []
    security:
      status: pass | fail
      issues: []
    architecture:
      status: pass | fail
      issues: []
  issues:
    - severity: critical | high | medium
      gate: correctness | style | performance | security | architecture
      area: ${AREA}
      location: "file:line"
      description: "Clear description"
      suggestion: "How to fix"
  strengths:
    - "Positive observation"
```
```

**Dispatch by Type:**

**Claude reviewers (Task tool):**
```python
Task(
  subagent_type="general-purpose",
  model="opus",  # or "sonnet"
  prompt=review_prompt
)
```

**OpenCode reviewers (Bash tool, background):**
```bash
timeout 300 opencode run --model "{MODEL_PATH}" "{review_prompt}"
```

### Step 5: Synthesize Reviews

After all reviewers complete:

1. **Parse reports** - Extract YAML from all outputs
2. **Merge issues:**
   - Deduplicate by location + description similarity
   - Combine issues flagged by multiple reviewers (higher confidence)
   - Note which reviewer(s) found each issue
3. **Aggregate gates:**
   - Gate fails if ANY reviewer fails it
   - Record which reviewer(s) failed each gate
4. **Prioritize by severity:**
   - Critical → High → Medium
   - Within severity, group by gate

### Step 6: Present Review

**Gate Summary Table:**

```
| Gate         | Status | Claude | Codex  | Gemini-3 Pro |
|--------------|--------|--------|--------|--------------|
| Correctness  | FAIL   | fail   | fail   | pass         |
| Style        | PASS   | pass   | pass   | pass         |
| Performance  | PASS   | pass   | pass   | pass         |
| Security     | FAIL   | fail   | pass   | fail         |
| Architecture | PASS   | pass   | pass   | pass         |
```

**Issues by Severity:**

```
## Critical (must fix)
- [C1] SQL injection in user input (Security) at src/db/query.py:45
  Found by: claude-opus, gemini-3-pro
  Suggestion: Use parameterized queries

## High (should fix)
- [H1] Missing null check before dereference (Correctness) at src/api/handler.ts:112
  Found by: claude-opus, opencode-codex
  Suggestion: Add guard clause

## Medium (consider)
- [M1] Variable name `x` is unclear (Style) at src/utils/calc.py:23
  Found by: opencode-codex
  Suggestion: Rename to `multiplier`
```

**Strengths (if any):**

```
## Strengths
- Clean separation of concerns in module structure
- Good error messages with context
```

### Step 7: Recommend Action

**All gates pass:**
```
Review complete. All gates passed.

Recommendation: Ready to commit/merge
```

**Issues found:**
```
Review complete. 2 gates failed.

Critical issues: 1
High issues: 1
Medium issues: 1

Recommendation: Address critical/high issues before proceeding
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

## Edge Cases

**OpenCode timeout (> 5 minutes):**
- Continue with completed reviews
- Note in output: "[Reviewer] timed out, partial results"

**One reviewer fails:**
- Parse what you can
- Report partial results with clear indication

**No reviewers selected:**
- Default to claude-opus only
- Warn: "Consider adding external reviewers for diverse perspectives"

**No code to review:**
- List recent changed files
- Ask user to specify target

**OpenCode not available:**
- Warn: "OpenCode not installed, using Claude only"
- Proceed with Claude reviewer

---

## Integration

**Command:** `/code.review [path]`

**Related skills:**
- `code-implement` - Language-specific patterns to check against
- `pr-review` - GitHub PR workflow (uses this for methodology)
- `code-debug` - Root cause analysis when issues found

---

## Reference

- [reference/roles/claude-reviewer.md](reference/roles/claude-reviewer.md) - Claude reviewer persona
- [reference/roles/opencode-reviewer.md](reference/roles/opencode-reviewer.md) - OpenCode reviewer persona
- [reference/report-format.md](reference/report-format.md) - YAML report schemas
- [reference/playbook.md](reference/playbook.md) - Edge case handling
- [reference/checklist.md](reference/checklist.md) - Review checklist
