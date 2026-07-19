# Implementation Agent Configuration

Implementation routing is live configuration, separate from the scope-review settings in
`validation.yaml.review_config`.

## Scope Configuration

Persist scope-backed routing at `./scopes/<state>/<scope-name>/config.yaml`:

```yaml
version: 1
epoch:
  id: <generated-at-top-level-implement>
  started_at: <ISO_TIMESTAMP>
  updated_at: <ISO_TIMESTAMP>
routing:
  tester:
    agent: codex-native
    effort: inherit
  implementer:
    agent: codex-native
    effort: inherit
  reviewer:
    agents: [codex-native]
    effort: inherit
```

- A new top-level `/implement` execution creates a new epoch ID and timestamps.
- `/implement config <scope>` changes routing within the current epoch; preserve `id` and
  `started_at`, and refresh `updated_at`. Resolve `<scope>` by path or unique scope name; ask for
  the target only when it is missing or ambiguous. If no config exists, create an epoch.
- `/continue` and `/loop` reuse the current epoch and read this file before every dispatch.
- Direct tasks use the same resolved structure in memory, generate an ephemeral epoch ID for
  report paths, and do not create repository-level configuration.

## Setup and Overrides

Pre-parse `--config '<assignments>'` before route detection. Assignments are comma-separated;
reviewer sets use `+`:

```text
# Claude-host example
--config 'implementer=gpt,implementer_effort=high,reviewer=opus+gpt+gemini'
```

Allowed keys are `tester`, `tester_effort`, `implementer`, `implementer_effort`, `reviewer`,
and `reviewer_effort`. Merge partial assignments in this order, last source winning:

1. Host-aware built-in defaults:
   - When running under Codex with native subagent/delegation available: tester `codex-native`,
     implementer `codex-native`, reviewer `codex-native`; all efforts `inherit`.
   - On a Claude host with native Task available: tester `opus`, implementer `opus`, reviewer
     `opus+gpt+gemini`; tester/implementer efforts `inherit`, reviewer effort `high` (applies only
     to the peer reviewers; native `opus` inherits).
   - If neither Codex delegation nor Claude native Task is available, require explicit routing;
     do not invent a native default.
2. Current scope `config.yaml`, if present.
3. Inline `--config` assignments.

Supplying `--config` accepts the merged result without prompting. Without it, run interactive
setup for all three routes, showing the current/default values as the recommended selections.
`/implement config <scope>` follows the same rule: interactive without `--config`, non-interactive
with it. A legacy scope resumed by `/continue` or `/loop` prompts once only when `config.yaml` is
missing, then persists the selection.

Validate before writing or dispatching:

- `codex-native` is a reserved persisted token. It means dispatch through Codex's native
  subagent/delegation interface, inheriting the current session model and reasoning. Never pass
  this token to a peer dispatch or translate it to an explicit model. It may appear in `peer list`
  with `native=true` for discovery/validation, but the orchestrator always dispatches it natively.
- Native explicit aliases `opus` and `sonnet` are Claude-host-native Task routes. They are valid
  only when the current host exposes that Task mechanism.
- Resolve external aliases and supported effort values against `peer list`/the peer contract.
- `opus-cli` and `sonnet-cli`, when present in `peer list`, are external Claude CLI routes through
  peer and are valid for tester, implementer, and reviewer. The Codex-host default nevertheless
  remains all `codex-native`.
- Validate `opus-cli`/`sonnet-cli` effort against the Claude CLI subset
  `low|medium|high|xhigh|max`. For a fan-out containing multiple external aliases, the configured
  effort must be supported by every selected peer.
- `inherit` is required for singular host-native routes (`codex-native`, `opus`, or `sonnet`) and
  for all-native reviewer sets. If a reviewer set contains any external alias, `reviewer_effort`
  must be a peer-supported explicit effort; every host-native member still inherits and ignores
  that value.
- Persist effort for every route. It is a peer dispatch setting only; host-native Codex delegation
  and Claude Task have no separate effort channel and always inherit the session.
- Tester and implementer each select exactly one agent.
- Reviewer selects one or more agents; all-native, all-external, and mixed sets are valid.
- Reject unknown keys, aliases, empty values, duplicate assignments, and malformed reviewer sets.

Normalize partial overrides before validation:

- Changing singular `tester` or `implementer` to any host-native alias (`codex-native`, `opus`, or
  `sonnet`) without its `*_effort` sets effort to `inherit`.
