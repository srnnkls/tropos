# Peer Routing

Canonical interpretation of the live peer registry and native/external dispatch. Callers select roles and persist configuration; this resource decides how a selected alias runs.

## Registry

`skills/peer/scripts/reviewers.yaml` is the sole source of route identity, harness, provider, model, alias, default effort, native capability, proxy capability, peer capability, and the default reviewer ensemble. Read entries through `peer list` and `peer get`; read the resolved default ensemble through `peer defaults reviewers`. Never infer behavior from an alias or hardcode model strings.

## Default reviewers

Unless a caller supplies an explicit reviewer configuration, use every entry from `peer defaults reviewers`. Its execution column is authoritative: `native` and `native-proxy` dispatch through the host subagent API; `peer` dispatches externally. An unavailable default route blocks its required execution class rather than changing mechanisms.

## Host routes

| Host | Native route | Generated in-harness route | External route |
|---|---|---|---|
| Claude Code | session inheritance or a `claude-*` route marked native | an active `claude-*` route marked proxy | a `peer-*` route |
| Codex | session inheritance or a `codex-*` route marked native | — | a `peer-*` route |

Claude Code treats native and proxy-served models as first-class role routes. The live registry identifies their model families and providers; availability comes from `peer route show` and `peer route check`, never from family assumptions.

Reject same-family loopback, unknown aliases, inactive generated definitions, and unsupported efforts. Never silently convert one execution mechanism into another.

A caller may explicitly require an execution class. Validate it against the `NATIVE`, `PROXY`, and `PEER` columns from `peer list`; persist the selected route ID so the mechanism remains explicit. Never substitute a sibling route when the selected mechanism is unavailable.

Route IDs encode the execution owner: `codex-*` runs through native Codex delegation, `claude-*` through Claude Code, and `peer-*` through the external harness. Aliases are command conveniences, not persisted route identity.

Registry `override_was` and `fanout_was` values are migration-only. They normalize old persisted Claude overrides and old external aliases in those contexts; new state stores the current route ID. An exact current route ID always keeps its encoded execution owner.

## Dispatch

- Codex native: delegate through the selected `codex-*` route, or inherit the session model and effort.
- Claude native: `Task(subagent_type="<role>", model="<alias>", prompt=...)`.
- Claude proxy route: after a successful route check, use `Task(subagent_type="<role>-<alias>[-<effort>]", prompt=...)` without a model argument.
- Peer route: use `peer -C <workdir> -d <outdir> --agent <role> --peers <peer-aliases> --effort <effort> --prompt-file <outdir>/prompt.md`.

Use one external call per mutating task so partial writes remain attributable. Review may fan out compatible external aliases once per role; start those fan-outs with all native role Tasks in the same assistant message.

## Route Commands

Run `peer route --help` for the current command surface. Use `show` to read resolved state and `check` immediately before directly naming a generated role.

`routing:` in the registry is the standing default. `.peer/routing` under a working root overrides it; `inherit` leaves a role on the session model. Route status, including stale generated definitions, is authoritative.

## Effort

Task has no effort argument. Native non-inherited effort is encoded in a generated definition:

```text
<role>-<effort>
<role>-<alias>-<effort>
```

The level must appear in registry `efforts:`. A peer route receives the same level through `--effort`; an inherited native route keeps the host session effort. One reviewer effort must be supported by every selected peer route.

A `<role>-<effort>` definition has no model, so a Claude-native model can combine with that level through `Task(model=...)`. Proxy aliases carry their model in `<role>-<alias>[-<effort>]` and therefore receive no model argument.

## Generated Definitions

`peer route sync` materializes ignored local definitions from each base role and reconciles obsolete generated files. `mise run install-peer` links the base roles into Claude's configured agent directory and syncs there. Edit only the base role or registry, then regenerate.

The routing hook applies a configured Claude-native alias through the Task model field and rewrites a configured proxy alias to its generated definition. It acts only on bare role dispatches when the selected route is reachable and current; an explicit model remains authoritative. Otherwise it leaves the role unchanged. Directly named generated roles still require `peer route check`.

Generated reviewers inherit the role tool list, not the external peer reviewer's sandbox profile. Route them only where a writable reviewer shell is acceptable.

## Reports

Create output directories through the [peer report-layout contract](../SKILL.md#report-layout--peer), save the complete materialized prompt as `prompt.md`, and treat manifest rows plus result filenames as authoritative provenance.
