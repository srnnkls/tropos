# Models

Available models for multi-agent review dispatch.

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

## Pi (external subprocess)

| Display Name | Model Path | Provider |
|---|---|---|
| openai-gpt5.5 | openai-codex/gpt-5.5 | OpenAI Codex |

### Invocation
```bash
timeout 1200 pi -p --model openai-codex/gpt-5.5 --thinking {reasoning} "{prompt}"
```

---

## Agy (external subprocess)

| Display Name | Model | Provider |
|---|---|---|
| agy-gemini-3.5-flash | Gemini 3.5 Flash (High) | Agy |

Thinking level is baked into the agy model name — there is no `--thinking` flag.
`--print-timeout 20m` is set so agy's internal cap (default 5m) matches the 20m outer `timeout`.
Run `agy models` for the full list. `Gemini 3.5 Flash (High)` is the default.

### Invocation
```bash
timeout 1200 agy -p --print-timeout 20m --model "Gemini 3.5 Flash (High)" "{prompt}"
```

---

## Thinking Level Format

Pi only. `--thinking {level}` (e.g., `high`)

| Level | Use for |
|---|---|
| low | Quick responses |
| medium | Balanced (default) |
| high | Deep analysis (recommended) |
| xhigh | Maximum reasoning |