- Changing a singular route from host-native to external while inherited effort remains resets to
  that peer's supported default effort, or asks for one when no safe default exists.
- Changing reviewer to an all-native set without `reviewer_effort` sets `inherit`; any reviewer set
  containing an external alias requires/resets to a peer-supported explicit effort.

Apply this host-routing matrix during setup, validation, and resume:

| Current host | GPT-family role | Claude-family role |
|---|---|---|
| Codex | `codex-native` native delegation (inherit session) | external `opus-cli`/`sonnet-cli` via peer |
| Claude | external `gpt`/other Codex alias via peer | native `opus`/`sonnet` Task |

Enforce same-host-family native routing using live registry metadata:

- Under Codex, reject `opus`/`sonnet` (suggest `opus-cli`/`sonnet-cli`) **and** reject every
  peer-runnable GPT/Codex-family alias whose registry harness/family is Codex (for example `gpt`,
  `terra`, or `luna`); direct that family to `codex-native`.
- Under Claude, reject `codex-native` (suggest a registered GPT/Codex peer alias) **and** reject
  every peer-runnable Claude-family alias whose registry harness/family is Claude (including
  `opus-cli`/`sonnet-cli`); direct that family to native `opus`/`sonnet`.
- Allow cross-family routes and unrelated peer families when their role capabilities permit.

Stop and ask the user to edit the live config; never silently convert or substitute. Apply these
rules equally to interactive setup, inline `--config`, `/implement config`, and resume validation.
Setup menus label/filter each choice as `native`, `via peer`, or `unavailable on this host` using
the registry family/harness rather than only hardcoded aliases.

The legacy `/implement --reviewers <comma-list>` form may be accepted as a reviewer-only override.
When accepted, it behaves as supplied inline configuration and therefore skips setup prompts; new
examples and persisted configuration use `--config`.

## Live Dispatch

Reload scope `config.yaml` immediately before Phase A, Phase A.5, Phase B, every Phase C role,
every fix dispatch, and final review. A saved change affects the next dispatch, never work already
running.

- Codex inherited route: native Codex subagent/delegation with the matching tester, implementer, or
  reviewer role prompt; omit model and reasoning overrides so the current session settings inherit.
- Explicit Claude-native route: `Task(subagent_type="<role>", model="<alias>", prompt=...)`.
- External route: first write the complete prompt to `<outdir>/prompt.md`, then run
  `peer -C <workdir> -d <outdir> --agent <role> --peers <aliases> --effort <effort>
  --prompt-file <outdir>/prompt.md`.

Never attempt to apply persisted effort to either host-native route. In a mixed reviewer set,
record that native entries used `inherit` and pass the configured reviewer effort only to peer.
- For external tester/implementer routes, make one singular peer call per task. For reviewer
  routes, convert the configured `+`-separated input to peer's comma-separated alias list and fan
  all configured external aliases through one peer call per review role.

Write implementation peer reports beneath
`.peer/<scope-or-direct>/<epoch>/<batch>/<stage>/`, adding task or review-role subdirectories when
multiple dispatches would otherwise collide.

Keep each materialized prompt as `prompt.md` inside its report directory (including
`.peer/direct/<epoch>/...` for direct tasks). Always use `--prompt-file`; never pass an
implementation pipeline prompt positionally, because embedded diffs/schemas may exceed argv limits.

Reviewer failures follow the review gate's partial-result policy. Require at least one successful
report from every execution class actually configured for that gate: native when any native alias
(`codex-native`, `opus`, or `sonnet`) is configured, and external when any `RUN-BY-PEER=yes` alias
is configured.
Do not require an absent class. Tester or implementer peer failure is mutating: preserve partial
edits, capture `git status --short` and the relevant `git diff`, mark the phase incomplete, and
pause for deliberate redispatch or `/continue`. Never auto-retry, roll back, or advance after a
mutating peer failure.

For every **scope-backed** native or external mutating dispatch, persist the stage-level recovery
marker described in [checkpoint-format.md](checkpoint-format.md) immediately before launch and
update it immediately after success or failure. Use the assigned `.peer` report directory for both
routes; peer writes external reports there, while the orchestrator stores a native report there
before clearing the marker. Direct tasks create no checkpoint: keep equivalent markers/evidence in
memory and store their artifacts beneath `.peer/direct/<epoch>/`.
