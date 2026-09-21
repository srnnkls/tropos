# Canonical Tropos with Henia and Phora

The `prototype/henia-phora` branch contains 25 canonical skills, three agent
contracts, shared instructions, and declarative harness profiles. Phora stages
the committed source and its transitive Loqui dependency; an ordinary hook runs
Henia and deploys the generated artifacts. No Python build/deployment wrapper or
generated Git package is involved.

```text
Tropos + transitive Loqui → Phora staging → Henia → Phora → local harness trees
```

## Run locally

Put Henia with clean builds, supporting files and artifact profiles on PATH,
along with Phora's explicit local-package import support, Scrut and yq.

```bash
mise run prototype:sync
mise run prototype:smoke
mise run prototype:test
```

`prototype:sync` runs `phora update --fast-forward` in
[phora/prototype](../phora/prototype/phora.toml). Its source selects the committed
`prototype/henia-phora` branch. Uncommitted source changes are intentionally absent
from the staged input. Ordinary `phora sync` in that directory reuses the pin.

All writes stay in the repository: `.henia/source` holds canonical inputs,
`.henia/build` holds compiler output, and `.henia/probe/home` contains `.claude`,
`.codex`, `.pi` and `.omp` smoke deployments. No live harness home is installed.
The standalone probe checks all four outputs; dotfiles uses Claude natively for
OMP and therefore installs only Claude, Codex and Pi trees.

## Configuration

[phora.toml](../phora.toml) advertises the canonical exports and Loqui's dependency
layout. Its `path = "."` export means the same pinned package snapshot when
imported. Loqui is pinned by Phora beneath `skills/loqui/reference/loqui`; Henia
copies those resources with the skill. Consumers need only one canonical Tropos
source with `transitive = true` and an explicit `imports = ["tropos"]` anchor.

[henia.toml](../henia.toml) selects Claude, Codex, Pi and OMP profiles. Henia renders
skills and sidecars, applies each agent profile, preserves executable resources,
and writes native instruction entrypoints. `clean = true` replaces the generated
output only after successful compilation, removing obsolete resources without a
cleanup script. The directory is compiler-owned.

The staging `post_sync` hook calls `henia build`, then runs Phora in
[phora/deploy](../phora/deploy/phora.toml), then Scrut. The `&&` chain prevents
deployment after a compiler failure. Global `post_sync` also runs on removal-only
updates. Deployment declares a generated local source per harness and uses native
links, with `collapse = false` to preserve unrelated files alongside them. Source
acquisition, pruning and ownership remain Phora's responsibility.

Global source configuration and local destinations stay separate in the dotfiles
consumer. Its main `phora.toml` selects `~/projects/tropos` at this prototype
branch; it never switches or builds the unrelated real working checkout.

## Verification

[henia-artifacts.md](../tests/scrut/henia-artifacts.md) checks all skills, parsed
metadata, references and directives, OpenAI sidecars, agent contracts, instruction
entrypoints, complete Loqui resources, executable modes and deployment links.
[henia-phora.md](../tests/scrut/henia-phora.md) runs native hooks in a disposable
repository, checking repeat syncs, resource removal, foreign-file preservation,
and compiler/dependency failure behavior. It fetches Loqui through a Git URL
rewrite to the local checkout, without starting a model or touching a live home.

`phora verify` checks the copied canonical input. Linked build outputs are outside
Phora's content-integrity checks, so Scrut validates their contents explicitly.
A frozen replay uses cached source pins; generated links still need the build
directory. Henia can recreate it from the staged canonical input.
