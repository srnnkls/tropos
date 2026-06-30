# Models

Available models for multi-agent review dispatch.

**Canonical source:** the `peer` wrapper's registry is the single source of truth for
reviewer identity (id ↔ harness ↔ model ↔ alias). Run `peer list` for the live table of
ids, harnesses, models, and aliases — do not hardcode any of those values here. Dispatch
by passing the selected reviewer to `peer`, which resolves the model at runtime.

---

## Claude (native subagent)

Dispatch with the user-selected Claude model; do not hardcode a model string.

### Invocation
```
Task(subagent_type="general", model="{claude-model}", prompt="{prompt}")
```

`{claude-model}` is the model selected for this review run (resolved at dispatch time, never hardcoded).

---

## Codex, Gemini (external subprocess)

Defined and dispatched by the **[`peer` skill](../../peer/SKILL.md)** — its registry is
canonical (`peer list`), and it owns invocation, model strings, reasoning effort, and the
stall watchdog. Don't restate them here. Codex reasoning effort is `low|medium|high`
(default `high`); gemini bakes reasoning into the model name.
