---
name: peer
description: |
  External code-review harness (`peer` zsh tool): canonical model registry, idle-stall watchdog, and self-parallelising fan-out to codex/gemini. Use when dispatching external (non-Claude) reviewers from the review or implement pipelines — call `peer run`/`peer <harness>` instead of `codex exec`/`gcloud`+Vertex directly.
metadata:
  type: generic
---

# peer

`peer` ships with this repo at `skills/peer/peer` (a zsh script with a `#!/usr/bin/env zsh`
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
  after `--idle` seconds of **silence** (default 60s — a healthy run streams every few
  seconds), retries once, then skips. So a stall is caught in ~1 min, never a long hang.
- **gemini** — `pi` + the **`@ssweens/pi-vertex`** provider → Gemini on **Vertex AI**, a
  *fully agentic* reviewer (explores the diff with tools, like codex). `pi --mode json`
  streams events, so the same fifo + idle-watchdog applies; the report is the final
  assistant message, recovered from the stream. Auth is **ADC** (`gcloud auth
  application-default login`) — no API key. Defaults: model `gemini-3.5-flash`, project
  `code17-main`, location `global` (3.x flash is served by Vertex AI on the global
  endpoint, which gemini-cli's Code Assist backend can't reach). Override with
  `PEER_GEMINI_PROJECT` / `PEER_GEMINI_LOCATION`.

The **Claude** harness is an in-process subagent (`Task`), dispatchable only by the agent
itself; `peer` covers the external harnesses. Don't replace `peer` with a bare `timeout`.

## Canonical model registry

`peer`'s registry is the single source of truth for reviewer identity. Never hardcode
model strings in a dispatch; pass the harness/alias and let peer supply the model.

```
$ peer list
REVIEWER-ID            HARNESS MODEL                      ALIAS   RUN-BY-PEER
codex-gpt5.5           codex   gpt-5.5                    gpt     yes
gemini-3.5-flash       gemini  gemini-3.5-flash           gemini  yes
claude-opus            claude  opus                       opus    no (agent Task)
claude-sonnet          claude  sonnet                     sonnet  no (agent Task)
```

## `peer run` — fan out (primary interface for skills)

One call fans a prompt out to every configured external reviewer concurrently, each with
its own watchdog, writing one report file per reviewer.

```bash
peer run -d {outdir} --reviewers {ids-or-aliases} --effort {reasoning} "{review_prompt}"
```

- `-d {outdir}` (required): directory for per-reviewer reports (`{outdir}/{reviewer-id}.yaml`).
- `--reviewers` (optional): comma-separated ids (`codex-gpt5.5`) or aliases (`gpt,gemini`).
  Omit to use every peer-runnable reviewer. `claude-*` entries are skipped with a notice
  (dispatch those as `Task` from the agent).
- `--effort` (optional): `low|medium|high` for codex (gemini ignores it). Defaults per registry.
- `--idle {s}` / `--cap {s}` (optional): codex silence timeout (default 60) / hard cap (default 600).

**Output:** a TSV manifest on stdout, one row per reviewer:

```
codex-gpt5.5      ok       /tmp/rev/codex-gpt5.5.yaml
gemini-3.5-flash  ok       /tmp/rev/gemini-3.5-flash.yaml
```

Read each `ok` file for its `reviewer_report:` YAML; skip `stalled`/`error`/`auth` rows
(note them as partial results). **Exit:** `0` if ≥1 report produced · `1` if none · `2` usage.

## `peer <codex|gemini>` — single reviewer

For a single external reviewer (or non-fan-out callers):

```bash
peer codex  --effort high -o {outfile} "{prompt}"
peer gemini --model gemini-3.5-flash -o {outfile} "{prompt}"   # agentic; explores the repo itself
```

Both write the report to `{outfile}`. **Exit:** `0` report in `{outfile}` · `2` usage ·
`3` auth/availability (codex: `codex login`; gemini: `gcloud auth application-default login`
+ billed project) · `124` failed twice → skip this reviewer.

## Dispatch contract for skills

Per role, in one message: a Claude `Task` (required) **plus** one `peer run` for the
external harnesses. Then read the manifest + report files and synthesise.

```
Task(subagent_type="general", prompt={role_prompt})            # Claude — agent-native
Bash(run_in_background=true):                                  # codex + gemini — peer fans out
  peer run -d {role_outdir} --reviewers {externals} --effort {reasoning} "{role_prompt}"
```

Requirements: `mise run install-peer` (PATH); `codex login` for codex; for gemini —
`pi install npm:@ssweens/pi-vertex` + `gcloud auth application-default login` with access
to a billed Vertex project (default `code17-main`).
