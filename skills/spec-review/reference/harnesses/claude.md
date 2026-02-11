# Claude Harness

Native subagent harness for context-aware spec review execution.

---

## Characteristics

- **Context-aware:** Has access to full codebase via tools
- **Pattern-aware:** Understands project conventions from CLAUDE.md
- **Comprehensive:** Can cross-reference with existing code
- **Consistent:** Follows established review methodology

---

## Strengths

- Deep understanding of project context
- Can verify feasibility against actual codebase
- Catches integration issues with existing code
- Applies project-specific conventions

---

## Limitations

- Single model perspective
- May be anchored by prior context

---

## Dispatch Configuration

```
Task(
  subagent_type="general",
  prompt="[Review prompt with spec content]"
)
```

Always use `subagent_type="general"` for Claude reviewers.

---

## Expected Behavior

- Reads spec documents thoroughly
- May use Glob/Grep/Read to check codebase
- Outputs structured YAML report
- Provides actionable suggestions
