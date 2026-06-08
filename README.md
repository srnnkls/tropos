# tropos

*Scope → Delegate → Review → Repeat*

> *τρόπος* • manner, way, style; a turn, direction
>
> Pronunciation: /ˈtro.pos/
>
> the particular way in which something is done

## About

A Claude Code configuration for agentic development flows. Scopes scaffold the work, git records the truth. Structure before code, verification before claims, delegation over heroics.

## Philosophy

- *Scope* — Research, validate requirements, create tracking documents
- *Delegate* — Fresh subagent per task with quality gates
- *Review* — Review completed work before continuing
- *Repeat* — Update scope, continue cycle, mark done

Supporting principles:

- *Test-driven by default* — Red, green, refactor
- *Fresh context per task* — Subagents prevent pollution
- *Evidence over assertion* — Verify before claiming done
- *Parallelize when independent* — Dependency trees unlock concurrency
- *Sequential when dependent* — Respect the critical path

## Plugins

- *[skills](skills/)* — Scope pipeline, code quality, task execution
- *[commands](commands/)* — Shortcuts for common workflows
- *[agents](agents/)* — Implementer, reviewer, tester

## Development

The `loqui` reference is not bundled with tropos. Point `skills/loqui/reference/loqui` at a local [loqui](https://github.com/srnnkls/loqui) checkout to activate the `loqui` skill:

```bash
mise run loqui-link               # symlinks to a cache dir, cloning from github if missing
mise run loqui-link --path ./foo  # custom path (must exist)
mise run loqui-unlink             # remove the symlink
```

The default cache location is `$XDG_CACHE_HOME/tropos/loqui` if set, else `~/Library/Caches/tropos/loqui` on macOS, else `~/.cache/tropos/loqui`. The symlink path is gitignored.
