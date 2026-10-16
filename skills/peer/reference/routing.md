# Peer Routing

## Registry

`skills/peer/scripts/reviewers.yaml` is the sole source of routes (ID, harness, provider, model, alias, default effort, native/proxy/peer capability) and the default reviewer ensemble. Read it through `peer list`, `peer get`, and `peer defaults reviewers`; never infer behavior from an alias or hardcode model strings.

## Default reviewers

Absent explicit reviewer configuration, use every `peer defaults reviewers` entry. Its execution column decides: `native` and `native-proxy` dispatch through the host subagent API, `peer` externally. An unavailable default route blocks its execution class.

## Host routes

| Host | Native route | Generated in-harness route | External route |
|---|---|---|---|
| Claude Code | session inheritance or a `claude-*` route marked native | an active `claude-*` route marked proxy | a `peer-*` route |
| Codex | session inheritance or a `codex-*` route marked native | — | a `peer-*` route |

- Read route availability and status (including staleness) from `peer route show` and `peer route check`, never from model family. Run `peer route check` immediately before naming a generated role directly.
- `.peer/routing` under the working root overrides registry `routing:`; `inherit` keeps the session model.
- Reject same-family loopback, unknown aliases, inactive generated definitions, and unsupported efforts. Never convert a mechanism or substitute a sibling route.
- Validate a caller-required execution class against `peer list` columns `NATIVE`, `PROXY`, `PEER`.
- Persist route IDs, never aliases; prefixes name the owner: `codex-*` Codex, `claude-*` Claude Code, `peer-*` external.
- `override_was`/`fanout_was` only normalize old persisted values; a current route ID keeps its owner.

## Dispatch

- Codex native: the selected `codex-*` route, or inherit session model and effort.
- Claude native: `Task(subagent_type="<role>", model="<alias>", prompt=<read pointer>)`.
- Claude proxy: after a successful route check, `Task(subagent_type="<role>-<alias>[-<effort>]", prompt=<read pointer>)` without a model argument.
- Peer: `peer -C <workdir> -d <outdir> --agent <role> --peers <peer-aliases> --effort <effort> --prompt-file <outdir>/prompt.md`.

One external call per mutating task. Review may fan out compatible external aliases once per role, in one assistant message with all native role Tasks. Create output directories through the [report-layout contract](../SKILL.md#report-layout--peer). Workflow dispatches write `prompt.md` and pass native routes a read pointer to it per [implement dispatch](../../implement/reference/subagent-workflow.md#dispatch).

## Effort

Native non-inherited effort needs a generated definition (Task takes no effort):

```text
<role>-<effort>
<role>-<alias>-<effort>
```

The level must be in registry `efforts:`; peer routes take `--effort`; inherited native routes keep the session effort; one reviewer effort must suit all selected peer routes. Combine `<role>-<effort>` with `Task(model=...)`; proxy definitions carry their model and take no model argument.

## Generated Definitions

Never edit generated definitions; edit base roles or registry, then run `peer route sync` from the deployed runner; it writes Claude's agent directory, pruning obsolete definitions.

The routing hook acts only on bare role dispatches with a reachable, current route: it sets a Claude-native alias as Task model or rewrites a proxy alias to its generated definition. An explicit model wins.

Generated reviewers have the role's tools, not the peer sandbox; use them only where a writable shell is acceptable.
