# Code Review Playbook

Edge case handling and decision trees for review scenarios.

---

## Timeout Handling

### OpenCode Timeout (> 5 minutes)

**Symptom:** `timeout` command exits with code 124

**Response:**
1. Continue with completed reviews
2. Add warning to output:
   ```
   Note: [Reviewer] timed out after 5 minutes.
   Results are partial. Consider re-running with fewer reviewers.
   ```
3. Proceed with synthesis using available data

### Claude Subagent Timeout

**Symptom:** Task tool returns timeout error

**Response:**
1. If other reviewers succeeded: use their results
2. If all failed: report failure, suggest retry
3. Never proceed with zero reviews

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
1. Default to claude-opus only
2. Warn: "No reviewers selected, defaulting to Claude. Consider external reviewer for fresh perspective."

### OpenCode Not Available

**Symptom:** `opencode` command not found

**Response:**
1. Warn: "OpenCode not installed, using Claude only"
2. Proceed with Claude reviewer
3. Suggest: `go install github.com/opencode-ai/opencode@latest`

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

**Symptom:** Claude passes, OpenCode fails (or vice versa)

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
  ├─ Code target found?
  │   ├─ No → Check git diff, list files, ask user
  │   └─ Yes → Continue
  │
  ├─ Reviewers selected?
  │   ├─ None → Default to Claude, warn
  │   └─ Some → Continue
  │
  ├─ Dispatch reviewers
  │   │
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
  ├─ Any gates failed?
  │   ├─ Yes → Recommend addressing issues
  │   └─ No → Recommend merge/commit
  │
  └─ End
```
