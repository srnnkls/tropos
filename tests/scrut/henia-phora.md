# Native Henia → Phora hooks

Requires Henia, Phora, Scrut and yq on PATH. Each test runs in a disposable
repository. Loqui is fetched through Git's URL rewrite from the local checkout
at TROPOS_LOQUI_SOURCE (default ~/projects/loqui); no live home is deployed.

## Clean deployment and repeat sync

```scrut
$ set -eu; \
> cp -R "$TESTDIR/../../phora" "$TESTDIR/../../skills" "$TESTDIR/../../agents" "$TESTDIR/../../instructions" .; \
> cp "$TESTDIR/../../henia.toml" "$TESTDIR/../../phora.toml" .; \
> mkdir -p .henia tests && cp -R "$TESTDIR/../../.henia/harnesses" .henia/harnesses && cp -R "$TESTDIR" tests/scrut; \
> git init -q -b prototype/henia-phora; \
> git config core.hooksPath /dev/null && git config commit.gpgsign false && git config user.name Smoke && git config user.email smoke@example.invalid; \
> git add skills agents instructions henia.toml phora.toml .henia/harnesses && git commit -qm canonical; \
> export GIT_CONFIG_GLOBAL="$PWD/gitconfig" GIT_CONFIG_SYSTEM=/dev/null; \
> git config --file "$GIT_CONFIG_GLOBAL" "url.${TROPOS_LOQUI_SOURCE:-$HOME/projects/loqui}.insteadOf" https://github.com/srnnkls/loqui.git; \
> (cd phora/prototype && phora sync) > first-sync.log 2>&1 || { cat first-sync.log; exit 1; }; \
> python3 "$TESTDIR/check-artifacts.py" .; \
> (cd phora/prototype && phora verify) > verify.log 2>&1; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > before.json; \
> (cd phora/prototype && phora sync) > repeat-sync.log 2>&1 || { cat repeat-sync.log; exit 1; }; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > after.json; \
> cmp before.json after.json && echo 'repeat sync: unchanged'
claude: 25 skills; metadata, body, resources and support OK
codex: 25 skills; metadata, body, resources and support OK
pi: 25 skills; metadata, body, resources and support OK
omp: 25 skills; metadata, body, resources and support OK
repeat sync: unchanged
```

## Removed resources are pruned; foreign files survive

```scrut
$ set -eu; \
> printf 'temporary resource\n' > skills/bash/obsolete.txt; \
> git add skills/bash/obsolete.txt && git commit -qm 'add resource'; \
> (cd phora/prototype && phora update --fast-forward) > add-resource.log 2>&1 || { cat add-resource.log; exit 1; }; \
> for target in .henia/probe/home/{.claude,.codex,.pi,.omp}; do test -f "$target/skills/bash/obsolete.txt"; printf 'foreign\n' > "$target/foreign.txt"; done; \
> git rm -q skills/bash/obsolete.txt && git commit -qm 'remove resource'; \
> (cd phora/prototype && phora update --fast-forward) > remove-resource.log 2>&1 || { cat remove-resource.log; exit 1; }; \
> for target in .henia/probe/home/{.claude,.codex,.pi,.omp}; do test ! -e "$target/skills/bash/obsolete.txt"; test "$(cat "$target/foreign.txt")" = foreign; rm "$target/foreign.txt"; done; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > removed.json; \
> cmp before.json removed.json && echo 'stale resource removed; foreign files preserved'
stale resource removed; foreign files preserved
```

## A compiler error prevents deployment

```scrut
$ set -eu; \
> cp phora/deploy/phora.lock before-failure.lock; \
> cp skills/code/SKILL.md original-skill.md; \
> printf '\n{{if}}\n' >> skills/code/SKILL.md; \
> git add skills/code/SKILL.md && git commit -qm 'invalid template'; \
> if (cd phora/prototype && phora update --fast-forward) > failed-sync.log 2>&1; then echo 'unexpected success'; exit 1; fi; \
> grep -q 'parse template' failed-sync.log; \
> mv original-skill.md skills/code/SKILL.md; \
> git add skills/code/SKILL.md && git commit -qm 'restore template'; \
> cmp phora/deploy/phora.lock before-failure.lock; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > failed.json; \
> cmp before.json failed.json && echo 'compiler failure: deployed artifacts unchanged'
compiler failure: deployed artifacts unchanged
```

## A missing dependency preserves the deployed bundle

```scrut
$ set -eu; \
> sed -i.bak 's|https://github.com/srnnkls/loqui.git|https://example.invalid/missing-loqui.git|' phora.toml; \
> git config --file "$GIT_CONFIG_GLOBAL" "url.$PWD/missing-loqui.insteadOf" https://example.invalid/missing-loqui.git; \
> git add phora.toml && git commit -qm 'missing dependency'; \
> if (cd phora/prototype && phora update --fast-forward) > missing-dependency.log 2>&1; then echo 'unexpected success'; exit 1; fi; \
> cmp phora/deploy/phora.lock before-failure.lock; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > dependency-failed.json; \
> cmp before.json dependency-failed.json && echo 'dependency failure: deployed artifacts unchanged'
dependency failure: deployed artifacts unchanged
```
