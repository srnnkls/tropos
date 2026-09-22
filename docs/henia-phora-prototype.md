# Canonical Tropos with Henia and Phora

The `prototype/henia-phora` branch contains 25 canonical skills, three agent
contracts, shared instructions and declarative harness profiles. Henia reads
this checkout directly and builds Claude, Codex, Pi and OMP artifacts.

[phora.toml](../phora.toml) advertises the canonical source and the relative
installation target for Loqui. Importing Tropos prepares Loqui under the
checkout's ignored `skills/loqui/reference/loqui` directory. Canonical Tropos
files are read in place.

The dotfiles consumer declares `~/projects/tropos` with the prototype branch.
Its preparation target points to this branch's existing worktree at
`~/projects/tropos/.worktrees/henia-phora`, preserving the main checkout's
unrelated branch and local edits. It uses one root shared/local configuration
pair with native Phora hooks:

```text
Prepare transitive Loqui in Tropos → Henia reads Tropos → dotfiles/.henia → harness targets → Scrut
```

The `post_prepare` hook invokes Henia with this checkout's [henia.toml](../henia.toml)
and source directory, writing `.henia/<harness>` in dotfiles. Henia includes the
Loqui resources, preserves executable helpers and publishes output atomically.
Phora links the selected outputs to the local deployment targets and runs Scrut
through `post_sync`. Dotfiles selects Claude and Codex; OMP reads Claude natively.
Its active probe keeps deployment destinations in a temporary home.

Builds include current working files. Phora pins the dependency catalog and Loqui;
`phora update tropos --fast-forward --prune` advances the catalog when it changes.
Ordinary `phora sync` rebuilds from the current checkout using existing dependency
pins. A frozen replay skips generation and requires existing output.

[check-artifacts.py](../tests/scrut/check-artifacts.py) validates all four generated
harness contracts with `--build <output-directory>`. Dotfiles' Scrut checks also
verify deployed resources, helper links, local configuration coexistence, the
selected worktree, and frozen replay. No live model invocation is required.
