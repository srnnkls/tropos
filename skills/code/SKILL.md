---
name: code
description: Code domain context for explicit implementation, review, and test workflows.
metadata:
  type: domain
henia:
  slots:
    code.style: keyed(list(path))
    code.conformance:
    code.validation: keyed(list(command))
    code.orientation:
  provides:
    code.conformance: {section: conformance}
  variables:
    context_commands:
      - label: Git status
        command: git status --short 2>/dev/null || true
      - label: Languages detected
        command: find . -maxdepth 3 -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.ts" -o -name "*.js" 2>/dev/null
  targets:
    claude:
      frontmatter:
        argument-hint: '[operation] [target]'
    codex:
      openai:
        interface:
          display_name: Code workflows
          short_description: Route implementation, review, and test workflows
          default_prompt: Use $code to select an explicit code workflow.
---

:::::head{context slots="code.orientation code.style code.conformance code.validation test.conventions test.approach implement.approach review.criteria review.general review.architecture review.tests review.abstractions review.detectors"}


# Code Domain

Code orientation, language guidance, and review roles for explicit workflows.

:slot[code.orientation]{.inline}

::::instruction{priority=high}
:::routes
| Argument | Action |
|---|---|
| `implement <target>` | Invoke `$implement` with `<target>` and code context |
| `review <target>` | Invoke `$review` with `<target>` and code review roles |
| `test <target>` | Invoke `$test` with `<target>` and local test conventions |
| Missing | Ask which explicit operation to run |

No operation is inferred from an ordinary task outside explicit skill invocation.
:::

::::

:::::

## Slots

| Slot | Covers |
|---|---|
| `code.style` | Style guidance for Implementation Context and the Compliance role, per language as `code.style.<language>` |
| `code.conformance` | Style and architecture validation before writing source, per language as `code.conformance.<language>`; replaces [Conformance](#conformance) |
| `code.orientation` | Repository orientation and structural queries: overview, callers, callees, references, definition-level diff, symbol history |
| `code.validation` | Native lint, typecheck, and build commands for directly affected native validation, one per language as `code.validation.<language>`, run as is |

## Implementation Context

- Orient per [AGENTS.md](../../instructions/AGENTS.md#tools-and-context). Query callers, callees, or references only for a changed symbol whose immediate relationship is unresolved.
- Before writing source, apply the `code.conformance` providers. Read each `code.style` provider once and only the topic files the change needs.
- Execute directly unless explicit `$implement` activated the strict delegated pipeline.

## Conformance

Before writing source in a language:

1. Apply its `code.style.<language>` providers and, inside a scope, the scope's Conventions and Invariants.
2. Without a `code.style.<language>` provider, apply the loqui guide of the most similar language (listed by `henia show loqui --head`), translated into the target language's idioms, and name the guide used. The loqui principles (`henia show 'loqui#principles'`) hold for every language.
3. Mirror the nearest existing code for what the guides leave open.
4. When guides, existing code, and the task conflict or leave a style or architecture choice open, ask the user before writing; a delegated tester or implementer returns `gap` or `blocked` naming the open choice instead.

## Test Context

Conventions: a `test.conventions` provider ([test slots](../test/SKILL.md#slots)), else nearby tests; load a language test guide only when neither settles the pattern. The [test skill](../test/SKILL.md) owns count, time, attempt, tooling, and exploration ceilings.

## Review Roles

| Role | Gates | Canonical focus |
|---|---|---|
| General | Correctness, Security, Performance | [general.md](reference/roles/general.md) |
| Architecture | Architecture | [architecture.md](reference/roles/architecture.md) |
| Compliance | Style | [compliance.md](reference/roles/compliance.md) |
| Abstractions | Abstractions | [abstractions.md](reference/roles/abstractions.md) |

Write each role prompt per [review dispatch prompt](../review/reference/harnesses.md#dispatch-prompt) and dispatch per [concurrent dispatch](../review/reference/harnesses.md#concurrent-dispatch); role files supply behavior. [Review synthesis](../review/reference/synthesis.md) owns disposition, grouping, user decisions, targeted re-review, and stopping.

:::references
- [reference/playbook.md](reference/playbook.md) — bounded edge-case handling
- [reference/checklist.md](reference/checklist.md) — gate checklist
- [review report](../review/reference/report.md) — YAML schemas
- [review finding bar](../review/reference/finding-bar.md) — admission and sufficiency
- [review synthesis](../review/reference/synthesis.md) — disposition and round limits
:::
