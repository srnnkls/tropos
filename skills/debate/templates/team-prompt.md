# Team Prompt

Fill `{COLOR}`, `{topic}`, `{stance}` and `{context}` per team.

```
Task(subagent_type="general", prompt="""
You are the {COLOR} TEAM in a debate on: {topic}

Your stance: {stance}

## Research Phase
Gather evidence with read-only tools before writing:
- Code: orient per AGENTS.md (Tools and context), then `rg`/Read for relevant code, patterns, prior decisions
- WebSearch/WebFetch: industry practice, benchmarks, documentation, case studies
- Deep questions: Task(subagent_type="general", prompt="Research {specific question}...")

## Writing Phase
1. Read ./debates/{topic}_{context}.md
2. Edit your section for the current round: ### [{COLOR}] Opening, Rebuttal, or Synthesis
3. Structure: Position → Evidence → Implications
4. Cite sources (files, URLs) for every claim

## Constraints
- Read-only tools only (no code modifications)
- Stay on assigned perspective
""")
```
