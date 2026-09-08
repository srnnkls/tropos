#!/bin/sh
# Run from the repository root. Each invocation preserves stdout, stderr and status.
set -u
p=prototype/henia/lint
e=.henia/evidence/lint
mkdir -p "$e"
run() {
    name=$1
    shift
    printf '%s\n' "henia lint $*" > "$e/$name.command"
    henia lint "$@" > "$e/$name.stdout" 2> "$e/$name.stderr"
    printf '%s\n' "$?" > "$e/$name.exit"
}
run builtins "$p/positive" --config "$p/builtins.toml" --format json
run clean "$p/negative" --config "$p/default.toml" --strict --format json
run warnings "$p/positive/a" --config "$p/builtins.toml" --format json
run strict "$p/positive/a" --config "$p/builtins.toml" --strict --format json
run text "$p/positive/a" --config "$p/builtins.toml" --format text
run disabled-config "$p/positive" --config "$p/disabled.toml" --strict --format json
run disabled-cli "$p/positive" --config "$p/builtins.toml" --disable metadata,large-skill,stale-review,duplicate-heading,duplicate-content,duplicate-skill,broken-link,missing-reference,outdated-reference,invalid-template,invalid-markup,similar-content,semantic-content --strict --format json
run exact-nested "$p/exact/nested.md" --config "$p/default.toml" --format json
run exact-normalized "$p/exact/normalized.md" --config "$p/default.toml" --format json
run exact-excluded "$p/exact/excluded" --config "$p/default.toml" --strict --format json
run jaccard "$p/lexical/jaccard.md" --config "$p/jaccard.toml" --format json
run containment "$p/lexical/containment.md" --config "$p/containment.toml" --format json
run lexical-negative "$p/lexical/unrelated.md" --config "$p/jaccard.toml" --strict --format json
run lexical-disabled "$p/lexical/jaccard.md" --config "$p/jaccard.toml" --disable similar-content --strict --format json
run shingles "$p/lexical/short.md" --config "$p/shingles.toml" --format json
run custom-positive "$p/custom/bad.md" --config "$p/custom.toml" --format json
run custom-negative "$p/custom/good.md" --config "$p/custom.toml" --strict --format json
run custom-disabled "$p/custom/bad.md" --config "$p/custom.toml" --disable custom-document,custom-frontmatter,custom-directive,custom-heading,custom-paragraph,custom-link,custom-image --strict --format json
run dynamic-skip "$p/dynamic" --config "$p/dynamic-skip.toml" --format json
run dynamic-include "$p/dynamic" --config "$p/dynamic-include.toml" --format json
run false-positives "$p/false-positives" --config "$p/default.toml" --format json
run semantic "$p/semantic" --config "$p/semantic.toml" --format json
run semantic-high "$p/semantic" --config "$p/semantic-high.toml" --strict --format json
run semantic-missing "$p/semantic" --config "$p/semantic-missing.toml" --format json
run semantic-disabled "$p/semantic" --config "$p/semantic-missing.toml" --disable semantic-content --strict --format json
run semantic-lazy "$p/negative/SKILL.md" --config "$p/semantic-missing.toml" --strict --format json
for config in "$p"/errors/*.toml; do
    name=${config##*/}
    run "error-${name%.toml}" "$p/negative/SKILL.md" --config "$config" --format json
done
run frontmatter-heading "$p/custom/frontmatter.md" --config "$p/frontmatter.toml" --format json
run frontmatter-directive "$p/custom/frontmatter-body.md" --config "$p/frontmatter.toml" --format json
run frontmatter-multiline "$p/custom/bad.md" --config "$p/frontmatter.toml" --format json
run custom-frontmatter "$p/custom/frontmatter.md" --config "$p/custom.toml" --format json
run custom-inline "$p/custom/inline.md" --config "$p/custom.toml" --format json
run environment "$p/environment" --config "$p/environment.toml" --strict --format json
run shingles-low "$p/lexical/short.md" --config "$p/shingles-low.toml" --format json
run semantic-low "$p/semantic" --config "$p/semantic-low.toml" --format json
run semantic-zero "$p/semantic-zero" --config "$p/semantic.toml" --format json
run semantic-exact-precedence "$p/exact/normalized.md" --config "$p/semantic-missing.toml" --format json
run invalid-format "$p/negative" --config "$p/default.toml" --format yaml
run missing-path "$p/absent.md" --config "$p/default.toml" --format json
run unknown-cli-disable "$p/negative" --config "$p/default.toml" --disable typo --format json
run containment-reversed "$p/lexical/containment-reversed.md" --config "$p/containment.toml" --format json
run lexical-precedence "$p/lexical/containment.md" --config "$p/precedence.toml" --format json
run exact-disabled "$p/exact/normalized.md" --config "$p/jaccard.toml" --disable duplicate-content --format json
run semantic-lexical-precedence "$p/lexical/jaccard.md" --config "$p/semantic-lexical.toml" --format json
run semantic-strict "$p/semantic" --config "$p/semantic.toml" --strict --format json
