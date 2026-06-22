# PR Review Operation

## Pre-loaded PR Context

PR metadata:
!`gh pr view $0 --json title,body,additions,deletions,files,commits 2>/dev/null`

PR diff:
!`gh pr diff $0 2>/dev/null`

Pending draft comments:
!`gh review comments $0 --mine --states=pending 2>/dev/null`

# PR Review Skill

Interactive GitHub PR review workflow: fetch PR, iterate findings with clarification, manage draft comments, submit when ready.

Delegates to `code` domain for review methodology and language guidelines.

Requires: `gh-review` extension (`gh extension install srnnkls/gh-review`)

---

## Workflow

### 1. Configure Review

Use **AskUserQuestion** to gather configuration (see `code review` for details):
- Focus areas: correctness, style, performance, security
- Severity threshold: blocking, high, all
- Scope: full, quick

### 2. Fetch PR Context

If pre-loaded context above is populated, skip fetching. Otherwise (cross-repo or no argument):

```bash
gh pr view {pr} --repo {owner}/{repo} --json title,body,files,commits,additions,deletions
gh pr diff {pr} --repo {owner}/{repo}
gh api repos/{owner}/{repo}/pulls/{pr} --jq '.head.sha'  # Get commit SHA
```

### 3. Check Existing Drafts

If pre-loaded draft comments above are populated, skip fetching. Otherwise:

```bash
gh review comments {pr} -R {owner}/{repo} --mine --states=pending
```

If drafts exist, display them and offer to continue or discard.

### 4. Check Related Issues

```bash
gh issue view {issue} --repo {owner}/{repo} --json title,body
```

### 5. Delegate to Review Skills

Detect language from file extensions:
```bash
gh pr view {pr} --repo {owner}/{repo} --json files --jq '.files[].path' | \
  sed 's/.*\.//' | sort | uniq -c | sort -rn
```

Load:
- `code` domain — review process and checklist
- `~/.claude/skills/loqui/reference/loqui/languages/{language}/*` — language-specific resources based on file extensions

### 6. Reference Style Guides

Compare against:
- Project style guides (STYLE.md, CLAUDE.md)
- Established patterns from related issues

### 7. Iterate Findings with Clarification

For each potential issue identified:

1. **Present finding** - Show code context and concern
2. **Ask context-aware questions** via `AskUserQuestion` with `multiSelect`:
   - Type changes → "Is type widening intentional?"
   - Error handling removed → "Was this error path obsolete?"
   - Performance-sensitive code → "Acceptable trade-off?"
   - General → "Flag this?", "Severity level?"
3. **Batch decisions** - Allow selecting multiple findings to flag/dismiss

### 8. Create/Update Draft Comments

For each confirmed finding, add to pending review:

```bash
gh review add {pr} -R {owner}/{repo} -p {file_path} -l {line} -b "{comment_body}"
```

For multi-line comments:
```bash
gh review add {pr} -R {owner}/{repo} -p {file_path} -l {end_line} --start-line {start_line} -b "{comment_body}"
```

To update an existing draft:
```bash
gh review edit {pr} -R {owner}/{repo} -c {comment_id} -b "{updated_body}"
```

To remove a draft:
```bash
gh review delete {pr} -R {owner}/{repo} -c {comment_id}
```

### 9. Submit or Keep Draft

Use **AskUserQuestion** to determine action:

**Options:**
- **Submit now** → Choose verdict (approve, request_changes, comment)
- **Keep as draft** → Leave pending for later continuation

To submit:
```bash
gh review submit {pr} -R {owner}/{repo} -v {approve|request_changes|comment} -b "{summary}"
```

To discard and start fresh:
```bash
gh review discard {pr} -R {owner}/{repo}
```

---

## Key Gotchas

- Line numbers: Use actual file line numbers (not diff positions) with `gh review`
- Comment IDs: GraphQL node IDs (e.g., `PRRC_kwDOABC123`) - get with `--ids` flag
- Comment format: Supports markdown, suggestion blocks with triple backticks

---

## gh-review Commands

| Command | Description |
|---------|-------------|
| `comments` | List PR comments with filtering (`--mine`, `--states`) |
| `view` | View review threads hierarchically |
| `add` | Add draft comment to pending review |
| `edit` | Update existing draft comment |
| `delete` | Remove draft comment |
| `submit` | Submit review with verdict |
| `discard` | Delete pending review |

---

## Related Skills

- `code`: Review methodology (focus, severity, checklist) and language guidelines
- `loqui`: Language guidelines

---

## Reference

- `gh review --help`
- `gh pr review --help`
