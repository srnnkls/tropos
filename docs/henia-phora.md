# Canonical Tropos with Henia and Phora

Tropos contains 25 canonical skills, three agent contracts, shared
instructions and declarative harness profiles. Henia compiles a prepared copy
of them into Claude, Codex, Pi and OMP artifacts.

[phora.toml](../phora.toml) advertises the package: the committed canonical
files, the FAS rules, and a relative installation target for Loqui. A consumer
imports Tropos into a preparation target of its own, receiving the pinned
Tropos snapshot with Loqui under `skills/loqui/reference/loqui`. Nothing is
written into this checkout.

The dotfiles consumer names both sides of the compiler explicitly:

```text
phora prepares .tropos → henia builds .tropos into .henia → phora links .henia slices → Scrut
```

Its `post_prepare` hook runs `henia build .tropos --output .henia --clean --harness claude,codex,pi`;
Henia reads the prepared [henia.toml](../henia.toml) from the input directory,
preserves executable helpers and publishes output atomically. Dotfiles selects
Claude, Codex and Pi; OMP reads Claude natively. FAS rules deploy from the same
prepared snapshot, so skills and rules share one pin.

Builds use the locked Tropos commit. `phora update tropos --fast-forward --prune`
advances it. For uncommitted edits, a consumer's local configuration points
`tropos` at a working tree with `deploy = "link"`; Phora then prepares the live
files while Loqui stays pinned. A frozen replay skips generation and requires
existing output.

`mise run test-artifacts` prepares this working tree through a throwaway
consumer, compiles all four harnesses, and runs
[check-artifacts.py](../tests/scrut/check-artifacts.py) over the prepared input
and the output: harness contracts, the skill inventory and the Loqui guides.
Consumers check only their deployment: links, modes, pins and frozen replay. No
live model invocation is required.
