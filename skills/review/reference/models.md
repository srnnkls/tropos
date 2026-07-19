# Models

Available agents for multi-agent review dispatch.

**Canonical source:** the `peer` wrapper's registry is the single source of truth for
external identity (id ↔ harness ↔ model ↔ alias). Run `peer list` for the live table of
ids, harnesses, models, and aliases — do not hardcode any of those values here. Dispatch
external reviewers with `peer --agent reviewer --peers <aliases>`, which resolves models at runtime.

`codex-native` may appear in the live table with `native=true`, but it is a reserved Codex-host
delegation token and must never be passed to peer. It inherits the session model/reasoning.

---

## Claude (native subagent)

Dispatch with the user-selected Claude model; do not hardcode a model string.

### Invocation
```
Task(subagent_type="reviewer", model="{claude-model}", prompt="{prompt}")
```

`{claude-model}` is the model selected for this review run (resolved at dispatch time, never hardcoded).

`opus`/`sonnet` are Claude-host-native aliases. Registered `opus-cli`/`sonnet-cli` are distinct
external Claude CLI aliases and run through peer (reviewer dispatch is read-only; tester and
implementer dispatch may mutate).

Use registry harness/family metadata for host compatibility: Codex hosts reject all Codex-family
peer aliases in favor of `codex-native`; Claude hosts reject all Claude-family peer aliases in
favor of native `opus`/`sonnet`. Allow cross-family and unrelated peer aliases.

---

## External subprocess peers

Defined and dispatched by the generic **[`peer` skill](../../peer/SKILL.md)** — its registry is
canonical (`peer list`), and it owns invocation, model strings, reasoning effort, reviewer-mode
read-only access, retry, and the stall watchdog. Do not restate backend details here.
