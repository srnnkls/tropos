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

## External Harnesses (Codex, Gemini)

External reviewers are dispatched **exclusively** through the **[`peer` skill](../../peer/SKILL.md)** —
never `codex exec` / `gemini` directly. `peer` owns the canonical model registry (`peer list`),
the idle-stall watchdog (kills a hung backend in ~1 min instead of waiting a fixed cap),
retry-once, graceful skip, and parallel fan-out (`peer run`). Harness flags, exit codes,
and model strings live in that skill — this doc does not duplicate them, so they can't drift.

What these external harnesses add: fresh outside perspective, cross-model coverage, catching
assumptions insiders miss — and both are **agentic** (they explore the diff with tools, not just read a static prompt). Limitations: no project context; may flag conventions as issues.
The Claude harness above is the one `peer` cannot dispatch (in-process `Task`) — the agent
spawns it directly.

---

## Dispatch Pattern

Per role, in a single message: the Claude `Task` (required) plus one `peer run` that fans
the role prompt out to every configured external reviewer concurrently.

```
Task(subagent_type="general", prompt={role_review_prompt})          # Claude — agent-native
Bash(run_in_background=true):                                        # codex + gemini via peer
  peer run -d {role_outdir} --reviewers {external_aliases} --effort {reasoning} "{role_review_prompt}"
```

Read the TSV manifest `peer run` prints; pull each `ok` report file, skip stalled/error/auth
rows (note them as partial results). Full contract — flags, manifest, exit codes — in the
**[peer skill](../../peer/SKILL.md)**.

---

## Timeout/Error Handling

**External harnesses:** handled inside `peer` (idle watchdog + retry-once + skip); the
caller only reads `peer run`'s manifest status per reviewer and synthesises what landed —
see the **[peer skill](../../peer/SKILL.md)**. Never block the pipeline on an external harness.

**Claude subagent timeout:**
1. If an external harness (Codex/Gemini) succeeded: use those results
2. If all failed: report failure, suggest retry
3. Never proceed with zero reviews

**Parse failures:**
- YAML not found: search for partial YAML, attempt parse, mark as failed
- Malformed YAML: report which reviewer failed, include raw output snippet, continue with parseable reviewers
