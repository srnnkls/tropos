# Canonical Tropos → Henia → Phora migration

All 25 Tropos skills on `prototype/henia-phora` are canonical sources. Henia
compiles 100 skill variants for Claude Code, Codex, Pi and OMP. Phora installs
committed build snapshots and the transitive Loqui dependency; Scrut checks the
installed artifacts after deployment.

```text
skills/ + agents/ + instructions/
    → Henia → validated Git packages → Phora → harness trees → Scrut
phora.toml → compiled Tropos manifest → Loqui Git pin ───┘
```

The optional smoke deployment is relative to `.henia/probe/home`.

| Harness | Smoke deployment | Invocation |
| --- | --- | --- |
| Claude Code | `.claude/skills/` | `/name` |
| Codex | `.codex/skills/` | `$name` |
| Pi | `.pi/skills/` | `/skill:name` |
| OMP | `.omp/skills/` | `/skill:name` |

## Run

Requires Henia, Phora, Scrut, Git, Python 3.11+, and Mike Farah's `yq` v4.
Building Henia additionally requires Go 1.26.5+ and a checkout with the
reference-after-code-fences fix used by this branch.

```sh
HENIA_SOURCE=~/projects/henia mise run prototype:build
TROPOS_LOQUI_SOURCE=~/projects/loqui mise run prototype:sync
mise run prototype:smoke
mise run prototype:test
```

`TROPOS_LOQUI_SOURCE` defaults to `~/projects/loqui`. Its committed HEAD must be
available from `https://github.com/srnnkls/loqui.git`; uncommitted Loqui edits are
not published. Phora may fetch that public dependency on the first sync.

The public [phora.toml](../phora.toml) advertises canonical Tropos artifacts and
the Loqui dependency layout. It contains no harness build paths or installation
homes. Consumers own the Henia build and select their deployment targets.

`prototype:sync` is an optional local smoke deployment. It builds and validates
all variants, then runs [phora/prototype.toml](../phora/prototype.toml) from the
ignored `.henia/probe` directory. One compiled Git source at
`.henia/packages/tropos` has a ref per harness. Each ref contains the native
artifacts and a `phora.toml` pinning Loqui. The prototype binds that source with
`transitive = true` and runs Scrut in `post_sync`.

Builds start with an empty output tree. Failed compilation, missing dependencies,
or failed pre-deployment checks preserve the current packages and deployment.
Content-identical builds produce the same Git commits. Successful syncs remove
obsolete managed resources and preserve unrelated files. A post-sync failure
reports an error after deployment and does not imply rollback.

To replay an existing lock without building or accessing the network:

```sh
(cd .henia/probe && phora sync --frozen --no-hooks --no-progress)
mise run prototype:smoke
```

## Canonical authoring

Edit `skills/<name>/SKILL.md` and its resources. All portable metadata lives at
the top level. Native hints, tool permissions, hooks and execution context live
under `henia.targets.claude.frontmatter`; Codex UI metadata lives under
`henia.targets.codex.openai.interface`. Every Codex skill gets its own
`agents/openai.yaml`.

`henia.variables.context_commands` supplies context inputs. Claude receives
native dynamic context expressions; the other harnesses receive explicit shell
instructions. Write canonical backtick references such as `$implement` in main
skill bodies. Henia renders `/implement`, `$implement` or `/skill:implement` as
appropriate, preserving literal code examples. Copied reference documents use
relative Markdown links and portable runtime shell blocks.

`implement`, `test`, `continue` and `loop` require explicit invocation. Claude,
Pi and OMP receive `disable-model-invocation: true`; Codex receives
`policy.allow_implicit_invocation: false`. The shared Pi/OMP compiler profile
lives in [`.henia/harnesses/pi-omp`](../.henia/harnesses/pi-omp/transform.toml).

All resources retain their bytes and executable modes. The bundle contains the
three role contracts, `instructions/AGENTS.md`, and the native `CLAUDE.md` or
`AGENTS.md` entrypoint. Claude role metadata is normalized; other harnesses
receive portable role descriptions and bodies without Claude hooks. Existing
workflow routing continues to materialize those role contracts.

## Transitive Loqui dependency

[phora.toml](../phora.toml) owns the Tropos → Loqui edge. The build copies that
dependency declaration into each compiled ref, pinned to Loqui's committed HEAD.
A consumer sets `transitive = true` on Tropos; Phora installs Loqui beneath each
harness's `skills/loqui/reference/loqui` and records a separate dependency
instance per target. No consumer-side Loqui source or dependency-export alias is
needed. Hash checks cover the published guides from the same commit, excluding
uncommitted files and third-party caches.

This branch does not require a symlink inside canonical `skills/loqui`.
`loqui-link`/`loqui-unlink` remain legacy authoring helpers; unlink such a source
resource before compiling because Henia rejects source-resource symlinks.

## Dotfiles Phora probe

Dotfiles's `phora.toml` owns a Henia pre-sync build and a single transitive
`tropos` source. Its ignored local deployment selects the targets. The build
reads `prototype/henia-phora` from `~/projects/tropos` without switching that
checkout or including its local edits.

The shared `.phora-shadow/home` contains dotfiles and compiled Tropos together:
`.claude`, `.codex` and `.pi/agent`. OMP uses the user's native Claude provider,
so it needs no duplicate `.omp` tree. Helpers land in `.local/bin`; Codex config
keeps its separate `.config/codex` identity path. All validation stays local.

## Smoke coverage

The artifact check covers all 25 skills in all four targets: parsed metadata,
invocation controls, Codex sidecars, template expansion, context dialects,
references, resource bytes and modes, role contracts, global instructions, and
Loqui's complete selected file inventory and hashes.

Lifecycle tests run real Henia and Phora in a disposable Tropos repository.
They cover clean and repeated deployment, stale-resource removal, foreign-file
preservation, malformed templates, and missing dependency inputs. They use the
selected public Loqui pin and may need network access to fill the fixture cache.
No model session or live-home installation is involved.

## Historical live probes

The earlier five-skill prototype passed one authenticated read-only `code` probe
each in Claude Code, Codex, Pi and OMP on 2026-09-20. Pi also exposed native
slash-command expansion. Recordings remain under ignored
`.henia/evidence/live-20260920/`; their hashes describe that earlier build.
The full migration does not claim model-driven execution of all 25 workflows.

## Gaps

Henia's existing lint warnings remain visible; errors and artifact assertions
fail the build. The deployed role contracts do not automatically register
host-specific Codex agent configurations. Workflow tools such as `peer`, `gh`,
Gestalt, FAS and the selected harnesses still need their normal workstation
configuration. Henia reads `~/.config/henia`, which may affect compilation.

Generated packages, runtime pins, caches and deployments are ignored. Build
packages are local artifacts; no generated Git repositories are pushed.
Historical exploratory results remain in [build results](henia-build-results.md)
and [lint results](henia-lint-results.md).
