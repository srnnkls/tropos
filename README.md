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

## Development

The [Henia → Phora migration](docs/henia-phora-prototype.md) compiles all 25
canonical skills for Claude Code, Codex, Pi and OMP, deploys immutable packages,
and installs Loqui as a transitive Phora dependency. Run `mise run prototype:sync`
and `mise run prototype:test` for deployment and lifecycle smoke tests.

The Loqui pin comes from the committed HEAD of `TROPOS_LOQUI_SOURCE` (default
`~/projects/loqui`). Phora installs its published guides beneath each deployed
`loqui` skill. No reference symlink is needed in canonical sources.
