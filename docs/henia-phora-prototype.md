# Henia → Phora prototype

Four canonical skills compile and deploy into worktree-local `.claude` and `.codex`. Phora verifies all 94 installed files. Repeated deployment preserved their checksums; disposable probes confirmed resource pruning, drift detection and compiler-failure containment.

Branch: `prototype/henia-phora`, based on checkpoint `f768f1f`. Worktree: `/Users/srnnkls/projects/tropos/.worktrees/henia-phora`. The prototype is isolated from the original checkout. No global installation was performed.

## Run

From the worktree root:

```sh
python3 prototype/henia/deploy.py
```

Requirements: installed `henia`, Rust `phora`, Git, and Python 3.11+. The [Henia configuration](../henia.toml) selects Claude/XML and Codex/directives. [Stage configuration](../prototype/henia/stage/phora.toml) owns the source subset; [deployment configuration](../prototype/henia/deploy/phora.toml) owns destination paths and local Phora cache/state.

`code`, `implement`, `review` and `peer` are rewritten in place. Their unchanged Markdown-link dependency closure adds `test`, three role contracts and `instructions/AGENTS.md`. Resources retain their source paths and executable modes. Generated copies carry `GENERATED.md`; the canonical skills also emit source/generator comments.

Claude retains command preloading and its original frontmatter restrictions. Codex receives explicit shell instructions and four `agents/openai.yaml` interface sidecars. The context instruction is defined once in `henia.toml`; workflow policies remain in their existing canonical resources.

## Feature and lint findings

The complete command inventories, measured results, minimal reproductions and unverified branches are recorded separately:

- [Compiler feature results](henia-build-results.md): all nine profiles × three formats, templates, mappings, directives, references, resources and configuration behavior.
- [Linter results](henia-lint-results.md): 69 CLI cases, all 13 built-in rule IDs, all seven custom selectors, and real cached Model2Vec inference without downloads.

Henia's Bash, Zsh, Fish and PowerShell completion generators also completed successfully. `bash -n` and `zsh -n` accepted their generated scripts; Fish/PowerShell execution was not exercised. Evidence: `.henia/evidence/completion.*`.

These are CLI feature exercises, not a claim that every internal branch or generated harness workflow was executed.

## Deployment evidence

Raw evidence is under ignored `.henia/evidence/`; generated snapshots and Phora state are also confined to `.henia/`.

| Check | Result | Evidence |
|---|---|---|
| Checkpoint validation | Workflow contracts and all five peer suites passed after replacing a stale duplicate route matrix with registry-derived expectations | `f768f1f`; original check log `/tmp/tropos-checkpoint-validation.log` |
| Canonical workflow validation | Existing `mise run test-workflow-contracts` passed after the rewrites | `workflow-contracts-final.log` |
| Build/deploy/verify | Five skills per target; 94 files total; `phora verify`: `all verified` | `deployment-final.log` |
| Artifact fidelity | `diff -r --exclude=.git` found no content differences for either harness; both deployed peer runners are executable | `deployed-final.sha256`; installed files |
| Repeat deployment | Every installed checksum matched after another complete run | `deployment-final-repeat.log`, `deployment-final-repeat-checksums.log` |
| Pure resource removal | Disposable `prune-probe.txt` disappeared from both targets after its source was removed | `deployment-fixture-initial.log`, `deployment-fixture-prune.log` |
| Compiler failure | Invalid `{{if}}` failed the build hook; every prior fixture deployment checksum remained unchanged | `deployment-fixture-failure.log`, `deployment-fixture-failure-checksums.log` |
| Drift | Edited fixture `GENERATED.md` made `phora verify` exit 1 with `content mismatch` | `deployment-fixture-drift.log` |
| Ownership | A snapshot missing its generator marker was rejected before any Git command ran; the real owned deployment still verified with unchanged hashes | `deployment-fixture-unowned.log`, `deployment-owned-final.log`, `deployment-owned-final-checksums.log` |

Fixture failure is intentional and remains isolated under `.henia/evidence/deployment-fixture`. It does not affect the installed prototype.

## Integration gaps and workarounds

### The documented Phora invocation cannot run

