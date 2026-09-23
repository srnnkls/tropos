# Canonical Tropos with Henia and Phora

The `prototype/henia-phora` branch contains 25 canonical skills, three agent
contracts, shared instructions and declarative harness profiles. Henia reads
this checkout directly and builds Claude, Codex, Pi and OMP artifacts.

[phora.toml](../phora.toml) advertises the package: the committed canonical
files, the FAS rules, and a relative installation target for Loqui. A consumer
imports Tropos into a preparation target of its own, receiving the pinned
Tropos snapshot with Loqui under `skills/loqui/reference/loqui`. Nothing is
written into this checkout.

The dotfiles consumer names both sides of the compiler explicitly:

```text
phora prepares .tropos → henia builds .tropos into .henia → phora links .henia slices → Scrut
```

Its `post_prepare` hook runs `henia build .tropos --output .henia --clean --harness claude,codex`;
Henia reads the prepared [henia.toml](../henia.toml) from the input directory,
preserves executable helpers and publishes output atomically. Dotfiles selects
Claude and Codex; OMP reads Claude natively. FAS rules deploy from the same
prepared snapshot, so skills and rules share one pin.

Builds use the locked Tropos commit. `phora update tropos --fast-forward --prune`
advances it. For uncommitted edits, a consumer's local configuration points
`tropos` at a working tree with `deploy = "link"`; Phora then prepares the live
files while Loqui stays pinned. A frozen replay skips generation and requires
existing output.

[check-artifacts.py](../tests/scrut/check-artifacts.py) validates all four generated
harness contracts, the skill inventory and the Loqui guides with
`--build <output-directory>`. Consumers check only their deployment: links,
modes, pins and frozen replay. No live model invocation is required.
