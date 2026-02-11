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

Dispatches any role via the Task tool. The role prompt determines review focus.

```
Task(
  subagent_type="general",
  prompt="{role_review_prompt}"
)
```

The `{role_review_prompt}` is the General, Architecture, or Compliance prompt from SKILL.md Step 4.

---

## Expected Behavior

- Reads code thoroughly
- May use Glob/Grep/Read to check codebase patterns
- Runs gestalt commands (Architecture role) or reads loqui files (Compliance role) as directed by the role prompt
- Outputs structured YAML report
- Provides actionable suggestions with concrete fixes
- References existing code when suggesting improvements
