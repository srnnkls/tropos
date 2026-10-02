# Canonical Tropos with Henia and Phora

Tropos contains 24 canonical skills, three agent contracts, shared instructions
and declarative harness profiles. The Gestalt and Limen skills live in their own
repositories beside the commands they document. Henia compiles a prepared copy
of them into Claude, Codex, Pi and OMP artifacts.

[phora.toml](../phora.toml) declares the package. Its targets install Loqui
under `skills/loqui/reference/loqui`, the Gestalt skill under `skills/gestalt`,
the Limen skill under `skills/limen` and the Moira FAS rules under
`rules/fas/moira`. Its `[sources.harnesses]` entry,
`build = { tool = "github:srnnkls/henia@…", run = "henia build {input} --output {output}" }`,
compiles the prepared tree into all four harnesses, and the `claude`, `codex`,
`pi` and `omp` targets take one harness each under `dist/`.

Consumers import Tropos as a transitive source, so its dependencies and the
harness build resolve in the consumer's sync, and select slices through
`[offers.*]`: `claude`, `codex`, `pi` and `omp` offer one compiled harness,
`fas` offers the FAS rules, and `default` offers the canonical files. Henia reads
[henia.toml](../henia.toml) from the build input and preserves executable
helpers. Skills and rules come from the same Tropos snapshot and share one pin.

Builds use the locked Tropos commit. `phora update tropos --fast-forward --prune`
advances it. For uncommitted edits, a consumer's local configuration points
`tropos` at a working tree with `deploy = "link"`; `phora sync` then builds the
harnesses from the working tree. Compiled skills are copied build output, so a
skill edit reaches a harness only after the next `phora sync`; FAS rules are
symlinked and take effect live. A frozen replay skips generation and requires
existing output.

`mise run test-artifacts` prepares this working tree through a throwaway
consumer, compiles all four harnesses, and runs
[check-artifacts.py](../tests/scrut/check-artifacts.py) over the prepared input
and the output: harness contracts, the skill inventory and the Loqui guides.
Consumers check only their deployment: links, modes, pins and frozen replay. No
live model invocation is required.
