---
name: debate
description: Start structured red vs. blue team debates via subagents. Use when exploring a topic from multiple adversarial perspectives.
metadata:
  type: generic
henia:
  targets:
    claude:
      frontmatter:
        argument-hint: '[topic]'
    codex:
      openai:
        interface:
          display_name: Debate
          short_description: Apply the canonical debate skill workflow
          default_prompt: Use $debate for the requested task.
---

# Start Debate Skill

Moderate with [reference.md](reference.md).

::::head

## Workflow

### Step 1: Initialize Debate

Slug the topic and a context of at most 3 words ("API Design" → `api-design`), create `./debates/` if missing, copy [templates/debate-scratchpad.md](templates/debate-scratchpad.md) to `./debates/{topic}_{context}.md`.

### Step 2: Configure Teams

Ask with `AskUserQuestion`:

:::menu{header="Teams" question="Which additional teams should participate beyond Red and Blue?" .multi}
- None: Just Red and Blue
- Green Team: Pragmatic/implementation focus
- Yellow Team: Risk/safety analysis
- Purple Team: Synthesis/integration bridge
:::

Then ask the stance of Red (challenger/skeptic), Blue (defender/advocate), and each selected team. Write all stances to Team Positions.

### Step 3: Spawn Opening Arguments (Parallel)

Fill [templates/team-prompt.md](templates/team-prompt.md) once per team and launch all team subagents in one message with the Task tool.

### Step 4: Monitor and Moderate

1. Summarize the scratchpad's key points to the user.
2. Run the checks in [reference.md#interventions](reference.md#interventions) and write each failed check's intervention to Moderator Notes.
3. Ask the user: advance to rebuttals, request a synthesis round, or conclude.

### Step 5: Rebuttal Round (Sequential)

Spawn active teams one at a time, Red → Blue → Green → Yellow → Purple, each instructed to answer specific opposing arguments.

### Step 6: Synthesis Round (Optional)

On request, spawn Purple (or all teams) to find common ground, irreconcilable differences, and compromises.

### Step 7: Conclude Debate

Write Conclusion (Summary per team, Agreements, Disagreements, Recommendations if any); set status "Completed". Done when every active team wrote its section for each round run, every intervention is in Moderator Notes, and the user chose each round transition.

::::
