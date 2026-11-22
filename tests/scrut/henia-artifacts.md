# Compiled harness contracts

A throwaway Phora consumer prepares this working tree the way a deployment
does, and Henia compiles every harness into `out/`. The expected paths and
fields follow the [Claude Code skill contract](https://code.claude.com/docs/en/skills),
[Codex skill contract](https://learn.chatgpt.com/docs/build-skills),
[Pi](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md),
[OMP](https://github.com/can1357/oh-my-pi/blob/main/docs/skills.md), and the
[Agent Skills specification](https://agentskills.io/specification).

```scrut
$ root=$(cd "$TESTDIR/../.." && pwd -P); \
> cat > phora.toml <<TOML
> [sources]
> tropos = { path = "$root", deploy = "link", transitive = true }
> henia = { build = { inputs = ["tropos"], run = "henia build \"\$PHORA_INPUT/tropos\" --output \"\$PHORA_OUTPUT\"", key = "henia --version" } }
> [targets.input]
> path = "input"
> sources = ["tropos"]
> [targets.out]
> path = "out"
> sources.henia = { collapse = false }
> TOML
```

```scrut
$ phora sync --no-progress > sync.log 2>&1 || cat sync.log
```

Every harness installs the hybrid skills from `henia.toml` plus the `henia`
catalog; dynamic skills stay out of the skill directories.

```scrut
$ for h in claude codex pi omp; do echo "$h: $(ls out/$h/skills | paste -sd' ' -)"; done
claude: clarify code continue debate dispatch git henia herdr implement issue loop loqui memex pr review rsb scope sweep tfcp tfcprr validate
codex: clarify code continue debate dispatch git henia herdr implement issue loop loqui memex pr review rsb scope sweep tfcp tfcprr validate
pi: clarify code continue debate dispatch git henia herdr implement issue loop loqui memex pr review rsb scope sweep tfcp tfcprr validate
omp: clarify code continue debate dispatch git henia herdr implement issue loop loqui memex pr review rsb scope sweep tfcp tfcprr validate
```

The catalog names every dynamic skill.

```scrut
$ sed -n 's/^- `\([a-z-]*\)`:.*/\1/p' out/claude/skills/henia/SKILL.md | paste -sd' ' -
adversarial bash doc dotfiles peer ponytail scrut skill strict-tdd test workstation
```

Skill frontmatter carries only the fields each harness reads.

```scrut
$ for h in claude codex pi omp; do \
>   echo "$h: $(for f in out/$h/skills/*/SKILL.md; do [ "$f" = out/$h/skills/henia/SKILL.md ] || yq --front-matter=extract 'keys | .[]' "$f"; done | sort -u | paste -sd' ' -)"; \
> done
claude: allowed-tools argument-hint context description disable-model-invocation hooks metadata name
codex: description metadata name
pi: description disable-model-invocation metadata name
omp: description disable-model-invocation metadata name
```

On Claude a hybrid skill is one head preload, allowed to run `henia show`.

```scrut
$ cat out/claude/skills/code/SKILL.md
---
allowed-tools: Bash(henia show *)
argument-hint: '[operation] [target]'
description: Code domain context for explicit implementation, review, and test workflows.
metadata:
  type: domain
name: code
---

!`henia show code --head`
```

The other harnesses cannot preload, so a hybrid skill ends by telling the
agent to read its contents and context, and no skill contains a preload.

```scrut
$ tail -3 out/codex/skills/code/SKILL.md
run first: `henia show code --toc`

run first: `henia context code`
```

```scrut
$ grep -l '!`' out/codex/skills/*/SKILL.md out/pi/skills/*/SKILL.md out/omp/skills/*/SKILL.md
[1]
```

Skills marked `auto_invoke: false` stay explicit: Claude, Pi and OMP disable
model invocation, and Codex disables implicit invocation.

```scrut
$ for s in clarify continue loop sweep; do \
>   echo "$s: $(for h in claude pi omp; do yq --front-matter=extract '.disable-model-invocation' out/$h/skills/$s/SKILL.md; done | paste -sd' ' -) $(yq '.policy.allow_implicit_invocation' out/codex/skills/$s/agents/openai.yaml)"; \
> done
clarify: true true true false
continue: true true true false
loop: true true true false
sweep: true true true false
```

Every Codex skill but the catalog has an interface sidecar whose short description fits the
25–64 character range; the listing names the offenders.

```scrut
$ for d in out/codex/skills/*/; do \
>   s=$(basename "$d"); y=$d/agents/openai.yaml; [ "$s" = henia ] && continue; \
>   if [ ! -f "$y" ]; then echo "$s: missing"; \
>   else n=$(yq '.interface.short_description | length' "$y"); [ "$n" -ge 25 ] && [ "$n" -le 64 ] || echo "$s: $n"; fi; \
> done
```

Agent roles keep their source body on every harness. Claude also receives the
role's `claude-agent` frontmatter; the others get only name and description.

```scrut
$ for h in claude codex pi omp; do for r in tester implementer reviewer; do \
>   diff <(awk 'c >= 2; /^---$/ { c++ }' input/agents/$r.md) <(awk 'c >= 2; /^---$/ { c++ }' out/$h/agents/$r.md) > /dev/null || echo "$h/$r: body differs"; \
> done; done
```

```scrut
$ yq --front-matter=extract . out/claude/agents/tester.md
---
color: red
description: Write bounded failing tests and prove the RED state
name: tester
skills:
  - test
  - code
```

```scrut
$ yq --front-matter=extract . out/codex/agents/tester.md
---
description: Write bounded failing tests and prove the RED state
name: tester
```

Instructions render skill references in each harness's syntax: a projected
skill by its invocation, a dynamic one through `henia show`.

```scrut
$ grep -h '^Reach other agent sessions' out/claude/CLAUDE.md out/codex/AGENTS.md out/pi/AGENTS.md
Reach other agent sessions through `/herdr`, never through built-in cross-session messaging.
Reach other agent sessions through `$herdr`, never through built-in cross-session messaging.
Reach other agent sessions through `/skill:herdr`, never through built-in cross-session messaging.
```

```scrut
$ grep -o 'only through explicit [^,]*, [^,]*,' out/claude/CLAUDE.md
only through explicit `/implement`, `henia show test`,
```
