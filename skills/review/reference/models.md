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
| openai-gpt5.4 | openai-codex/gpt-5.4 | OpenAI |
| gemini-3-flash | google-gemini-cli/gemini-3-flash-preview | Google |
| gemini-3.1-pro | google-gemini-cli/gemini-3.1-pro-preview | Google |

### GitHub Copilot Alternatives

| Display Name | Model Path |
|---|---|
| gpt5.4-copilot | github-copilot/gpt-5.4 |
| gemini-3.1-pro-copilot | github-copilot/gemini-3.1-pro-preview |

### Invocation
```bash
timeout 1200 pi -p --model openai-codex/gpt-5.4 --thinking {reasoning} "{prompt}"
timeout 1200 pi -p --model google-gemini-cli/gemini-3-flash-preview --thinking {reasoning} "{prompt}"
timeout 1200 pi -p --model google-gemini-cli/gemini-3.1-pro-preview --thinking {reasoning} "{prompt}"
```

---

## Thinking Level Format

`--thinking {level}` (e.g., `high`)

| Level | Use for |
|---|---|
| low | Quick responses |
| medium | Balanced (default) |
| high | Deep analysis (recommended) |
| xhigh | Maximum reasoning |

**Note:** Google native models (`google-gemini-cli/`) use `thinkingLevel` internally.
Use `github-copilot/` Gemini models for thinking level control.
