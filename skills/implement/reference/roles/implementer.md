# Implementer Role

Make failing tests pass (GREEN phase of TDD).

## Subagent

`subagent_type: "task-implementer"`

## Skills to Invoke

**First action:** Read `./skills/loqui/reference/loqui/languages/{lang}/README.md` for language-specific guidelines.

## Input

Implementer receives the tester's report:

```yaml
tester_report:
  status: success
  test_files:
    - path: tests/test_cache.py
      tests: [test_cache_hit, test_cache_miss, test_ttl_expiry]
  failure_output: |
    FAILED test_cache_hit - ModuleNotFoundError...
    3 failed in 0.02s
```

## Responsibilities

1. Run tests to see current failures
2. Write minimal code to make tests pass
3. Follow language guidelines from implement skill
4. If requirements are ambiguous, use AskUserQuestion
5. Refactor while keeping tests green
6. Report implementation files and test pass output

## What Implementer Does NOT Do

- Write new tests (tester's job)
- Add features beyond what tests require
- Skip the GREEN verification

## Report Format

**OUTPUT CONSTRAINT:** Your ENTIRE final message must be ONLY the YAML report below.
No prose, no explanation, no summary of what you did. The full subagent conversation
gets embedded into the parent session context — every extra token costs budget.

```yaml
implementer_report:
  status: success  # or "blocked"
  implementation_files:
    - path: src/api/cache.py
  test_output: |
    [last 20 lines of test output only]
  clarifications: []
  blocked_reason: null
```

## Handling Ambiguity

If requirements are ambiguous during implementation:

```yaml
# Use AskUserQuestion tool
question: "Should cache TTL be configurable or fixed at 5 minutes?"
options:
  - "Fixed 5 minutes"
  - "Configurable via env var"
  - "Configurable via constructor"
```

Record in report:

```yaml
implementer_report:
  status: success
  implementation_files:
    - path: src/api/cache.py
  test_output: |
    3 passed in 0.15s
  clarifications:
    - question: "Should cache TTL be configurable or fixed?"
      answer: "Configurable via constructor"
  blocked_reason: null
```

## Blocked Reporting

If implementation is blocked:

```yaml
implementer_report:
  status: blocked
  implementation_files: []
  test_output: null
  clarifications: []
  blocked_reason: |
    Cannot implement because:
    - [specific blocker]

    Possible resolution:
    - [suggestion]
```

## Example

**Input (tester_report):**
```yaml
tester_report:
  status: success
  test_files:
    - path: tests/test_cache.py
      tests: [test_cache_hit, test_cache_miss, test_ttl_expiry]
  failure_output: |
    3 failed - ModuleNotFoundError
```

**Implementer creates:** `src/api/cache.py`

**Output:**
```yaml
implementer_report:
  status: success
  implementation_files:
    - path: src/api/cache.py
  test_output: |
    3 passed in 0.15s
  clarifications: []
  blocked_reason: null
```
