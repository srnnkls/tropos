# Code Review Playbook

---

## Timeout Handling

### External Harness (Codex / Gemini) Stall

`peer` owns the idle-stall watchdog, retry-once, and skip. Read `peer`'s manifest status per
reviewer. Standalone review may warn "[Reviewer] stalled, skipped. Partial results." and
synthesize when another report succeeded. An implementation-owned gate instead pauses and
deliberately redispatches until every execution class actually configured for the role has a
successful report. Exit codes and rationale: [peer skill](../../peer/SKILL.md).

### Claude Subagent Timeout

**Symptom:** Task tool returns timeout error

**Response:**
1. Standalone review: if another reviewer succeeded, use its result and disclose partial coverage
2. Implementation-owned gate: pause unless every configured execution class has a success
3. If all failed: report failure and suggest retry
4. Never proceed with zero reviews

---

## Parse Failures

### YAML Not Found in Output

**Symptom:** Reviewer output lacks `reviewer_report:` block

**Response:**
1. Search for partial YAML (may be malformed)
2. If found: attempt parse, report issues
3. If not found: mark reviewer as failed
4. Continue with available data

### Malformed YAML

**Symptom:** YAML parsing error

**Response:**
1. Report which reviewer's output failed to parse
2. Include raw output snippet for debugging
3. Continue with parseable reviewer(s)

---

## Reviewer Selection Edge Cases

### No Reviewers Selected

**Symptom:** User deselects all options

**Response:**
1. Codex host with delegation → default to `codex-native`; Claude host with Task → default to `opus`
2. If neither native mechanism exists, ask for an available external reviewer rather than inventing one

### Codex Not Available

**Symptom:** `codex` command not found, or `codex login` not completed (401 / `refresh_token_invalidated`)

**Response:**
1. Standalone review: warn "Codex not available, using Claude only" and disclose reduced coverage
2. Implementation-owned gate: pause only when an external class was configured; all-native gates
   do not require Codex CLI

---

## Input Type Detection

### Disambiguation Flags

Flags override auto-detection:

| Flag | Forces |
|------|--------|
| `--scope` | Scope mode (batch review) |
| `--rev` | Git rev/range mode |
| `--path` | Path mode |
| `--diff` | Diff mode (staged/unstaged) |

### Auto-Detection Priority (no flag)

1. **Scope** - `find ./scopes -maxdepth 2 -type d -name {arg}` matches one of `./scopes/{draft,active,done}/{arg}/`
2. **Git rev** - `git rev-parse --verify {arg}`
3. **Git range** - contains `..` or valid range syntax
4. **Path** - `test -e {arg}`
5. **Diff** - no argument, use staged/unstaged

### Ambiguous Input

**Symptom:** Input could match multiple types (e.g., "main" is both a branch and could be a scope)

**Response:**
1. If flag provided → use flag, skip detection
2. Otherwise, follow priority order (scope → git → path)

---

## Review Storage

### Scope Mode

**Location:** `./scopes/<state>/<scope>/review.yaml` (`<state>` ∈ `{draft, active, done}`)
**Persistence:** Committed with scope, part of audit trail

### Other Modes (Ephemeral)

**Location:** `~/.claude/reviews/<generated-name>.md`
**Persistence:** Ephemeral, like Claude's internal plans

**Naming:**
```
review-<sha>-<timestamp>.md           # Git rev
review-<from>..<to>-<timestamp>.md    # Git range
review-<path-slug>-<timestamp>.md     # Path
review-staged-<timestamp>.md          # Staged changes
```

**Cleanup:** User manages `~/.claude/reviews/` manually

---

## Code Target Edge Cases

### No Argument, No Changes

**Symptom:** No path provided, `git diff` returns empty

**Response:**
1. Check `git diff --cached` for staged changes
2. If still empty: list recently modified files
3. Ask user to specify target

### Invalid Path

**Symptom:** Provided path doesn't exist

**Response:**
1. Check for typos (suggest closest match)
2. List files in parent directory
3. Ask user to correct

### Binary Files

**Symptom:** Target includes binary files

**Response:**
1. Skip binary files
2. Note: "Skipped N binary files"
3. Review text files only

### Large Diff

**Symptom:** Diff exceeds reasonable size (> 2000 lines)

**Response:**
1. Warn: "Large diff detected (N lines)"
2. Suggest reviewing in chunks or specific files
3. Proceed if user confirms

---

## Conflicting Reviews

### Reviewers Disagree on Gate

**Symptom:** Claude passes, an external reviewer (codex/gemini) fails (or vice versa)

**Response:**
1. Gate status = FAIL (conservative)
2. In summary table, show which failed
3. Include both perspectives in issues

### Reviewers Find Same Issue Differently

**Symptom:** Similar description, different wording

**Response:**
1. Deduplicate by location + semantic similarity
2. Combine into single issue
3. Mark `found_by: [both]` for higher confidence

---

## Empty Results

### Reviewer Returns No Issues

**Symptom:** `issues: []` in report

**Response:**
1. Valid result (code may be solid)
2. Check if gates still passed
3. Report as clean review

### Reviewer Returns Only Strengths

**Symptom:** No issues, only strengths listed

**Response:**
1. Treat as passing review
2. Include strengths in synthesis
3. Proceed to recommendation

---

## Decision Tree

```
Start
  │
  ├─ Detect input type
  │   ├─ Scope exists? → Scope mode (batch review)
  │   ├─ Valid git rev? → Git rev mode
  │   ├─ Contains '..'? → Git range mode
  │   ├─ Path exists? → Path mode
  │   └─ No argument? → Diff mode (staged/unstaged)
  │
  ├─ Load review context
  │   ├─ Scope → Read scope.md, tasks.yaml, review.yaml, validation.yaml
  │   ├─ Git → git show/diff, commit messages
  │   ├─ Path → Read files
  │   └─ Diff → git diff --cached or git diff
  │
  ├─ Select reviewers
  │   ├─ Scope → Use validation.yaml config (no prompt)
  │   └─ Other → Prompt user with AskUserQuestion
  │
  ├─ Dispatch reviewers (parallel)
  │   ├─ All succeed → Synthesize
  │   ├─ Some fail → Use available, note partial
  │   └─ All fail → Report failure, suggest retry
  │
  ├─ Parse results
  │   ├─ YAML valid → Continue
  │   └─ YAML invalid → Attempt recovery, note issues
  │
  ├─ Synthesize
  │   ├─ Deduplicate issues
  │   ├─ Aggregate gates
  │   └─ Prioritize by severity
  │
  ├─ Write review output
  │   ├─ Scope → ./scopes/<state>/<scope>/review.yaml
  │   └─ Other → ~/.claude/reviews/<name>.md (ephemeral)
  │
  ├─ Present results
  │   ├─ Gate summary table
  │   ├─ Issues by severity
  │   └─ Scope: scope compliance + deferred issues
  │
  ├─ Recommend action
  │   ├─ All pass → Ready to merge/commit
  │   └─ Issues → Address before proceeding
  │
  └─ End
```
