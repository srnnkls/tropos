# OpenCode Reviewer Role

External subprocess reviewer for fresh perspective analysis.

---

## Characteristics

- **Fresh perspective:** No prior context, sees spec as newcomer would
- **Different model:** Uses GPT-5.2, different reasoning patterns
- **Independent:** Separate process, no shared state
- **Quick:** Focused on provided content only

---

## Strengths

- Catches assumptions that insiders miss
- Different model catches different issues
- Simulates new team member perspective
- Validates clarity for external audiences

---

## Review Focus

1. **Completeness:** What's missing that a newcomer would need?
2. **Consistency:** Are terms and concepts self-consistent?
3. **Feasibility:** Do described tasks make logical sense?
4. **Clarity:** Can someone unfamiliar understand this?

---

## Dispatch Configuration

```bash
timeout 300 opencode run \
  --model openai/gpt-5.2 \
  --print-last \
  "[Review prompt with spec content]"
```

5-minute timeout prevents hanging.

---

## Expected Behavior

- Analyzes only provided content
- No access to codebase (fresh perspective)
- Outputs structured YAML report
- Highlights clarity issues effectively

---

## Limitations

- Cannot verify against actual codebase
- May flag "issues" that are project conventions
- Limited context for integration feasibility
- Depends on external service availability
