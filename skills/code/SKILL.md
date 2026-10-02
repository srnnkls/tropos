---
name: code
description: Code domain context for explicit implementation, review, and test workflows.
metadata:
  type: domain
henia:
  variables:
    context_commands:
      - label: Slot providers
        slots: code.style code.validation test.conventions review.criteria
      - label: Git status
        command: git status --short 2>/dev/null || true
      - label: Languages detected
        command: find . -maxdepth 3 -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.ts" -o -name "*.js" 2>/dev/null
  targets:
    claude:
      frontmatter:
        allowed-tools: Bash({{.resolve_slots}} *)
        argument-hint: '[operation] [target]'
    codex:
      openai:
        interface:
          display_name: Code workflows
          short_description: Route implementation, review, and test workflows
          default_prompt: Use $code to select an explicit code workflow.
---

<!-- Generated from skills/code/SKILL.md by henia build; edit the canonical source. -->

## {{if eq .preload_context "true"}}Pre-loaded Context{{else}}Runtime Context{{end}}

{{.context_instruction}}

{{range .context_commands}}{{.label}}:
{{if eq $.preload_context "true"}}!`{{if .slots}}{{$.resolve_slots}} {{.slots}}{{else}}{{.command}}{{end}}`{{else}}```bash
{{if .slots}}{{$.resolve_slots}} {{.slots}}{{else}}{{.command}}{{end}}
```{{end}}

{{end}}
# Code Domain

Compose generic workflows with code-specific Gestalt navigation, language guidance, and review lenses.

:::instruction{priority=high}
## Routes

| Argument | Action |
|---|---|
| `implement <target>` | Invoke `$implement` with `<target>` and code context |
| `review <target>` | Invoke `$review` with `<target>` and code review roles |
| `test <target>` | Invoke `$test` with `<target>` and local test conventions |
| Missing | Ask which explicit operation to run |

No operation is inferred from an ordinary task outside explicit skill invocation.
:::

## Slots

| Slot | Covers |
|---|---|
| `code.style` | Style guidance for Implementation Context and the Compliance role; providers scope it per language as `code.style.<language>` |
| `code.validation` | Native lint, typecheck, and build commands that make up directly affected native validation |

## Implementation Context

- Apply the repository-orientation contract in [AGENTS.md](../../instructions/AGENTS.md#tools-and-context).
- Use named `gestalt callers`, `callees`, or `refs` only when a changed symbol's immediate relationship is unresolved.
- Apply the listed `code.style` providers when language behavior, APIs, or unfamiliar style choices are material. Read each provider once and only the topic files needed by the change.
- Follow direct execution unless explicit `$implement` activated the strict delegated pipeline.

## Test Context

A `test.conventions` provider ([test slots](../test/SKILL.md#slots)) settles conventions first; otherwise use existing nearby tests. Load a language test guide only when those tests do not settle the pattern. The [test skill](../test/SKILL.md) owns count, time, attempt, tooling, and exploration ceilings.

## Review Roles

| Role | Gates | Canonical focus |
|---|---|---|
| General | Correctness, Security, Performance | [general.md](reference/roles/general.md) |
| Architecture | Architecture | [architecture.md](reference/roles/architecture.md) |
| Compliance | Style | [compliance.md](reference/roles/compliance.md) |

Prepare once:

- materialized target/diff;
- applicable requirements, including listed `review.criteria` providers ([review slots](../review/SKILL.md#slots));
- exact report schema;
- verbatim [finding bar](../review/reference/finding-bar.md);
- fresh materialized repository orientation;
- bounded Gestalt context;
- only material `code.style` provider excerpts.

For implementation-owned initial review, launch every role and configured reviewer in one assistant message. Standalone review launches selected roles the same way. Post-fix verification never uses this fan-out; [review synthesis](../review/reference/synthesis.md#46-fix-and-re-review-protocol) owns its single targeted reviewer. Resolve mechanisms through [peer routing](../peer/reference/routing.md); review-specific materialization and coverage live in [review harnesses](../review/reference/harnesses.md).

## Role Prompt Contract

Use the runtime materialization contract in [subagent-workflow.md](../implement/reference/subagent-workflow.md). Role files supply behavior; prompts supply shared evidence, assigned gates, the canonical report schema, and the verbatim finding bar.

Architecture uses materialized structural context first. Run `gestalt diff` for a code range or a named-symbol query for one unresolved blast-radius question. Do not run a fixed checklist of analyze, verbose propagation, rank, and caller enumeration.

Compliance loads only language guidance material to changed patterns. It does not audit every guideline file.

## Synthesis

Apply [review synthesis](../review/reference/synthesis.md); it owns disposition, grouping, user decisions, re-review, and stopping.

## References

- [reference/playbook.md](reference/playbook.md) — bounded edge-case handling
- [reference/checklist.md](reference/checklist.md) — gate checklist
- [review report](../review/reference/report.md) — YAML schemas
- [review finding bar](../review/reference/finding-bar.md) — admission and sufficiency
- [review synthesis](../review/reference/synthesis.md) — disposition and round limits
