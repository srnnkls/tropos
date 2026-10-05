# Canonical Tropos with Henia and Phora

Tropos contains 23 canonical skills, three agent contracts, shared instructions
and declarative harness profiles. The Gestalt, Limen and Loqui skills live in
their own repositories beside the commands and guides they document. Henia
serves them to Claude, Codex, Pi and OMP.

[phora.toml](../phora.toml) declares the package. Its `moira` target installs
the Moira FAS rules under `rules/fas/moira`; Henia fetches the Gestalt, Limen
and Loqui skill packages declared in [henia.toml](../henia.toml).

Consumers import Tropos as a transitive source and select slices through
`[offers.*]`: `fas` offers the FAS rules, `library` the skills Henia serves, and
`default` the canonical files. Skills and rules come from the same Tropos
snapshot and share one pin.

Harnesses receive skills from Henia's library, not from Phora. Tropos is a
global Henia package, and `henia sync --global` runs `henia install`, which
writes each harness's static skills, hybrid heads and the `henia` catalog from
the modes in [henia.toml](../henia.toml). Hybrid heads and dynamic skills render
from the library when read, so a library update reaches every harness without a
rebuild. FAS rules are symlinked and take effect live.

`mise run test-artifacts` prepares this working tree through a throwaway
consumer, compiles all four harnesses, and runs
[check-artifacts.py](../tests/scrut/check-artifacts.py) over the prepared input
and the output: harness contracts, the skill inventory and the Loqui language guides.
Consumers check only their deployment: links, modes, pins and frozen replay. No
live model invocation is required.
