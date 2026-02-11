# OpenCode Harness

External subprocess harness for fresh-perspective review execution.

---

## Characteristics

- **Fresh perspective:** No prior context, sees code as newcomer would
- **Multiple models:** OpenAI or Google, different reasoning patterns
- **Independent:** Separate process, no shared state
- **Full tool access:** Can run gestalt, read loqui files, execute git commands

---

## Strengths

- Catches assumptions that insiders miss
- Different models catch different issues
- Simulates new team member perspective
- Validates readability for external audiences
- Code-specialized models excel at pattern detection
- Full tool access enables all review roles (General, Architecture, Compliance)

---

## Available Models

**OpenAI:**
- `openai/gpt-5.2` - Base GPT-5.2 model
- `openai/gpt-5.3-codex` - Code-specialized variant (recommended)
- `openai/gpt-5.2` - Pro tier with extended capabilities

**Google:**
- `google/gemini-3-flash-preview` - Fast, efficient model
- `google/gemini-3-pro-preview` - Advanced reasoning capabilities

**Reasoning Effort (--variant flag):**

Format: `{reasoning}-medium` (verbosity fixed at medium)

- `low-medium` - Quick responses, minimal deliberation
- `medium-medium` - Balanced reasoning
- `high-medium` - Deep analysis, thorough deliberation (recommended for reviews)
- `xhigh-medium` - Maximum reasoning (GPT-5.2 only)

---

## Dispatch Configuration

Dispatches any role via `opencode run`. The role prompt determines review focus.

**Template:**
```bash
timeout 1200 opencode run --model "{MODEL}" --variant high-medium "{role_review_prompt}"
```

The `{role_review_prompt}` is the General, Architecture, or Compliance prompt from SKILL.md Step 4.

**Examples:**
```bash
# Any role × OpenAI Codex
opencode run --model "openai/gpt-5.3-codex" --variant high-medium "{prompt}"

# Any role × OpenAI GPT-5.2
opencode run --model "openai/gpt-5.2" --variant high-medium "{prompt}"

# Any role × Google Gemini 3 Pro
opencode run --model "google/gemini-3-pro-preview" --variant high-medium "{prompt}"
```

5-minute timeout prevents hanging.

---

## Limitations

- No prior session context (fresh perspective — this is also a strength)
- May flag "issues" that are project conventions
- Depends on external service availability

---

## Expected Behavior

- Runs `{diff_cmd}` or reads files as directed by the role prompt
- Runs gestalt commands (Architecture role) or reads loqui files (Compliance role) as directed
- Outputs structured YAML report
- Highlights clarity and readability issues effectively
- Catches common anti-patterns
