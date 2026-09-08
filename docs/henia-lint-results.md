# Henia lint results

Verified 2026-09-08 in `/Users/srnnkls/projects/tropos/.worktrees/henia-phora` with the installed `/Users/srnnkls/.local/bin/henia`.

- 13/13 built-in rule IDs emitted diagnostics.
- 7/7 custom Expr selectors emitted diagnostics; passing and disabled controls also ran.
- 69 native CLI replay cases completed, including 25 invalid-configuration/runtime cases.
- Real local Model2Vec inference succeeded without downloads, servers or external inference.
- All five requested baseline-noise categories reproduced. An additional frontmatter-selector omission was confirmed.

The canonical behavior reference is [Henia's lint documentation](/Users/srnnkls/projects/henia/docs/lint-rules.md). These are observations, not another rule specification.

## Reproduction and evidence

Run from this worktree's root:

```sh
sh prototype/henia/lint/replay.sh
```

The [replay script](../prototype/henia/lint/replay.sh) contains the exact commands and records each invocation as `.henia/evidence/lint/<case>.{command,stdout,stderr,exit}`. Expected failures do not stop replay; the script's own status is not an aggregate pass/fail result. `sh -n prototype/henia/lint/replay.sh` passed.

The installed binary reports no `version` command or `--version` option. `.henia/evidence/lint/binary.txt` records `go version -m`; `binary.sha256` identifies the executable. Build metadata identifies revision `084015a1a61935eff238f2dc9e51aa1cf75a7412`, with `vcs.modified=true`, Go 1.26.5 and aikit 1.16.0.

The original full-skills baseline was captured before the canonical skill rewrites:

```sh
henia lint skills --format json
```

Evidence: `.henia/evidence/lint/baseline-original.{json,stderr,exit}`. Exit 1; 73 diagnostics: 62 `missing-reference`, 6 `duplicate-heading`, 4 `broken-link`, 1 `invalid-template`. This is the original working-tree baseline, not a pristine-HEAD claim. Replay deliberately does not overwrite it.

## Built-in coverage

| Rule | Observed positive evidence |
|---|---|
| `metadata` | `builtins`: missing description, invalid date and malformed YAML; warning and error severities |
| `invalid-template` | `builtins`: unclosed `if`; `false-positives`: escaped literal function name |
| `invalid-markup` | `builtins`: unclosed directive |
| `broken-link` | `builtins`: nonexistent relative Markdown destination |
| `missing-reference` | `builtins`: absent skill token |
| `duplicate-heading` | `builtins`: repeated heading with related location |
| `duplicate-content` | `builtins`: within/across-file duplicates; `exact-nested`: directive/list paragraphs; `exact-normalized`: case/space normalization |
| `similar-content` | `jaccard`, `containment`, `containment-reversed`, `shingles-low` |
| `semantic-content` | `semantic`, `semantic-low`, `semantic-strict`: real cached model |
| `duplicate-skill` | `builtins`: same explicit skill name in two directories |
| `outdated-reference` | `builtins`: configured old token and replacement |
| `large-skill` | `builtins`: configured four-line limit exceeded |
| `stale-review` | `builtins`: date 2000-01-01 exceeds configured 180 days |

`clean` returned `[]`, exit 0 under `--strict`, including a resolvable skill token, valid heading anchor, remote URL, valid directive and fenced examples. `exact-excluded` returned `[]` for repeated fenced content and paragraphs containing template actions. `disabled-cli` and `disabled-config` both returned `[]`, exit 0, with all 13 IDs disabled.

`warnings` and `text` exited 0 with eight warnings. `strict` emitted the same eight diagnostics and exited 1. Syntax/metadata errors failed without strict mode. JSON carried original-file coordinates and related locations; text carried `path:line:column`, severity, rule and message. Invalid format, missing scan path and unknown CLI disable ID each failed.

## Custom Expr and dynamic nodes

`custom-positive` emitted six selector diagnostics; `custom-frontmatter` separately emitted the seventh at YAML key position 2:1. The missing seventh diagnostic in the combined fixture is the confirmed gap below. `custom-negative` and `custom-disabled` returned `[]`, exit 0. The combined negative fixture alone does not prove frontmatter traversal because of that gap.

`custom-inline` emitted one directive diagnostic for inline canonical markup, not for its inline-code or fenced examples. `environment` passed checks over node kind/text/start/end/dynamic, document path/kind/body/lines, nested frontmatter, missing-key coalescing, directive name and inline status. The selector fixtures exercise attribute lookup, `when`, default-true `when`, boolean assertions, default warning severity and explicit error severity.

`dynamic-skip` emitted only the document diagnostic. `dynamic-include` emitted all seven selector IDs, including the dynamic YAML key, heading, directive, paragraph, link and image. The document rule still saw unexpanded input. A directive with template content was skipped conservatively by default.

The 25 `error-*` configuration/runtime cases all exited 1:

- Invalid/reserved/duplicate IDs; unknown selector; invalid severity; missing message/assertion.
- Unknown expression field and `when` name; malformed syntax; non-boolean assertion; disabled `now()`.
- Expression source above 16,384 bytes; AST above 2,048 nodes; VM collection above the 100,000 allocation budget.
- Runtime conversion failures in both `assert` and `when`, emitted as error diagnostics under the custom rule ID.
- Out-of-range lexical thresholds, negative limit, empty outdated key, unknown disabled rule, and missing/out-of-range semantic configuration.

## Similarity and local inference

| Case | Actual result |
|---|---|
| `jaccard` | 0.8181818182, method `jaccard`, five sorted shared phrases |
| `containment`, `containment-reversed` | 1.0 in either order, method `containment` |
| `lexical-negative`, `lexical-disabled` | No findings |
| `shingles`, `shingles-low` | Two-word shingles score 1/3: no finding at 0.4; one at 0.3 |
| `lexical-precedence` | Jaccard 0.4166666667 wins even though containment is 1.0 |
| `exact-disabled` | No findings: disabling exact diagnostics does not forward identical normalized paragraphs into lexical matching |
| `semantic-exact-precedence` | Exact duplicate emitted; nonexistent semantic model was not loaded |
| `semantic-lexical-precedence` | Lexical duplicate emitted; nonexistent semantic model was not loaded |
| `semantic-missing` | Hard failure loading local tokenizer; relative path resolved against the declaring config |
| `semantic-disabled`, `semantic-lazy` | Exit 0 despite nonexistent model: disabled or fewer than two eligible candidates |
| `semantic-high` | No findings at threshold 1 |
| `semantic-strict` | Semantic warning makes strict lint exit 1 |

Bounded discovery checked existing Hugging Face and Anax cache locations plus common local model directories. Three cached Potion snapshots were present. Inference used the unmodified local snapshot:

```text
/Users/srnnkls/.cache/huggingface/hub/models--minishlab--potion-retrieval-32M/snapshots/6fc8051fab2a1e0ee76689cf08c853792ac285e7
```

`semantic.toml` uses that existing absolute path. Replay is machine-local: another machine needs an existing compatible model and a corresponding fixture-config path; replay does not download one.

At threshold 0.35, only the negated instruction matched the original, cosine 0.9770079023. At threshold 0.15, the intended paraphrase also matched, cosine 0.2887532582; the unrelated bird paragraph did not. This is a measured limitation, consistent with the canonical warning that embeddings do not establish equivalent instructions.

## Verified gaps and baseline noise

All commands below run from the worktree root. The replay case names point to preserved expected/actual evidence.

### Existing YAML keys can silently disappear from custom selection

```sh
henia lint prototype/henia/lint/custom/frontmatter.md --config prototype/henia/lint/frontmatter.toml --format json
henia lint prototype/henia/lint/custom/frontmatter-body.md --config prototype/henia/lint/frontmatter.toml --format json
```

Expected: both emit `frontmatter-probe` at 2:1 because both have the same existing description key and an always-false assertion. Actual: heading-only body emits the diagnostic; valid `:::note` body returns `[]`, exit 0. `frontmatter-multiline` independently reproduces omission in the combined selector fixture. Source inspection: `/Users/srnnkls/projects/henia/internal/lint/rules.go` decodes the whole Markdown file as YAML for source marks and silently skips nodes on decoder failure. Valid frontmatter parsing earlier in lint does not prevent this omission.

### Five requested noise categories

```sh
henia lint prototype/henia/lint/false-positives --config prototype/henia/lint/default.toml --format json
```

Expected for ordinary Tropos prose: these examples describe shell values, filesystem paths, literal templates, issue identifiers and independently scoped template headings—not unresolved Henia artifacts. Actual: eight findings, exit 1.

| Fixture | Actual | Original baseline examples |
|---|---|---|
| `shell.md` | `$HOME`, `$TMPDIR` interpreted as absent skills | `skills/bash/SKILL.md:30`; `skills/issue/SKILL.md:73` |
| `slash.md` | `/usr/local/bin/wake-nix`, `/etc/nixos/idle-suspend.nix` interpreted as absent commands | `skills/workstation/SKILL.md:17,22` |
| `escaped/SKILL.md` | Literal `\{{email}}` produces undefined template-function error | `skills/dotfiles/SKILL.md:8`, error names template line 103 |
| `issue.md` | `#172`, `#N` interpreted as missing files `172`, `N` | `skills/issue/SKILL.md:38,46`; `skills/review/SKILL.md:44` |
| `headings.md` | `## Evidence` under different candidate headings flagged as duplicate | Six findings in `skills/debate/templates/debate-scratchpad.md` |

`control.md` contributes no diagnostics for fenced shell/path/issue examples. These are compatibility noise for existing Tropos conventions; the token and duplicate-heading behavior may be intentional Henia semantics rather than implementation defects. Backslash escaping does not protect Go template actions in the installed linter.

## Boundaries

All lint commands used local inputs and cached weights; no network access or model download was required.

Real semantic inference is not blocked. The zero-embedding warning branch was attempted with unusual Unicode text (`semantic-zero`) but returned no diagnostic; that branch is not verified. Corrupt-weight/inconsistent-dimension branches and cancellation/resource-exhaustion timing were not forced. User-global configuration merging was not mutated or exercised. These results establish the requested rule/selector/CLI surface, not exhaustive coverage of every internal branch or Expr built-in.
