# Code Review Playbook

Timeouts, parse failures, partial results, execution classes: [review harnesses](../../review/reference/harnesses.md). Reviewer selection and availability: [peer routing](../../peer/reference/routing.md).

## Target Detection

Flags override detection: `--scope` scope mode (batch review), `--rev` git rev/range, `--path` path, `--diff` staged/unstaged diff. Without a flag, take the first match:

1. Scope: `find ./scopes -maxdepth 2 -type d -name {arg}` matches one of `./scopes/{draft,active,done}/{arg}/`
2. Git rev: `git rev-parse --verify {arg}`
3. Git range: contains `..` or valid range syntax
4. Path: `test -e {arg}`
5. Diff: no argument; staged/unstaged changes

| Mode | Load |
|---|---|
| Scope | `scope.md`, `tasks.yaml`, `review.yaml`, `validation.yaml` |
| Git | `git show` or `git diff`, commit messages |
| Path | the files |
| Diff | `git diff --cached` or `git diff` |

| Case | Action |
|---|---|
| No argument, empty `git diff` | Check `git diff --cached`; if empty, list recently modified files, ask for a target |
| Path does not exist | Suggest the closest match, list the parent directory, ask the user to correct it |
| Binary files | Skip them, report "Skipped N binary files", review text files only |
| Diff over 2000 lines | Warn "Large diff detected (N lines)", suggest chunks or specific files, proceed only on user confirmation |

## Synthesis

[Review synthesis](../../review/reference/synthesis.md) owns merging (by failure mechanism; agreement is not validity) and gate aggregation.

## Output

Scope mode writes `./scopes/<state>/<scope>/review.yaml` (`<state>` ∈ `{draft, active, done}`), committed with the scope. Other modes write to the [review report paths](../../review/SKILL.md#report-paths).

Present the gate summary table, issues by severity, and for scopes, compliance and deferred issues. Recommend merge/commit when all gates pass; otherwise, fixing the issues first.
