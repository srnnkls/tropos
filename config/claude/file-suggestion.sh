#!/usr/bin/env bash
# Claude Code prints this command's stdout verbatim, so filtering happens here.

set -u

command -v rg >/dev/null 2>&1 || exit 0
command -v fzf >/dev/null 2>&1 || exit 0

if [ "$#" -gt 0 ]; then
  query="$1"
else
  command -v jq >/dev/null 2>&1 || exit 0
  query="$(jq -r 'if type == "object" and ((.query // "") | type == "string") then (.query // "") else empty end' 2>/dev/null)" || exit 0
fi

root="$PWD"
physical_root="$(pwd -P 2>/dev/null)" || exit 0

case "$query" in
  "~") query="$HOME" ;;
  "~/"*) query="$HOME/${query#\~/}" ;;
esac

case "$query" in
  "$root" | "$physical_root") query="" ;;
  "$root"/*) query="${query#"$root"/}" ;;
  "$physical_root"/*) query="${query#"$physical_root"/}" ;;
  /*) exit 0 ;;
esac

while [[ "$query" == ./* ]]; do query="${query#./}"; done
case "/$query/" in */../*) exit 0 ;; esac

prune=(
  .worktrees .cache .direnv .gradle .mypy_cache .next
  .pytest_cache .ruff_cache .terraform .tox .turbo .venv
  venv __pycache__ node_modules target build coverage dist
)

hidden=""
case "${CLAUDE_FILE_SUGGESTION_HIDDEN:-}" in
  1 | true | yes)
    hidden=1
    kept=()
    for directory in "${prune[@]}"; do
      case "$directory" in .*) continue ;; esac
      kept+=("$directory")
    done
    prune=("${kept[@]+"${kept[@]}"}")
    ;;
esac
prune=(.git "${prune[@]+"${prune[@]}"}")

globs=(--glob '!**/.git')
for directory in "${prune[@]}"; do
  globs+=(--glob "!**/$directory/**")
done

candidates=()
for entry in "$physical_root"/* "$physical_root"/.*; do
  [ -d "$entry" ] || continue
  name="${entry##*/}"
  case "$name" in . | .. | .git) continue ;; esac
  skip=""
  for directory in "${prune[@]}"; do
    if [ "$name" = "$directory" ]; then
      skip=1
      break
    fi
  done
  [ -n "$skip" ] || candidates+=("$name")
done

extra_roots=()
if [ "${#candidates[@]}" -gt 0 ] && command -v git >/dev/null 2>&1; then
  while IFS= read -r name; do
    [ -z "$name" ] || extra_roots+=("$name")
  done < <(printf '%s\n' "${candidates[@]}" | git check-ignore --stdin 2>/dev/null)
fi

policy=(--files --hidden --follow --no-config --no-messages "${globs[@]}")
sig="$(printf '%s\0' "$physical_root" "${policy[@]}" "${extra_roots[@]+"${extra_roots[@]}"}" | cksum | cut -d' ' -f1)"
cache="${TMPDIR:-/tmp}/cc-fsugg-$sig"
cache_ttl=10
now="$(date +%s)"
mtime=0
if [ -s "$cache" ]; then
  mtime="$(stat -f %m "$cache" 2>/dev/null || stat -c %Y "$cache" 2>/dev/null || printf '0')"
  case "$mtime" in '' | *[!0-9]*) mtime=0 ;; esac
fi

enumerate() {
  {
    rg "${policy[@]}"
    for name in "${extra_roots[@]+"${extra_roots[@]}"}"; do
      rg "${policy[@]}" -- "$name" 2>/dev/null | head -n 20000
    done
  } 2>/dev/null | LC_ALL=C sort -u | head -n 300000
}

case "$query" in
  .*) demote='^$' ;;
  *) demote='^[.]' ;;
esac

take() {
  awk -v limit=200 -v demote="$demote" '
    $0 ~ demote { if (deferred < limit) later[++deferred] = $0; next }
    taken < limit { print; taken++ }
    END { for (i = 1; i <= deferred && taken < limit; i++) { print later[i]; taken++ } }
  '
}

filter_candidates() {
  if [ -z "$query" ]; then
    take
  else
    fzf --filter="$query" --scheme=path --ignore-case | take
  fi
}

if [ -s "$cache" ] && [ "$mtime" -le "$now" ] && [ "$((now - mtime))" -lt "$cache_ttl" ]; then
  filter_candidates <"$cache"
  exit 0
fi

umask 077
temporary="$(mktemp "$cache.XXXXXX" 2>/dev/null)" || {
  enumerate | filter_candidates
  exit 0
}
cleanup() { [ -z "$temporary" ] || rm -f -- "$temporary"; }
trap cleanup EXIT

enumerate >"$temporary"
[ -s "$temporary" ] || exit 0
if mv -f "$temporary" "$cache" 2>/dev/null; then
  temporary=""
  filter_candidates <"$cache"
else
  filter_candidates <"$temporary"
fi
