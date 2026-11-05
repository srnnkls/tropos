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
  providers_applied:
    - slot: test.conventions
      applied: "rule or section applied to these tests"
  gap_reason: null
```

`success` requires the [canonical RED gate](../SKILL.md#red). `providers_applied` names, per slot provider read for the task, the rules the tests applied; `[]` when the skills list none for it. `gap` names the missing requirement, tool, or decision and never authorizes broader test machinery.
