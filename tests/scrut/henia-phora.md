# Henia → Phora prototype

Run with `scrut test tests/scrut/henia-phora.md` from the repository root.
Requires Henia, Phora, Python 3.11+ and Mike Farah's
`yq` v4 on PATH. Tests use a disposable local Git repository; no harness or model
is started and no user installation is changed. Phora fetches the public Loqui
revision selected by TROPOS_LOQUI_SOURCE (default ~/projects/loqui).

## Clean deployment and repeat sync

```scrut
$ set -eu; \
> export PATH="$TESTDIR/../../.henia/bin:$PATH"; \
> cp -R "$TESTDIR/../../phora" "$TESTDIR/../../scripts" "$TESTDIR/../../skills" "$TESTDIR/../../agents" "$TESTDIR/../../instructions" .; \
> cp "$TESTDIR/../../henia.toml" "$TESTDIR/../../phora.toml" .; \
> mkdir -p tests && cp -R "$TESTDIR" tests/scrut; \
> git init -q && git -c user.name=Smoke -c user.email=smoke@example.invalid -c core.hooksPath=/dev/null commit -q --allow-empty -m smoke; \
> mkdir -p .henia; \
> cp -R "$TESTDIR/../../.henia/harnesses" .henia/harnesses; \
> export TROPOS_LOQUI_SOURCE="${TROPOS_LOQUI_SOURCE:-$HOME/projects/loqui}"; \
> python3 scripts/sync-harnesses.py --no-progress > .henia/first-sync.log 2>&1 || { cat .henia/first-sync.log; exit 1; }; \
> grep -q '^hook post_sync#.*henia-artifacts.md.* ok$' .henia/first-sync.log; \
> python3 "$TESTDIR/check-artifacts.py" .; \
> diff -qr skills "$TESTDIR/../../skills"; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > before.json; \
> python3 scripts/sync-harnesses.py --no-progress > .henia/repeat-sync.log 2>&1 || { cat .henia/repeat-sync.log; exit 1; }; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > after.json; \
> cmp before.json after.json && echo 'repeat sync: unchanged'
claude: 25 skills; metadata, body, resources and support OK
codex: 25 skills; metadata, body, resources and support OK
pi: 25 skills; metadata, body, resources and support OK
omp: 25 skills; metadata, body, resources and support OK
repeat sync: unchanged
```

## Removed generated resources are pruned; foreign files survive

```scrut
$ set -eu; \
> printf 'temporary resource\n' > skills/bash/obsolete.txt; \
> python3 scripts/sync-harnesses.py --no-progress > .henia/add-resource.log 2>&1 || { cat .henia/add-resource.log; exit 1; }; \
> for target in .claude .agents .pi .omp; do test -f "$target/skills/bash/obsolete.txt"; printf 'foreign\n' > "$target/foreign.txt"; done; \
> rm skills/bash/obsolete.txt; \
> python3 scripts/sync-harnesses.py --no-progress > .henia/remove-resource.log 2>&1 || { cat .henia/remove-resource.log; exit 1; }; \
> for target in .claude .agents .pi .omp; do test ! -e "$target/skills/bash/obsolete.txt"; test "$(cat "$target/foreign.txt")" = foreign; rm "$target/foreign.txt"; done; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > removed.json; \
> cmp before.json removed.json && echo 'stale resource removed; foreign files preserved'
stale resource removed; foreign files preserved
```

## A compiler error prevents deployment

```scrut
$ set -eu; \
> cp phora.lock before-failure.lock && cp phora.local.lock before-failure.local.lock; \
> cp skills/code/SKILL.md original-skill.md; \
> printf '\n{{if}}\n' >> skills/code/SKILL.md; \
> if python3 scripts/sync-harnesses.py --no-progress > .henia/failed-sync.log 2>&1; then echo 'unexpected success'; exit 1; fi; \
> grep -q 'parse template' .henia/failed-sync.log; \
> mv original-skill.md skills/code/SKILL.md; \
> cmp phora.lock before-failure.lock && cmp phora.local.lock before-failure.local.lock; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > failed.json; \
> cmp before.json failed.json && echo 'compiler failure: deployed artifacts unchanged'
compiler failure: deployed artifacts unchanged
```

## A missing dependency preserves the deployed bundle

```scrut
$ set -eu; \
> if TROPOS_LOQUI_SOURCE="$PWD/missing-loqui" python3 scripts/sync-harnesses.py --no-progress > .henia/missing-dependency.log 2>&1; then echo 'unexpected success'; exit 1; fi; \
> grep -q 'Loqui is missing' .henia/missing-dependency.log; \
> cmp phora.lock before-failure.lock && cmp phora.local.lock before-failure.local.lock; \
> python3 "$TESTDIR/check-artifacts.py" . --snapshot > dependency-failed.json; \
> cmp before.json dependency-failed.json && echo 'dependency failure: deployed artifacts unchanged'
dependency failure: deployed artifacts unchanged
```
