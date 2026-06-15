---
name: peer
description: |
  External code-review harness (`peer` zsh function): canonical model registry, idle-stall watchdog, and self-parallelising fan-out to codex/agy. Use when dispatching external (non-Claude) reviewers from the review or implement pipelines — call `peer run`/`peer <harness>` instead of `codex exec`/`agy` directly.
metadata:
  type: generic
---

# peer

`peer` ships with this repo at `skills/peer/peer` (a zsh script with a `#!/usr/bin/env zsh`
shebang, so it runs from any shell). It is the **only** sanctioned way to invoke codex or
agy from the skills — never call `codex exec` / `agy` directly.

**Install:** `mise run install-peer` symlinks it onto PATH at `~/.local/bin/peer`
(idempotent; re-run after pulls). `~/.local/bin` is on PATH in interactive and
non-interactive shells, so skill `Bash` shell-outs resolve `peer`. A future compiled
(go) binary will build to the same path with the same CLI — nothing downstream changes.

## Why peer exists (don't replace it with `timeout`)

The shared ChatGPT/Codex backend (and agy) intermittently **stalls mid-request**: the
client sits at ~0 CPU emitting nothing, and `codex exec` does **not** self-abort — it
blocks indefinitely. A plain `timeout` waits out its whole cap on every stall. `peer`
watches the live output stream and kills a run after `--idle` seconds of **silence**
(default 60s; a healthy run streams an event every few seconds), so a stall is caught in
~1 min. It then retries once and, on a second stall, skips — the pipeline never hangs.

## Canonical model registry

`peer`'s registry is the single source of truth for reviewer identity. Never hardcode
model strings in a dispatch; pass the harness and let peer supply the model.

```
$ peer list
REVIEWER-ID            HARNESS MODEL                      ALIAS   RUN-BY-PEER
codex-gpt5.5           codex   gpt-5.5                    gpt     yes
agy-gemini-3.5-flash   agy     Gemini 3.5 Flash (High)    gemini  yes
claude-opus            claude  opus                       opus    no (agent Task)
claude-sonnet          claude  sonnet                     sonnet  no (agent Task)
```

The Claude harness is an in-process subagent (`Task`) and can only be dispatched by the
agent. `peer` covers the external harnesses; `peer list` shows all four for reference.

## `peer run` — fan out (primary interface for skills)

One call fans a prompt out to every configured external reviewer concurrently, each with
its own idle-stall watchdog, writing one report file per reviewer.

```bash
peer run -d {outdir} --reviewers {ids-or-aliases} --effort {reasoning} "{review_prompt}"
```

- `-d {outdir}` (required): directory for per-reviewer reports (`{outdir}/{reviewer-id}.yaml`).
- `--reviewers` (optional): comma-separated ids (`codex-gpt5.5`) or aliases (`gpt,gemini`).
  Omit to use every peer-runnable reviewer. `claude-*` entries are skipped with a notice
  (dispatch those as `Task` from the agent).
- `--effort` (optional): `low|medium|high` for codex (agy ignores it). Defaults per registry.
- `--idle {s}` / `--cap {s}` (optional): silence timeout (default 60) / hard backstop (default 600).

**Output:** a TSV manifest on stdout, one row per reviewer:

```
codex-gpt5.5            ok       /tmp/rev/codex-gpt5.5.yaml
agy-gemini-3.5-flash    stalled  /tmp/rev/agy-gemini-3.5-flash.yaml
```

Read each `ok` file for its `reviewer_report:` YAML; skip `stalled`/`error`/`auth` rows
(note them as partial results). **Exit:** `0` if ≥1 report produced · `1` if none · `2` usage.

## `peer <codex|agy>` — single reviewer

For a single external reviewer (or non-fan-out callers):

```bash
peer codex --effort high -o {outfile} "{prompt}"
peer agy   --model "Gemini 3.5 Flash (High)" -o {outfile} "{prompt}"
```

codex writes its report to `{outfile}` via `-o`; for agy, peer captures stdout to `{outfile}`.
**Exit:** `0` report in `{outfile}` · `2` usage · `3` auth/missing (run `codex login` / install) ·
`124` stalled twice → skip this reviewer.

## Dispatch contract for skills

Per role, in one message: a Claude `Task` (required) **plus** one `peer run` for the
external harnesses. Then read the manifest + report files and synthesise.

```
Task(subagent_type="general", prompt={role_prompt})            # Claude — agent-native
Bash(run_in_background=true):                                   # codex + agy — peer fans out
  peer run -d {role_outdir} --reviewers {externals} --effort {reasoning} "{role_prompt}"
```

Requires `codex login` for the codex harness, and `mise run install-peer` to put `peer`
on PATH (see Install above).
