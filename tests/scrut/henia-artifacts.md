# Deployed harness contracts

Phora runs this test after deployment. It checks the actual repository-local
trees using parsed YAML, rendered bodies, resource bytes and executable modes.
The expected paths and fields follow the [Claude Code skill contract](https://code.claude.com/docs/en/skills),
[Codex skill contract](https://learn.chatgpt.com/docs/build-skills),
[Pi](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md),
[OMP](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md), and the
[Agent Skills specification](https://agentskills.io/specification).

```scrut
$ python3 "$TESTDIR/check-artifacts.py" "$TESTDIR/../.."
claude: 25 skills; metadata, body, resources and support OK
codex: 25 skills; metadata, body, resources and support OK
pi: 25 skills; metadata, body, resources and support OK
omp: 25 skills; metadata, body, resources and support OK
```
