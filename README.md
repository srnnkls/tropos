# tropos

*Scope → Delegate → Review → Repeat*

> *τρόπος* • manner, way, style; a turn, direction
>
> Pronunciation: /ˈtro.pos/
>
> the particular way in which something is done

## About

A cross-harness configuration for agentic development. Ordinary work stays direct; explicit workflows add scoped delegation and evidence gates when requested. Git records the truth.

## Philosophy

- *Direct by default* — Use the shortest native path for ordinary work
- *Explicit assurance* — Scope, delegated TDD, and review activate only when invoked
- *Fresh context per task* — Subagents prevent pollution
- *Evidence over assertion* — Verify before claiming done
- *Parallel when independent* — Dependency trees unlock concurrency

## Components

- *[instructions/AGENTS.md](instructions/AGENTS.md)* — Concise global contract shared across harnesses
- *[skills](skills/)* — Progressively disclosed workflows and domain policy
- *[agents](agents/)* — Implementer, reviewer, and tester boundaries

## Composition

Skills expose seams as typed slots that other skills fill without editing them.
The owner declares a slot and states what it covers; a provider names the slot
in `metadata.provides`; every skill that applies a slot preloads its providers
through `henia slots`, at runtime, over the harness's skills and the project's.
The [Project slots](instructions/AGENTS.md#project-slots) contract defines types,
priorities and shadowing; [Henia](https://github.com/srnnkls/henia/blob/main/docs/slots.md)
resolves them.

| Seam | Owner | Applied by | Default providers |
|---|---|---|---|
| `code.style` | [code](skills/code/SKILL.md#slots) | code, implement, continue, loop | [loqui](skills/loqui/SKILL.md) per language |
| `code.validation` | [code](skills/code/SKILL.md#slots) | code, implement, continue, loop | — |
| `test.conventions` | [test](skills/test/SKILL.md#slots) | test, code, implement, continue, loop | — |
| `review.criteria` | [review](skills/review/SKILL.md#slots) | review, code, implement, continue, loop, tfcp, tfcprr, pr | — |
| `git.branching` | [git](skills/git/SKILL.md#slots) | git, implement, continue, loop | — |
| `git.commits` | [git](skills/git/SKILL.md#slots) | git, tfcp, tfcprr | — |
| `scope.templates` | [scope](skills/scope/SKILL.md#slots) | scope | — |
| `issue.template` | [issue](skills/issue/SKILL.md#slots) | issue | — |

A repository fills a seam with a project skill; it shadows the global providers
of that slot and its sub-slots, or sits beside them at `fallback` priority:

```markdown
---
name: house-go
description: Go conventions for this repository.
metadata:
  provides: "code.style.go review.criteria@fallback"
---
```

`henia slots --global ~/.claude/skills --explain` shows every seam with its
declaration, its providers and which provider shadows which.

## Development

Henia compiles the canonical skills for Claude Code, Codex, Pi and OMP; Phora
deploys them and installs Loqui as a transitive dependency. See
[Henia and Phora](docs/henia-phora.md). Run `mise run test-artifacts` to prepare
this tree, compile every harness and check the results.
