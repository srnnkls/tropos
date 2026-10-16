#!/usr/bin/env bash
set -uo pipefail

readonly MARGIN=4

rgb() { printf '\e[38;2;%d;%d;%dm' "0x${1:0:2}" "0x${1:2:2}" "0x${1:4:2}"; }

# Recessed doom-one and doom-one-light hues and greys, following the macOS appearance.
if [[ $(defaults read -g AppleInterfaceStyle 2>/dev/null) == Dark ]]; then
  blue=$(rgb 6f9cc4) green=$(rgb 8aa36c) red=$(rgb b07c7a) grey=$(rgb 7f858b)
else
  blue=$(rgb 5f82c4) green=$(rgb 5f8f5e) red=$(rgb a8706b) grey=$(rgb 8a8e93)
fi
# Claude Code's own orange, which herdr's Claude mark uses too.
orange=$(rgb d77757)
reset=$'\e[0m'

input=$(cat)

IFS=$'\x1f' read -r model model_id session dir used size pct duration_ms effort cache_seen cache_expires cache_misses < <(jq -r '[
  (.model.display_name // "Claude"),
  (.model.id // ""),
  (.session_id // ""),
  (.workspace.current_dir // .cwd // "."),
  (.context_window.total_input_tokens // 0),
  (.context_window.context_window_size // 200000),
  ((.context_window.used_percentage // 0) | floor),
  ((.cost.total_duration_ms // 0) | floor),
  ((.effort | if type == "object" then .level else . end) // .effort_level // ""),
  (.prompt_cache.caching_observed // false),
  (.prompt_cache.expires_at // 0),
  (.prompt_cache.misses // 0)
] | map(tostring) | join("\u001f")' <<<"$input")

if [[ -z $effort ]]; then
  effort=${CLAUDE_CODE_EFFORT_LEVEL:-$(jq -r '.effortLevel // "default"' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" 2>/dev/null)}
fi

# Limen reports the model and effort to the herdr pane; the hook events it
# hears carry no effort, so a change seen here is sent through its hook. One
# record per session holds the last key sent and whether limen took it; an
# unanswered send is retried after RETRY seconds.
readonly RETRY=30
report_model() {
  [[ -n ${HERDR_PANE_ID:-} && -n $model_id && -n $session ]] || return 0
  command -v limen >/dev/null 2>&1 || return 0
  local level=$effort record="${TMPDIR:-/tmp}" seen="" now
  [[ $level == default ]] && level=""
  local key="$model_id/$level"
  record="${record%/}/claude-statusline-model.$session"
  [[ -r $record ]] && seen=$(<"$record")
  [[ $seen == "$key ok" ]] && return 0
  now=${EPOCHSECONDS:-$(date +%s)}
  [[ $seen == "$key sent "* ]] && ((now - ${seen##* } < RETRY)) && return 0
  printf '%s sent %s\n' "$key" "$now" >"$record" 2>/dev/null || return 0
  {
    jq -c --arg model "$model_id" --arg effort "$level" \
      '{hook_event_name: "StatusLine", model: $model, effort: $effort,
        session_id, transcript_path, cwd}' <<<"$input" |
      limen hook claude | grep -q '"received":true' &&
      printf '%s ok\n' "$key" >"$record"
  } >/dev/null 2>&1 &
  disown 2>/dev/null || true
}
report_model

cols=${COLUMNS:-}
if [[ -z $cols ]]; then
  cols=$( { stty size </dev/tty | cut -d' ' -f2; } 2>/dev/null)
fi
cols=$(( ${cols:-80} - MARGIN ))

common=$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
if [[ -n $common ]]; then
  root=$(basename "$(dirname "$common")")
else
  root=$(basename "$dir")
fi

branch=$(git -C "$dir" branch --show-current 2>/dev/null || true)

human() {
  awk -v n="$1" 'BEGIN {
    if (n >= 1000000) printf "%.1fM", n / 1000000
    else if (n >= 1000) printf "%.0fk", n / 1000
    else printf "%d", n
  }'
}

elapsed=$((duration_ms / 1000))
duration=""
((elapsed > 0)) && printf -v duration '%02d:%02d' $((elapsed / 3600)) $((elapsed % 3600 / 60))

tokens="$(human "$used")/$(human "$size")"

cache=""
if [[ $cache_seen == true ]] && ((cache_expires > 0)); then
  cache="$(date -r "$cache_expires" "+%d %b %H:%M" 2>/dev/null || date -d "@$cache_expires" "+%d %b %H:%M")"
fi
misses=""
((cache_misses > 0)) && misses=$cache_misses

# Nerd Font glyphs; model, directory and branch match herdr-status-field-glyphs.
# The context glyph is a pie filled to the nearest eighth, full only at 100%.
slices=(󰄰 󰪞 󰪟 󰪠 󰪡 󰪢 󰪣 󰪤 󰪥)
slice=$((((pct > 100 ? 100 : pct) * 8 + 50) / 100))
((slice == 8 && pct < 100)) && slice=7
# Ghostel widens an icon over the space after it; the icon's own size leaves the gap.
readonly ICON_WIDTH=1 GAP=" " SEP="  " BRANCH_MIN=24
field() { printf '%s%s%s%s%s' "$1" "$2" "$GAP" "$3" "$reset"; }
# Columns a field takes on screen: its icon, the gap and its text.
width() { echo $((ICON_WIDTH + ${#GAP} + ${#1})); }

# Model and token usage always show. Project and effort come next, then the
# branch at up to BRANCH_MIN columns, then duration and cache while they fit;
# the branch grows into whatever room is left.
context="$tokens ($pct%)"
fixed=$(($(width "$model") + ${#SEP} + $(width "$context")))
[[ -n $misses ]] && fixed=$((fixed + ${#SEP} + $(width "$misses")))
keep() {
  local name=$1 reserve=${2:-0}
  [[ -n ${!name} ]] || return 0
  if ((fixed + ${#SEP} + $(width "${!name}") + reserve > cols)); then
    printf -v "$name" '%s' ""
  else
    fixed=$((fixed + ${#SEP} + $(width "${!name}")))
  fi
}
keep root
keep effort
[[ -z $root ]] && branch=""
reserve=0
if [[ -n $branch ]]; then
  held=$((cols - fixed - ${#SEP} - ICON_WIDTH - ${#GAP}))
  ((held > BRANCH_MIN)) && held=$BRANCH_MIN
  ((held > ${#branch})) && held=${#branch}
  ((held >= 4)) && reserve=$((${#SEP} + ICON_WIDTH + ${#GAP} + held))
fi
keep duration "$reserve"
keep cache "$reserve"
room=$((cols - fixed - ${#SEP} - ICON_WIDTH - ${#GAP}))
if [[ -n $branch ]] && ((${#branch} > room)); then
  if ((room > 1)); then branch="${branch:0:room-1}…"; else branch=""; fi
fi

line="$(field "$orange" 󰍛 "$model")"
[[ -n $effort ]] && line+="${SEP}$(field "$grey" 󱐋 "$effort")"
[[ -n $root ]] && line+="${SEP}$(field "$blue"  "$root")"
[[ -n $branch ]] && line+="${SEP}$(field "$green"  "$branch")"
[[ -n $duration ]] && line+="${SEP}$(field "$grey" 󰔛 "$duration")"
[[ -n $cache ]] && line+="${SEP}$(field "$grey" 󱘪 "$cache")"
[[ -n $misses ]] && line+="${SEP}$(field "$red" 󱘵 "$misses")"
line+="${SEP}$(field "$grey" "${slices[slice]}" "$context")"
printf '%s\n' "$line"
