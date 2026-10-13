---
allowed-tools: Bash(gh review *), Bash(gh pr *), Bash(gh api *), Bash(gh issue view *)
---

# PR Review

Interactive review of a PR: draft line comments, then submit a verdict through `gh review`.

## Workflow

1. Gather configuration with AskUserQuestion: focus areas (correctness, style, performance, security), severity threshold (blocking, high, all), scope (full, quick).
2. If the pre-loaded context is empty (cross-repo or no PR), fetch it:
   ```bash
   gh pr view {pr} --repo {owner}/{repo} --json title,body,files,commits,additions,deletions
   gh pr diff {pr} --repo {owner}/{repo}
   gh api repos/{owner}/{repo}/pulls/{pr} --jq '.head.sha'
   gh review comments {pr} -R {owner}/{repo} --mine --states=pending
   ```
3. Display existing pending drafts and offer to continue or discard them.
4. Read related issues: `gh issue view {issue} --repo {owner}/{repo} --json title,body`.
5. Detect the changed languages, then load the [code review roles](../../code/SKILL.md#review-roles), the [checklist](../../code/reference/checklist.md), and the parts of the listed `code.style` providers ([code slots](../../code/SKILL.md#slots)) material to those languages:
   ```bash
   gh pr view {pr} --repo {owner}/{repo} --json files --jq '.files[].path' | \
     sed 's/.*\.//' | sort | uniq -c | sort -rn
   ```
6. Compare against project style guides (STYLE.md, CLAUDE.md) and patterns from related issues.
7. For each candidate, present its code context and concern, then ask via AskUserQuestion with `multiSelect`; allow flagging or dismissing several findings at once:
   - type changes → "Is type widening intentional?"
   - error handling removed → "Was this error path obsolete?"
   - performance-sensitive code → "Acceptable trade-off?"
   - general → "Flag this?", "Severity level?"
8. Manage draft comments for confirmed findings:
   ```bash
   gh review add {pr} -R {owner}/{repo} -p {file_path} -l {line} -b "{comment_body}"
   gh review add {pr} -R {owner}/{repo} -p {file_path} -l {end_line} --start-line {start_line} -b "{comment_body}"  # multi-line
   gh review edit {pr} -R {owner}/{repo} -c {comment_id} -b "{updated_body}"
   gh review delete {pr} -R {owner}/{repo} -c {comment_id}
   ```
9. Ask via AskUserQuestion: submit now with a verdict (approve, request_changes, comment), or keep as draft.
   ```bash
   gh review submit {pr} -R {owner}/{repo} -v {approve|request_changes|comment} -b "{summary}"
   gh review discard {pr} -R {owner}/{repo}   # discard and start fresh
   ```

## gh-review Notes

- Use file line numbers, not diff positions.
- Comment IDs are GraphQL node IDs (e.g., `PRRC_kwDOABC123`); list them with `--ids`.
- Comment bodies support markdown and suggestion blocks.
- `gh review view` shows review threads hierarchically; see `gh review --help`.
