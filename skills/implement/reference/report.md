# Subagent Report Schemas

Every subagent returns only the requested YAML. Limit command output to the last 20 relevant lines and gap/block reasons to five lines.

## Tester

```yaml
tester_report:
  status: success | gap
  test_files:
    - path: tests/test_feature.py
      tests: [test_requested_behavior]
  test_command: "focused command"
  red_kind: assertion | compiler | typechecker
  rejected_wrong_implementation: "plausible wrong behavior the test rejects"
  failure_output: |
    [last 20 relevant lines]
  gap_reason: null
```

`success` requires valid bounded RED evidence. `gap` names the missing requirement, tool, or decision; it never authorizes broader test machinery.

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

## Reviewer

Use the exact schema materialized by the review operation. Every issue includes:

```yaml
- severity: critical | high | medium
  gate: correctness | style | performance | security | architecture
  location: path/to/file:line
  trigger: "reachable input or state"
  wrong_outcome: "incorrect result"
  suggestion: "smallest shared-root fix or needs decision: constraint"
```

A report may contain no issues. Agreement count does not alter validity.

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
