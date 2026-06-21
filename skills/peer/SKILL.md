---
name: peer
description: |
  External code-review harness (`peer` bash tool): canonical model registry, idle-stall watchdog, and self-parallelising fan-out to codex/gemini. Use when dispatching external (non-Claude) reviewers from the review or implement pipelines — call `peer`/`peer <harness>` instead of `codex exec`/`gcloud`+Vertex directly.
metadata:
  type: generic
---

# peer

`peer` ships with this repo at `skills/peer/scripts/peer` (a bash script with a `#!/usr/bin/env bash`
shebang, so it runs from any shell). It is the **only** sanctioned way to invoke the
external review harnesses from the skills — never call `codex exec` / the Vertex API directly.

**Install:** `mise run install-peer` symlinks it onto PATH at `~/.local/bin/peer`
(idempotent; re-run after pulls). `~/.local/bin` is on PATH in interactive and
non-interactive shells, so skill `Bash` shell-outs resolve `peer`. A future compiled
(go) binary will build to the same path with the same CLI — nothing downstream changes.

## Harnesses

- **codex** — OpenAI Codex CLI; an *agentic* reviewer that explores the diff with tools.
  The shared ChatGPT/Codex backend intermittently **stalls mid-request**: the client sits
  at ~0 CPU emitting nothing, and `codex exec` does **not** self-abort. A plain `timeout`
  waits out its whole cap on every stall; `peer` instead watches the live stream and kills
  after `--idle` seconds of **silence** (default 120s — a healthy agentic run at high
  reasoning effort legitimately goes quiet for 60-90s during a long tool/reasoning step,
  so a tighter idle false-kills it; a true stall is unbounded silence the `--cap` still
  catches), retries once, then skips. So a stall is caught in ~2 min, never a long hang.
- **pi** — the `pi` CLI + the **`@ssweens/pi-vertex`** provider → the gemini model on
  **Vertex AI**, a *fully agentic* reviewer (explores the diff with tools, like codex).
  (The harness is `pi`, the binary peer execs; the gemini model comes from the registry.) `pi --mode json`
  streams events, so the same fifo + idle-watchdog applies; the report is the final
  assistant message, recovered from the stream. Auth is **ADC** (`gcloud auth
  application-default login`) — no API key. Defaults: model !`peer get model gemini` — project
  `code17-main`, location `global` (3.x flash is served by Vertex AI on the global
  endpoint, which gemini-cli's Code Assist backend can't reach). Override with
  `PEER_GEMINI_PROJECT` / `PEER_GEMINI_LOCATION`.

The **Claude** harness is an in-process subagent (`Task`), dispatchable only by the agent
itself; `peer` covers the external harnesses. Don't replace `peer` with a bare `timeout`.

## Canonical model registry

`peer`'s registry is the single source of truth for reviewer identity. Never hardcode
model strings in a dispatch; pass the harness/alias and let peer supply the model. The
table below is injected live from `peer list` at skill-load — it cannot drift:

```!
peer list
```

## `peer` — fan out (primary interface for skills)

One call fans a prompt out to every configured external reviewer concurrently, each with
its own watchdog, writing one report file per reviewer.

```bash
peer -d {outdir} --reviewers {ids-or-aliases} --effort {reasoning} "{review_prompt}"
```

Fan-out is `peer`'s default action — no subcommand needed. (`peer run -d …` still works as
a back-compat alias for the same thing.)

- `-d {outdir}` (required): directory for per-reviewer reports (`{outdir}/{reviewer-id}.yaml`).
  Callers don't invent this — the review pipeline pins a git-ignored `.reviews/<slug>/`
  per run (see the review skill's **Report Output Directory**); `issue` pins `.issues/<number>-reviews/`.
- `--reviewers` (optional): comma-separated reviewer-ids — e.g. !`peer get id gpt` — or aliases (`gpt,gemini`).
  Omit to use every peer-runnable reviewer. `claude-*` entries are skipped with a notice
  (dispatch those as `Task` from the agent).
- `--effort` (optional): `low|medium|high` for codex (gemini ignores it). Defaults per registry.
- `--idle {s}` / `--cap {s}` (optional): silence timeout / hard cap (default 600). Idle
  auto-scales as `base + 1s per 500 prompt chars`; base is harness-specific — codex 120s,
  pi 180s (gemini-on-Vertex's legitimate mid-generation silence runs longer). An explicit
  `--idle` overrides the auto-scale for every reviewer.

**Output:** a TSV manifest on stdout, one row per reviewer:

```
{reviewer-id}  ok       {outdir}/{reviewer-id}.yaml
{reviewer-id}  stalled  {outdir}/{reviewer-id}.yaml
```

Read each `ok` file for its `reviewer_report:` YAML; skip `stalled`/`error`/`auth` rows
(note them as partial results). **Exit:** `0` if ≥1 report produced · `1` if none · `2` usage.

## `peer <codex|pi>` — single reviewer

For a single external reviewer (or non-fan-out callers). The harness names the CLI peer
execs (`codex`, `pi`) — not the model:

```bash
peer codex --effort high -o {outfile} "{prompt}"
peer pi -o {outfile} "{prompt}"   # gemini model supplied by the registry — never pass --model
```

Both write the report to `{outfile}`. **Exit:** `0` report in `{outfile}` · `2` usage ·
`3` auth/availability (codex: `codex login`; pi: `gcloud auth application-default login`
+ billed project) · `124` failed twice → skip this reviewer.

## Dispatch contract for skills

Per role, in one message: a Claude `Task` (required) **plus** one `peer` for the
external harnesses. Then read the manifest + report files and synthesise.

```
Task(subagent_type="general", prompt={role_prompt})            # Claude — agent-native
Bash(run_in_background=true):                                  # codex + gemini — peer fans out
  peer -d {role_outdir} --reviewers {externals} --effort {reasoning} "{role_prompt}"
```

Requirements: `mise run install-peer` (PATH); `codex login` for codex; for gemini —
`pi install npm:@ssweens/pi-vertex` + `gcloud auth application-default login` with access
to a billed Vertex project (default `code17-main`).
