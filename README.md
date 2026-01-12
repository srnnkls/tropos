# tropos

*Spec → Delegate → Review → Repeat*

> *τρόπος* • manner, way, style; a turn, direction
>
> Pronunciation: /ˈtro.pos/
>
> the particular way in which something is done

## About

A Claude Code configuration for agentic development flows. Specs scaffold the work, git records the truth. Structure before code, verification before claims, delegation over heroics.

## Philosophy

- *Spec* — Validate requirements, create tracking documents
- *Delegate* — Fresh subagent per task with quality gates
- *Review* — Review completed work before continuing
- *Repeat* — Update spec, continue cycle, archive when done

Supporting principles:

- *Test-driven by default* — Red, green, refactor
- *Fresh context per task* — Subagents prevent pollution
- *Evidence over assertion* — Verify before claiming done
- *Parallelize when independent* — Dependency trees unlock concurrency
- *Sequential when dependent* — Respect the critical path

## Plugins

- *[skills](skills/)* — Spec pipeline, code quality, task execution
- *[commands](commands/)* — Shortcuts for common workflows
- *[agents](agents/)* — Implementer, reviewer, tester

## Usage

Add as a marketplace:

```bash
/plugin marketplace add srnnkls/tropos
/plugin install skills@tropos
/plugin install commands@tropos
/plugin install agents@tropos
```

Or reference from your own marketplace:

```json
{
  "name": "skills",
  "source": {"source": "github", "repo": "srnnkls/tropos", "path": "skills"}
}
```

## Auto-Update

```json
{
  "extraKnownMarketplaces": {
    "tropos": {
      "source": {"source": "github", "repo": "srnnkls/tropos"}
    }
  },
  "pluginMarketplaceAutoUpdate": {
    "tropos": true
  }
}
```
