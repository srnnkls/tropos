# Claude Harness

Native subagent harness for context-aware review execution.

---

## Characteristics

- **Context-aware:** Has access to full codebase via tools
- **Pattern-aware:** Understands project conventions from CLAUDE.md
- **Comprehensive:** Can cross-reference with existing code
- **Consistent:** Follows established review methodology

---

## Strengths

- Deep understanding of project context
- Can verify patterns against actual codebase
- Catches integration issues with existing code
- Applies project-specific conventions
- Understands language-specific idioms from `code-implement`

---

## Limitations

- Single model perspective
- May be anchored by prior context

---

## Dispatch Configuration

**General role:**
```
Task(
  subagent_type="general-purpose",
  model="opus",
  prompt="[Review prompt with code content]"
)
```

**Architecture role:**
```
Task(
  subagent_type="task-reviewer",
  model="opus",
  prompt="[Architecture review prompt with gestalt instructions]"
)
```

**Compliance role:**
```
Task(
  subagent_type="task-reviewer",
  model="opus",
  prompt="[Compliance review prompt with loqui instructions]"
)
```

Use `model="opus"` for thorough review, `model="sonnet"` for faster results.

---

## Expected Behavior

- Reads code thoroughly
- May use Glob/Grep/Read to check codebase patterns
- Outputs structured YAML report
- Provides actionable suggestions with concrete fixes
- References existing code when suggesting improvements
