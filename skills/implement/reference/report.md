# Implementation Reports

Canonical implementer and fix handoffs for explicit [implement](../SKILL.md). Return only the requested YAML and limit command output to the last 20 relevant lines.

## Implementer

```yaml
implementer_report:
  status: success | blocked
  implementation_files: [src/feature.py]
  test_command: "focused command"
  test_output: |
    [last 20 relevant lines]
  blocked_reason: null
```

`success` requires verified GREEN evidence. `blocked` names the conflicting requirement, invalid RED evidence, unavailable dependency, or public-surface decision.

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