Henia's `docs/phora.md` uses `phora --config … sync`. Installed Phora 0.1.2 rejects `--config`; its CLI loads only `./phora.toml`. The example configs also omit mandatory `version = 1`, which fails parsing when used as `phora.toml`.

This prototype uses two working directories with versioned configs. Source references: `/Users/srnnkls/projects/henia/docs/phora.md:41`, `/Users/srnnkls/projects/phora/src/cli/mod.rs:807`.

### Phora local copy sources require Git snapshots

A local `path` is a Git remote in copy mode. Pointing it at this worktree staged committed `f768f1f` content, ignoring the canonical rewrites. The stage lock recorded that commit; its `code/SKILL.md` still contained the old top-level `argument-hint`. Strict Codex compilation then failed on that unsupported metadata. Evidence: `deployment-second.log`.

A separate native probe, `cd .henia/evidence/phora-nongit && phora sync`, exited 1: `clone bare plain: Could not verify that …/artifacts url is a valid git directory`. Its input and config remain in that evidence directory.

Plain Henia output directories are therefore not sufficient copy-mode inputs. The wrapper creates generated local Git snapshots of the selected dirty sources and each compiled harness output. Snapshot commits stay under `.henia/`; they do not commit or publish the prototype branch. Unchanged snapshot trees retain their previous commits.

`phora update --fast-forward` refreshes each source pin and handles removals. Ordinary `sync` alone would retain locked content. Link mode was not substituted: this prototype verifies copied deployment contents through Phora's integrity model.

### Build hooks require two phases

Phora resolves source snapshots before its build hook runs. Compilation is the staging phase's global `post_sync` hook; deployment runs in a separate process only after that hook succeeds. Building in the deployment phase's `pre_sync` cannot refresh its already-selected snapshot. Pure-removal handling is verified above.

### A fresh build is required for reliable pruning

The wrapper builds into a new directory and publishes it only after both harnesses compile and pass non-strict lint. Previous owned snapshots are archived rather than removed. Phora then deploys the fresh Git snapshots. Compiler-specific stale-output behavior is documented in the compiler results.

This is a local prototype, not an atomic two-target deployment system. Compiler failure containment is verified; process death during the build-directory rename and partial Phora deployment are not covered by a rollback mechanism. Archives accumulate; no automatic retention policy is installed. Concurrent deployment invocations are not supported.

### Strict compilation succeeds; strict lint does not

The deployed Claude output has 29 lint warnings; Codex has 26. Both have zero lint errors. Raw diagnostics are `.henia/build/claude-lint.json` and `codex-lint.json`; paths inside them refer to the temporary compilation directory before publication.

Warnings include compatibility noise documented in the lint report, generated context-paragraph repetition, and genuine references to skills outside this subset. The wrapper retains every diagnostic and gates on errors; it does not disable a rule or claim strict-lint cleanliness.

### Harness variables are strings

`preload_context = true` failed with `load config: toml: cannot assign boolean to a true` (`deployment-first.log`). The working config uses strings and explicit template equality against `"true"`. A nonempty `"false"` must not be used as a Go-template boolean condition.

### Configuration isolation is incomplete

Henia consults `~/.config/henia`, independently of `XDG_CONFIG_HOME`. No such user config directory existed during the deployment run. HOME-overridden checks were blocked by the worktree command guard; the working pipeline leaves HOME unchanged. Future user-global Henia settings can affect builds. Phora cache and registry isolation use explicit `[paths]` settings and were verified locally.

## Runtime limits

The deployed Markdown-link closure is present, but the subset is not a standalone Tropos installation. Routes mentioning `continue`, `scope`, `gestalt`, `loop`, `tfcp`, `tfcprr` and Loqui still depend on existing repository/global facilities. Supporting Markdown is copied verbatim; its Claude-style invocations are not rewritten for Codex. The peer runner is bundled, not installed onto PATH. Codex permission enforcement and native agent registration are not supplied by copying Claude role-contract files.

No generated skill was invoked against an external model. An offline, network-denied Codex app-server initialization recognized the project `.codex` directory and reported that skills load even while project settings are untrusted. The `skills/list` response did not complete before stdin closed; subsequent paced probes were blocked by the command guard. Full Codex enumeration and live Claude skill discovery remain unverified. Evidence: `codex-discovery.jsonl`, `codex-discovery.stderr`.
