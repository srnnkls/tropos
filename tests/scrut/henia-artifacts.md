# Compiled harness contracts

A throwaway Phora consumer prepares this working tree the way a deployment
does, with its pinned Loqui dependency, and Henia compiles every harness from
it. The checker reads the prepared input and the compiled trees using parsed
YAML, rendered bodies, resource bytes and executable modes. The expected paths
and fields follow the [Claude Code skill contract](https://code.claude.com/docs/en/skills),
[Codex skill contract](https://learn.chatgpt.com/docs/build-skills),
[Pi](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md),
[OMP](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md), and the
[Agent Skills specification](https://agentskills.io/specification).

```scrut
$ set -eu; \
> root=$(cd "$TESTDIR/../.." && pwd -P); \
> printf '%s\n' '[sources]' "tropos = { path = \"$root\", deploy = \"link\", transitive = true }" \
>   'henia = { build = { inputs = ["tropos"], run = "henia build \"$PHORA_INPUT/tropos\" --output \"$PHORA_OUTPUT\"", key = "henia --version" } }' \
>   '[targets.input]' 'path = "input"' 'sources = ["tropos"]' \
>   '[targets.out]' 'path = "out"' 'sources.henia = { collapse = false }' > phora.toml; \
> phora sync --no-progress > sync.log 2>&1 || { cat sync.log; exit 1; }; \
> python3 "$TESTDIR/check-artifacts.py" input out
claude: 26 skills; metadata, body, resources and support OK
codex: 26 skills; metadata, body, resources and support OK
pi: 26 skills; metadata, body, resources and support OK
omp: 26 skills; metadata, body, resources and support OK
```
