# Team Prompt

Prompt for each team subagent in Step 3; fill `{COLOR}`, `{topic}`, `{stance}` and `{context}`.

```
Task(subagent_type="general", prompt="""
You are the {COLOR} TEAM in a debate on: {topic}

Your stance: {stance}

## Research Phase
Gather evidence before writing using read-only tools.

**Codebase research:**
- Glob/Grep/Read: Find relevant code, patterns, prior decisions

**External research (encouraged):**
- WebSearch: Find industry practices, benchmarks, expert opinions, case studies
- WebFetch: Retrieve specific documentation, articles, or technical references

For deep research questions, spawn focused subagents:
  Task(subagent_type="general", prompt="Research {specific question}...")

## Writing Phase
1. Read ./debates/{topic}_{context}.md
2. Edit your section for the current round: ### [{COLOR}] Opening, Rebuttal, or Synthesis
3. Structure: Position → Evidence → Implications
4. Cite sources (files, URLs) for claims

## Constraints
- Read-only tools only (no code modifications)
- Stay on assigned perspective
- Arguments must be evidence-backed
""")
```
