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

## OpenCode Harness (External Subprocess)

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
timeout 1200 opencode run --model "{MODEL}" --variant {reasoning}-medium "{role_review_prompt}"
```

See [models.md](models.md) for available models and variant format.

### Expected Behavior

- Runs `{diff_cmd}` or reads files as directed by the role prompt
- Runs gestalt commands (Architecture role) or reads loqui files (Compliance role) as directed
- Outputs structured YAML report
- Highlights clarity and readability issues effectively
- Catches common anti-patterns

---

## Dispatch Mapping

| Harness | Tool | Template |
|---------|------|----------|
| Claude | Task | `Task(subagent_type="general", prompt={role_prompt})` |
| OpenCode | Bash | `timeout 1200 opencode run --model "{model}" --variant {reasoning}-medium "{role_prompt}"` |

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

# {Role} — OpenCode harnesses [0-N from config, for each role]
Bash(run_in_background=true):
  timeout 1200 opencode run --model "{model_1}" --variant {reasoning}-medium "{role_review_prompt}"
Bash(run_in_background=true):
  timeout 1200 opencode run --model "{model_2}" --variant {reasoning}-medium "{role_review_prompt}"
```

---

## Timeout/Error Handling

**OpenCode timeout (> 20 minutes):**
1. Continue with completed reviews
2. Add warning: "[Reviewer] timed out, partial results"
3. Proceed with synthesis using available data

**Claude subagent timeout:**
1. If OpenCode succeeded: use OpenCode results only
2. If both failed: report failure, suggest retry
3. Never proceed with zero reviews

**Parse failures:**
- YAML not found: search for partial YAML, attempt parse, mark as failed
- Malformed YAML: report which reviewer failed, include raw output snippet, continue with parseable reviewers
