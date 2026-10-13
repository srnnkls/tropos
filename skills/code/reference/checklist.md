# Code Review Checklist

Severity: [review severity contract](../../review/reference/report.md#issue-severity).

| Gate | Check |
|---|---|
| Correctness | Logic matches stated requirements; edge cases (null, empty, boundary) handled; errors handled or propagated, not swallowed; type safety maintained; no off-by-one errors |
| Style | Consistent naming; no comments restating the code; no commented-out code; project conventions followed |
| Performance | No N+1 queries; files and connections cleaned up |
| Security | No hardcoded secrets; input validated at boundaries; no SQL, command, or other injection; user-provided paths handled safely |
| Abstractions | [Abstraction admission](../../review/reference/finding-bar.md#abstraction-admission); no new dependency for what a few lines cover; no unused config, flags, or parameters |
| Architecture | No circular dependencies |
| Testing (if applicable) | Tests cover the change and its edge cases |
