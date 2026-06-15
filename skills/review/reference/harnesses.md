# Harnesses

Dispatch mechanisms for multi-agent review execution.

---

## Claude Harness (Native Subagent)

### Characteristics

- **Context-aware:** Full codebase access via tools
- **Pattern-aware:** Understands project conventions from CLAUDE.md
- **Comprehensive:** Can cross-reference with existing code
- **Consistent:** Follows established review methodology

### Strengths

- Deep understanding of project context
- Can verify patterns against actual codebase
- Catches integration issues with existing code
- Applies project-specific conventions
- Understands language-specific idioms from `implement`

### Limitations

- Single model perspective
- May be anchored by prior context

### Dispatch

```
Task(
  subagent_type="general",
  prompt="{role_review_prompt}"
)
```

The `{role_review_prompt}` is the role-specific prompt from the domain skill (e.g., code review Step 4).

### Expected Behavior

- Reads code thoroughly via Glob/Grep/Read
- Runs gestalt commands (Architecture role) or reads loqui files (Compliance role) as directed
- Outputs structured YAML report
- Provides actionable suggestions with concrete fixes
- References existing code when suggesting improvements

---

## Pi Harness (External Subprocess)

### Characteristics

- **Fresh perspective:** No prior context, sees code as newcomer would
- **Multiple models:** OpenAI or Google, different reasoning patterns
- **Independent:** Separate process, no shared state
- **Full tool access:** Can run gestalt, read loqui files, execute git commands

### Strengths

- Catches assumptions insiders miss
- Different models catch different issues
- Simulates new team member perspective
- Validates readability for external audiences
- Code-specialized models excel at pattern detection
- Full tool access enables all review roles

### Limitations

- No prior session context (fresh perspective — also a strength)
- May flag "issues" that are project conventions
- Depends on external service availability

### Dispatch

```bash
timeout 1200 pi -p --model {MODEL} --thinking {reasoning} "{role_review_prompt}"
```

See [models.md](models.md) for available models and thinking levels.

### Expected Behavior

- Runs `{diff_cmd}` or reads files as directed by the role prompt
- Runs gestalt commands (Architecture role) or reads loqui files (Compliance role) as directed
- Outputs structured YAML report
- Highlights clarity and readability issues effectively
- Catches common anti-patterns

---

## Agy Harness (External Subprocess)

### Characteristics

- **Fresh perspective:** No prior context, sees code as newcomer would
- **Independent:** Separate process, no shared state
- **Full tool access:** Can run gestalt, read loqui files, execute git commands

### Strengths

- Cross-model coverage distinct from Claude and Pi
- Catches assumptions insiders miss
- Simulates new team member perspective

### Limitations

- No prior session context (fresh perspective — also a strength)
- May flag "issues" that are project conventions
- Depends on external service availability
- Thinking level is fixed in the model name — no `--thinking` flag

### Dispatch

```bash
timeout 1200 agy -p --print-timeout 20m --model "{MODEL}" "{role_review_prompt}"
```

Default model: `Gemini 3.5 Flash (High)`. Run `agy models` for the full list. See [models.md](models.md).
`--print-timeout 20m` keeps agy's internal cap (default 5m) aligned with the outer `timeout`.

### Expected Behavior

- Runs `{diff_cmd}` or reads files as directed by the role prompt
- Runs gestalt commands (Architecture role) or reads loqui files (Compliance role) as directed
- Outputs structured YAML report

---

## Dispatch Mapping

| Harness | Tool | Template |
|---------|------|----------|
| Claude | Task | `Task(subagent_type="general", prompt={role_prompt})` |
| Pi | Bash | `timeout 1200 pi -p --model {model} --thinking {reasoning} "{role_prompt}"` |
| Agy | Bash | `timeout 1200 agy -p --print-timeout 20m --model "{model}" "{role_prompt}"` |

Roles provide the prompt content (gates, focus, report schema). Harnesses provide the transport.

---

## Dispatch Pattern

Cartesian product: roles × harnesses, all dispatched in a single message.

Domain skill defines roles. This infrastructure defines harnesses.

```
# Single message — all role × harness combinations in parallel:

# {Role} — Claude harness [required for each role]
Task(
  subagent_type="general",
  prompt={role_review_prompt}
)

# {Role} — Pi harness [from config, for each role]
Bash(run_in_background=true):
  timeout 1200 pi -p --model openai-codex/gpt-5.5 --thinking {reasoning} "{role_review_prompt}"

# {Role} — Agy harness [from config, for each role]
Bash(run_in_background=true):
  timeout 1200 agy -p --print-timeout 20m --model "Gemini 3.5 Flash (High)" "{role_review_prompt}"
```

---

## Timeout/Error Handling

**Pi or Agy timeout (> 20 minutes):**
1. Continue with completed reviews
2. Add warning: "[Reviewer] timed out, partial results"
3. Proceed with synthesis using available data

**Claude subagent timeout:**
1. If an external harness (Pi/Agy) succeeded: use those results
2. If all failed: report failure, suggest retry
3. Never proceed with zero reviews

**Parse failures:**
- YAML not found: search for partial YAML, attempt parse, mark as failed
- Malformed YAML: report which reviewer failed, include raw output snippet, continue with parseable reviewers
