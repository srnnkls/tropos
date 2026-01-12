---
description: Start a red vs. blue team debate on a topic
---

## User Input

```text
$ARGUMENTS
```

## Task

Use the `start-debate` skill to facilitate a multi-perspective debate via team subagents.

**Topic:** `$ARGUMENTS` (required - the subject of the debate)

Follow the start-debate skill workflow to:
1. Initialize scratchpad at `./debates/{topic-slug}.md`
2. Configure team positions via AskUserQuestion
3. Spawn team subagents for opening arguments
4. Moderate the debate with user-controlled rounds
5. Conclude with synthesis and recommendations

> **See**: `.claude/skills/start-debate/SKILL.md` for complete workflow.
