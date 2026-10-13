# SDD Pre-Implementation Gates

Apply all gates to Initiatives only.

| Gate | Checklist |
|---|---|
| Simplicity | Minimal projects/components; no future-proofing or speculative features; complexity justified by requirements |
| Anti-Abstraction | Framework/tools used directly (no wrapper layers); single representation of core concepts; no "just in case" abstractions |
| Integration-First | API contracts defined (if applicable); integration points identified in scope.md; contract tests planned (if applicable) |

Track results in `validation.yaml`:

```yaml
gates:
  simplicity:
    status: pass|fail|n/a
    reason: "[explanation if failed or n/a]"
  anti_abstraction:
    status: pass|fail|n/a
    reason: "[explanation]"
  integration_first:
    status: pass|fail|n/a
    reason: "[explanation]"
```

Task-dispatch reads `validation.yaml`. If `issue_type` is Initiative and any gate is `fail`, block dispatch, report the failed gates, and have the user resolve them via [clarify](../../clarify/SKILL.md), a manual `validation.yaml` edit with justification, or reclassifying `issue_type` if the scope was misclassified. Otherwise proceed.
