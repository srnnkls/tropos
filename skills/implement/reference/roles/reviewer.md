# Reviewer Role

Review one completed implementation batch through three independent lenses. All roles and configured reviewer routes launch in one assistant message.

## Roles

| Role | Gates | Inputs |
|---|---|---|
| General | Correctness, Security, Performance | Diff, requirements, focused validation |
| Architecture | Architecture | Diff, requirements, bounded Gestalt context |
| Compliance | Style | Diff, requirements, material Loqui excerpts |

A role reports only its gates. Agreement count is evidence, not validity.

## First Action

Every reviewer runs `gestalt map` as its first repository tool action. Architecture may then use `gestalt diff` or named `callers`/`callees`/`refs` queries when the changed structure leaves a concrete blast-radius question unresolved. No role has a fixed multi-command exploration floor.

## Shared Inputs

Prepare once before dispatch:

1. materialized batch diff;
2. applicable requirements and acceptance criteria;
3. exact reviewer YAML schema;
4. verbatim [finding bar](../../../review/reference/finding-bar.md);
5. bounded structural context;
6. language guidance material to the diff.

Commands and the workdir may supplement these inputs for shell-capable reviewers. They never replace the materialized content.

## Routing and Concurrency

Use the immutable batch snapshot from [configuration.md](../configuration.md). Do not reload configuration per role.

In one assistant message:

- dispatch every configured native General reviewer;
- dispatch every configured native Architecture reviewer;
- dispatch every configured native Compliance reviewer;
- start one external peer fan-out for each role that has external aliases.

`codex-native`, Claude-native Tasks, `ROUTABLE=yes` generated definitions, effort variants, and external aliases follow the canonical configuration rules. Never infer the route from an alias name or send a host-native token through peer.

Wait once. A role clears when every execution class configured in the snapshot has at least one successful report. An absent class is irrelevant.

## Finding Contract

A finding must identify a reachable trigger and wrong outcome against the materialized change. Review the state machine in one pass. Do not report:

- preferences, speculative hardening, or adjacent cleanup;
- thin coverage where representative falsifiers cover the guarantee;
- another permutation of a failure mechanism already considered;
- telemetry, provenance, or observability precision without a production requirement or observed failure;
- style or architecture concerns outside the assigned role.

Return only the requested YAML schema.

## Synthesis and Fixes

Synthesize through [review synthesis](../../../review/reference/synthesis.md). Batch admitted findings by mechanism. `needs decision:` goes to the user.

After a fix, dispatch only the lens that failed and only against the changed mechanism. Two fix rounds per subject are the ceiling. A further round requires a verified failure mode in a component no prior round examined.

## Final Review

A one-batch scope does not receive another reviewer wave. A multi-batch scope receives one concurrent holistic integration prompt per configured reviewer, focused on cross-batch interactions, acceptance criteria, deferred findings, and final validation evidence. Do not repeat the three role cascade or reopen cleared batch-local findings.
