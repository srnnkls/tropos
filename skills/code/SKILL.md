---
name: code
description: Code domain context for explicit implementation, review, and test workflows.
argument-hint: "[operation] [target]"
metadata:
  type: domain
---

## Pre-loaded Context

Git status:
!`git status --short 2>/dev/null || true`

Languages detected:
!`find . -maxdepth 3 -name "*.py" -o -name "*.go" -o -name "*.rs" -o -name "*.ts" -o -name "*.js" 2>/dev/null`

# Code Domain

Compose generic workflows with code-specific Gestalt navigation, language guidance, and review lenses.

## Routes

| Argument | Action |
|---|---|
| `implement <target>` | `Skill(implement, <target>)` with code context |
| `review <target>` | `Skill(review, <target>)` with code review roles |
| `test <target>` | `Skill(test, <target>)` with local test conventions |
| Missing | Ask which explicit operation to run |

No operation is inferred from an ordinary task outside explicit skill invocation.

## Implementation Context

- Run `gestalt map` first.
- Use named `gestalt callers`, `callees`, or `refs` only when a changed symbol's immediate relationship is unresolved.
- Load the Loqui README once per language when language behavior, APIs, or unfamiliar style choices are material. Read only topic files needed by the change.
- Follow direct execution unless explicit `/implement` activated the strict delegated pipeline.

## Test Context

Use existing nearby tests for conventions. Load a language test guide only when those tests do not settle the pattern. The count, time, attempt, tooling, and exploration ceilings in `skills/test/SKILL.md` are mandatory.

## Review Roles

| Role | Gates | Canonical focus |
|---|---|---|
| General | Correctness, Security, Performance | [general.md](reference/roles/general.md) |
| Architecture | Architecture | [architecture.md](reference/roles/architecture.md) |
| Compliance | Style | [compliance.md](reference/roles/compliance.md) |

Prepare once:

- materialized target/diff;
- applicable requirements;
- exact report schema;
- verbatim [finding bar](../review/reference/finding-bar.md);
- bounded Gestalt context;
- only material Loqui excerpts.

For implementation-owned review, launch every role and all configured native/external routes in one assistant message. Standalone review launches the selected roles the same way. Routing, `ROUTABLE=yes` definitions, effort variants, peer fan-out, and execution-class gates live in [review harnesses](../review/reference/harnesses.md) and the [peer skill](../peer/SKILL.md).

## Role Prompt Contract

Every prompt contains the shared inputs and says:

- review only the assigned gates;
- run `gestalt map` first;
- a finding requires a reachable trigger and wrong outcome;
- enumerate a changed state machine once and group defects by mechanism;
- representative falsifiers are sufficient;
- return only the exact YAML schema.

Architecture uses materialized structural context first. Run `gestalt diff` for a code range or a named-symbol query for one unresolved blast-radius question. Do not run a fixed checklist of analyze, verbose propagation, rank, and caller enumeration.

Compliance loads only language guidance material to changed patterns. It does not audit every guideline file.

## Synthesis

Use [review synthesis](../review/reference/synthesis.md). Agreement count is evidence, not validity. Batch accepted findings by mechanism, defer valid medium issues, surface `needs decision:`, and re-review only a failed lens after fixes.

## References

- [reference/playbook.md](reference/playbook.md) — bounded edge-case handling
- [reference/checklist.md](reference/checklist.md) — gate checklist
- [review report](../review/reference/report.md) — YAML schemas
- [review finding bar](../review/reference/finding-bar.md) — admission and sufficiency
- [review synthesis](../review/reference/synthesis.md) — disposition and round limits
