# Tester Report

Canonical tester handoff for explicit test and implementation workflows.

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

`success` requires valid bounded RED evidence under the test skill. `gap` names the missing requirement, tool, or decision and never authorizes broader test machinery.
