# Harnesses

Dispatch mechanisms for multi-agent review execution.

---

## Claude Harness (Native Subagent)

Full codebase access via tools; understands project conventions from CLAUDE.md; can cross-reference existing code and language-specific idioms from `implement`. Single model perspective; may be anchored by prior context.

### Dispatch

```
Task(
  subagent_type="reviewer",
  model="{native_alias}",
  prompt="{role_review_prompt}"
)
```

The `{role_review_prompt}` is the role-specific prompt from the domain skill (e.g., code review Step 4).

For `codex-native`, use Codex's native delegation interface and inherit the current session model
and reasoning. Never pass that reserved token to peer. `opus`/`sonnet` remain Claude-host-native;
`opus-cli`/`sonnet-cli` from `peer list` are external Claude CLI routes (read-only when dispatched
with `--agent reviewer`). Under Codex reject `opus`/`sonnet` and registry Codex-family peer aliases
in favor of `codex-native`. Under Claude reject `codex-native` and registry Claude-family peer
aliases in favor of native `opus`/`sonnet`. Cross-family peer routes remain valid.

### Expected Behavior

- Reads code thoroughly via Glob/Grep/Read
- Runs gestalt commands (Architecture role) or reads loqui files (Compliance role) as directed
- Outputs structured YAML report
- Provides actionable suggestions with concrete fixes
- References existing code when suggesting improvements

---

## External Peer Harnesses

External reviewers are dispatched **exclusively** through the generic
**[`peer` skill](../../peer/SKILL.md)** — never invoke an external harness directly. `peer` owns
the canonical model registry (`peer list`), reviewer-mode read-only access, the idle-stall
watchdog, retry-once, graceful skip, and parallel fan-out. Harness flags, exit codes, and model
strings live in that skill so this document cannot drift from them.

Fresh outside perspective and cross-model coverage catch assumptions insiders miss. External
reviewers explore the diff with tools but begin without the orchestrator's conversation context,
so their prompt must carry the requirements and review schema. Native reviewers are dispatched
directly as in-process Tasks; `peer` handles only external aliases.

---

## Dispatch Pattern

Per role, in a single message: Codex delegation for `codex-native`, one Task per configured
Claude-host-native reviewer, plus one `peer` only when external reviewers are configured.

Build a self-contained prompt before fan-out: materialize and embed the review target (including
the actual git diff), applicable requirements/context, and exact output schema. Workdirs and git
commands are supplemental for shell-capable reviewers; some read-only peers have no shell tool.

```
Codex native delegation(role=reviewer, prompt={role_review_prompt})  # codex-native on Codex
Task(subagent_type="reviewer", model={native_alias}, prompt={role_review_prompt})
Bash(run_in_background=true):
  # Only when external aliases are configured:
  peer -C {workdir} -d {role_outdir} --agent reviewer --peers {external_aliases} \
    --effort {reasoning} --prompt-file {role_outdir}/prompt.md
```

Write the complete materialized shared prompt to `{role_outdir}/prompt.md` before dispatch. Using
the prompt file avoids argv-size limits for embedded diffs and schemas.

For standalone `/review`, `{role_outdir}` is the per-run review home under `.reviews/<slug>/`,
pinned by the review skill's **Report Output Directory** section, not invented per dispatch.

For implementation-owned test, batch, and final review, reload the scope's `config.yaml` and use
`.peer/<scope>/<epoch>/<batch-or-final-review>/<stage-or-role>/`. Those calls carry the configured
aliases and effort directly and never write to `.reviews/` or consult
`validation.yaml.review_config`.

Read the TSV manifest `peer` prints; pull each `ok` report file, skip stalled/error/auth
rows (note them as partial results). Full contract — flags, manifest, exit codes — in the
**[peer skill](../../peer/SKILL.md)**.

---

## Timeout/Error Handling

External reviewer harnesses are handled inside `peer --agent reviewer` (idle watchdog +
retry-once + skip). For standalone `/review`, synthesize available results when at least one report
succeeds and disclose partial coverage. For implementation-owned gates, partial coverage cannot
pass: pause and deliberately redispatch until every execution class actually configured has a
successful report. See the **[peer skill](../../peer/SKILL.md)**.

Native dispatch timeout follows the same split: standalone review may use successful external
results; implementation-owned gates pause unless every configured execution class has a success.
Never proceed with zero reviews.

Parse failures:
- YAML not found: search for partial YAML, attempt parse, mark as failed
- Malformed YAML: report which reviewer failed, include raw output snippet, continue with parseable reviewers
