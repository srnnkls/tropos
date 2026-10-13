# Implementation Reports

Handoffs for [implement](../SKILL.md). Return only the requested YAML; limit command output to the last 20 relevant lines.

## Implementer

```yaml
implementer_report:
  status: success | blocked
  implementation_files: [src/feature.py]
  ownership:
    - definition: src/feature.py:parse_window
      candidates: [src/util/time.py:parse_span, "dateutil.parser.parse"]
      decision: reuse | extend | new
      owner: src/feature.py:parse_window
  test_command: "focused command"
  test_output: |
    [last 20 relevant lines]
  blocked_reason: null
```

`ownership` lists each definition the change adds that owns behavior, with candidates from `gestalt map`, `refs`, and `callers` and from installed dependencies' APIs as `path:symbol` or package API; `[]` when none. `success` requires verified GREEN evidence. `blocked` names the conflicting requirement, invalid RED evidence, unavailable dependency, or public-surface decision.

## Fix

```yaml
fix_report:
  status: success | blocked
  fixes_applied:
    - issue: "admitted finding"
      fix: "shared mechanism changed"
  test_output: |
    [last 20 relevant lines]
  blocked_reason: null
```

Fix reports never include residual, deferred, or `needs decision:` work.
