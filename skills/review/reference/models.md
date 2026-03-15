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

## OpenCode (external subprocess)

| Display Name | Model Path | Provider |
|---|---|---|
| openai-gpt5.4 | openai/gpt-5.4 | OpenAI |
| gemini-3-flash | google/gemini-3-flash-preview | Google |
| gemini-3.1-pro | google/gemini-3.1-pro-preview | Google |

### GitHub Copilot Alternatives

| Display Name | Model Path |
|---|---|
| gpt5.4-copilot | github-copilot/gpt-5.4 |
| gemini-3.1-pro-copilot | github-copilot/gemini-3.1-pro-preview |

### Invocation
```bash
timeout 1200 opencode run --model "openai/gpt-5.4" --variant {reasoning}-medium "{prompt}"
timeout 1200 opencode run --model "google/gemini-3-flash-preview" --variant {reasoning}-medium "{prompt}"
timeout 1200 opencode run --model "google/gemini-3.1-pro-preview" --variant {reasoning}-medium "{prompt}"
```

---

## Variant Format

Compound: `--variant {reasoning}-{verbosity}` (e.g., `high-medium`)
Canonical source: `~/dotfiles/.opencode/opencode.json`

| Variant | Reasoning | Verbosity | Use for |
|---|---|---|---|
| low-medium | low | medium | Quick responses |
| medium-medium | medium | medium | Balanced (default) |
| high-medium | high | medium | Deep analysis (recommended) |
| xhigh-medium | xhigh | medium | Maximum reasoning |
| high-low | high | low | Deep analysis, terse output |

**Note:** Google native models (`google/`) use `thinkingLevel` internally.
Use `github-copilot/` Gemini models for variant control.
