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
The owner declares a slot in `henia.slots` and states what it covers; a provider
names the slot in `henia.provides`; every skill that applies a slot preloads its
providers through `henia slots`, at runtime, over Henia's library: the
project's own skills, its skill packages and the global packages.
The [Project slots](instructions/AGENTS.md#project-slots) contract defines types,
priorities and shadowing; [Henia](https://github.com/srnnkls/henia/blob/main/docs/slots.md)
resolves them.

For example, `code` owns `code.style`, `implement` preloads its providers,
Loqui provides `code.style.go`, and a repository's own Go skill replaces it:

```text
$ henia slots --explain code.style.go
code.style.go
  code.style.go (keyed(list) of code.style, declared by …/henia/packages/global/tropos/skills/code/SKILL.md)
    selected house-go [project, normal from tier] .henia/skills/house-go/SKILL.md
    shadowed loqui [global, fallback from tier] …/henia/packages/global/tropos/skills/loqui/SKILL.md
      by house-go [project, normal from tier] for code.style.go, .henia/skills/house-go/SKILL.md
```

[COMPOSITION.md](COMPOSITION.md) lists every seam with its type, owner, the
skills that apply it and the providers Tropos ships. `scripts/composition`
generates it, and CI commits the result on every push to `main` that changes it.

A repository fills a seam with a skill in `.henia/skills`; it shadows the global
providers of that slot and its sub-slots, or sits beside them at `fallback`
priority:

```markdown
---
name: house-go
description: Go conventions for this repository.
henia:
  provides:
    code.style.go:
    review.criteria: {priority: fallback}
---
```

`henia slots --explain` shows every seam with its
declaration, its providers and which provider shadows which.

## Development

Henia compiles the canonical skills for Claude Code, Codex, Pi and OMP; Phora
deploys them and installs Loqui as a transitive dependency. See
[Henia and Phora](docs/henia-phora.md). Run `mise run test-artifacts` to prepare
this tree, compile every harness and check the results.
