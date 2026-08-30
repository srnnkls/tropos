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

The `loqui` reference is not bundled with tropos. Point `skills/loqui/reference/loqui` at a local [loqui](https://github.com/srnnkls/loqui) checkout to activate the `loqui` skill:

```bash
mise run loqui-link               # symlinks to a cache dir, cloning from github if missing
mise run loqui-link --path ./foo  # custom path (must exist)
mise run loqui-unlink             # remove the symlink
```

The default cache location is `$XDG_CACHE_HOME/tropos/loqui` if set, else `~/Library/Caches/tropos/loqui` on macOS, else `~/.cache/tropos/loqui`. The symlink path is gitignored.
