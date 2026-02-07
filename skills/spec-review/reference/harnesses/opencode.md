# OpenCode Harness

External subprocess harness for fresh-perspective spec review execution.

---

## Characteristics

- **Fresh perspective:** No prior context, sees spec as newcomer would
- **Multiple models:** OpenAI or Google, different reasoning patterns
- **Independent:** Separate process, no shared state
- **Quick:** Focused on provided content only

---

## Strengths

- Catches assumptions that insiders miss
- Different models catch different issues
- Simulates new team member perspective
- Validates clarity for external audiences

---

## Available Models

Model paths depend on provider selection (native or github-copilot).

**OpenAI models:**
| Model | native | github-copilot |
|---|---|---|
| GPT-5.2 | `openai/gpt-5.2` | `github-copilot/gpt-5.2` |
| GPT-5.3 Codex | `openai/gpt-5.3-codex` | `github-copilot/gpt-5.3-codex` |

**Google models:**
| Model | native | github-copilot |
|---|---|---|
| Gemini 3 Flash | `google/gemini-3-flash-preview` | `github-copilot/gemini-3-flash` |
| Gemini 3 Pro | `google/gemini-3-pro-preview` | `github-copilot/gemini-3-pro` |

**Reasoning Effort (--variant flag):**

Format: `{reasoning}-medium` (verbosity fixed at medium)

- `low-medium` - Quick responses, minimal deliberation
- `medium-medium` - Balanced reasoning
- `high-medium` - Deep analysis, thorough deliberation (recommended for reviews)
- `xhigh-medium` - Maximum reasoning (GPT-5.2 only)

---

## Dispatch Configuration

**Template:**
```bash
timeout 1200 opencode run --model "{MODEL}" --variant high-medium "[Review prompt with spec content]"
```

**Examples (native provider):**
```bash
opencode run --model "openai/gpt-5.2" --variant high-medium "{prompt}"
opencode run --model "google/gemini-3-pro-preview" --variant high-medium "{prompt}"
opencode run --model "openai/gpt-5.3-codex" --variant high-medium "{prompt}"
```

**Examples (github-copilot provider):**
```bash
opencode run --model "github-copilot/gpt-5.2" --variant high-medium "{prompt}"
opencode run --model "github-copilot/gemini-3-pro" --variant high-medium "{prompt}"
opencode run --model "github-copilot/gpt-5.3-codex" --variant high-medium "{prompt}"
```

5-minute timeout prevents hanging.

---

## Limitations

- Cannot verify against actual codebase
- May flag "issues" that are project conventions
- Limited context for integration feasibility
- Depends on external service availability

---

## Expected Behavior

- Analyzes only provided content
- No access to codebase (fresh perspective)
- Outputs structured YAML report
- Highlights clarity issues effectively
