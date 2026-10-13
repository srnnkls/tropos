# Skill Best Practices

## Structure

- References one level deep from SKILL.md, split by domain or condition; table of contents above 100 lines.
- One term per concept.
- Current behavior only; deprecated patterns in a collapsed legacy section, never behind dates.

## Workflows

- Complex operations: numbered steps plus a copyable progress checklist.
- Fragile steps: validate, fix, re-validate; proceed only on pass.
- Batch or destructive changes: plan file, script-validate it, apply only on pass, verify.
- Explicit branches at decision points.
- Mark each output template exact or adjustable; give input/output pairs for style-dependent output.

## Evaluation

1. Record the agent's failures on target tasks without the skill.
2. Write three scenarios for them: query, files, expected behaviors.
3. Write minimal passing instructions; iterate with a fresh agent on real tasks.

Fix what the fresh agent's navigation shows: unexpected path → restructure; missed connection → explicit link; repeated reads of one reference → move it into SKILL.md; ignored file → cut or signal it.

## Scripts

- Handle errors in the script; justify or derive every constant.
- Document each script's purpose and invocation, and required packages with install commands.
- MCP tools as `ServerName:tool_name`; forward slashes in paths.
