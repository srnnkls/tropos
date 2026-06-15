# Models

Available models for multi-agent review dispatch.

**Canonical source:** the `peer` wrapper's registry is the single source of truth for
reviewer identity (id ↔ harness ↔ model ↔ alias). Run `peer list` for the live table;
the tables below mirror it. Don't hardcode model strings in dispatch — pass the harness
to `peer` and let it supply the model.

```
$ peer list
REVIEWER-ID            HARNESS MODEL                      ALIAS   RUN-BY-PEER
codex-gpt5.5           codex   gpt-5.5                    gpt     yes
gemini-3.5-flash       gemini  gemini-3.5-flash           gemini  yes
claude-opus            claude  opus                       opus    no (agent Task)
claude-sonnet          claude  sonnet                     sonnet  no (agent Task)
```

---

## Claude (native subagent)

| Display Name | Model |
|---|---|
| claude-opus | opus |
| claude-sonnet | sonnet |

### Invocation
```
Task(subagent_type="general", model="opus", prompt="{prompt}")
Task(subagent_type="general", model="sonnet", prompt="{prompt}")
```

---

## Codex, Gemini (external subprocess)

Defined and dispatched by the **[`peer` skill](../../peer/SKILL.md)** — its registry is
canonical (`peer list`), and it owns invocation, model strings, reasoning effort, and the
stall watchdog. Don't restate them here. Codex reasoning effort is `low|medium|high`
(default `high`); gemini bakes reasoning into the model name.
