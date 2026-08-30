# Peer Routing

Canonical interpretation of the live peer registry and native/external dispatch. Callers select roles and persist configuration; this resource decides how a selected alias runs.

## Registry

`skills/peer/scripts/reviewers.yaml` is the sole source of peer identity, harness, provider, model, alias, default effort, native status, and proxy availability. Read it through `peer list` and `peer get`; never infer behavior from an alias or hardcode model strings.

## Host Compatibility

| Host | Native route | Compatible cross-family route |
|---|---|---|
| Codex | `codex-native` delegation with inherited session settings | registered external peer |
| Claude | native `opus`/`sonnet` Task | `ROUTABLE=yes` generated Task; otherwise registered external peer |

Reject same-family loopback, unknown aliases, inactive generated definitions, and unsupported efforts. Never silently convert one execution mechanism into another.

A caller may explicitly require an execution class. In that case, validate the class against live metadata: a compatible cross-family entry with `RUN-BY-PEER=yes` may run externally even when it is also `ROUTABLE=yes`. Persist or state that class constraint; it is an intentional selection, never fallback from an inactive native route.

`codex-native` is a persisted delegation token, never a peer alias. `opus` and `sonnet` are Claude-native aliases; external Claude CLI routes use distinct registry aliases such as `opus-peer` and `sonnet-peer`.

## Dispatch

- Codex native: use the host's native delegation and inherit session model/effort.
- Claude native: `Task(subagent_type="<role>", model="<alias>", prompt=...)`.
- Routable proxy alias: by default, after a successful route check, use `Task(subagent_type="<role>-<alias>[-<effort>]", prompt=...)` without a model argument. An explicit external-class constraint uses the external form instead.
- External alias: use `peer -C <workdir> -d <outdir> --agent <role> --peers <aliases> --effort <effort> --prompt-file <outdir>/prompt.md`.

Use one external call per mutating task so partial writes remain attributable. Review may fan out compatible external aliases once per role; start those fan-outs with all native role Tasks in the same assistant message.

## Route Commands

```bash
peer route sync
peer route show [-C DIR]
peer route check <role>=<alias>[@<effort>] [...]
peer route set <role>=<alias> [-C DIR]
peer route clear [-C DIR]
```

`routing:` in the registry is the standing default. `.peer/routing` under a working root overrides it. `inherit` leaves a role on the session model.

`show` reports the resolved peer and `active` or `inactive: <reason>`. Read status, not the peer name. Directly naming a generated definition bypasses the routing hook, so every such selection must pass `peer route check`; batch all known assignments into one call.

## Effort

Task has no effort argument. Native non-inherited effort is encoded in a generated definition:

```text
<role>-<effort>
<role>-<alias>-<effort>
```

The level must appear in registry `efforts:`. A peer route receives the same level through `--effort`; `codex-native` accepts only `inherit`. One reviewer effort must be supported by every selected external peer.

A `<role>-<effort>` definition has no model, so a Claude-native model can combine with that level through `Task(model=...)`. Proxy aliases carry their model in `<role>-<alias>[-<effort>]` and therefore receive no model argument.

## Generated Definitions

`peer route sync` materializes ignored local definitions from each base role and reconciles obsolete generated files. `mise run install-peer` links the base roles into Claude's configured agent directory and syncs there. Edit only the base role or registry, then regenerate.

The routing hook rewrites bare role dispatches only when the selected proxy is configured, reachable, and backed by a generated definition. Otherwise it leaves the native role unchanged. Directly named generated roles still require `peer route check`.

Generated reviewers inherit the role tool list, not the external peer reviewer's sandbox profile. Route them only where a writable reviewer shell is acceptable.

## Reports

Create output directories through the [peer report-layout contract](../SKILL.md#report-layout--peer), save the complete materialized prompt as `prompt.md`, and treat manifest rows plus result filenames as authoritative provenance.
