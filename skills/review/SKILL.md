---
name: review
description: Unified review dispatcher for code, PR, scope, structural, and bounded test-quality review.
argument-hint: "[target]"
allowed-tools: Bash(git status *), Bash(git log *), Bash(git branch *), Bash(find *), Bash(gh pr list *)
metadata:
  type: generic
---

## Pre-loaded Context

Git status:
!`git status --short 2>/dev/null || true`

Recent commits:
!`git log --oneline -5 2>/dev/null || true`

Current branch:
!`git branch --show-current 2>/dev/null || true`

Active scopes:
!`find scopes -maxdepth 3 -name scope.md 2>/dev/null || true`

Open PRs:
!`gh pr list --limit 5 --json number,title,headRefName --jq '.[] | "#\(.number) \(.title) (\(.headRefName))"' 2>/dev/null || true`

# Review Dispatcher

## Routes

Pre-parse `--reviewers <aliases>` and pass it to downstream review operations.

| Target | Action |
|---|---|
| PR number, `#N`, or GitHub PR URL | [operations/pr.md](operations/pr.md) |
| Commit SHA | `Skill(code, review --rev <sha>)` |
| `--final <scope>` | Standalone holistic scope review |
| Scope path/name | `Skill(scope, review <name>)` |
| `gestalt` or `--structural` | `Skill(gestalt, review <target>)` |
| `--test-audit [path]` or test path | [operations/test-audit.md](operations/test-audit.md), explicit or changed tests only |
| Existing file path | `Skill(code, review --path <path>)` |
| Missing | Ask for PR, commit, diff, path, scope, structural, or test target |

## Canonical Contracts

- [models.md](reference/models.md) — registry and host compatibility
- [harnesses.md](reference/harnesses.md) — native/routable/peer dispatch
- [finding-bar.md](reference/finding-bar.md) — finding admission and sufficiency
- [report.md](reference/report.md) — YAML schemas
- [synthesis.md](reference/synthesis.md) — merge, disposition, and fix-round limits
- [peer skill](../peer/SKILL.md) — external fan-out and report layout

## Reviewer Selection

Resolve in order:

1. `--reviewers` aliases;
2. `validation.yaml.review_config` for standalone scope review;
3. one interactive multi-select from live `peer list`.

Use registry harness/family metadata. On Codex, same-family work uses `codex-native`; on Claude, same-family work uses native `opus`/`sonnet`. A Claude-host `ROUTABLE=yes` cross-family alias is a generated native reviewer; other compatible aliases use peer. Reject same-host loopback, inactive generated variants, unknown aliases, and unsupported shared effort. Never silently convert.

Standalone scope selection persists to `validation.yaml.review_config`. Implementation-owned review ignores that file and uses its immutable batch routing snapshot.

## Dispatch

Materialize reviewed content, requirements, exact schema, and the verbatim finding bar before dispatch. Commands and workdirs supplement the prompt; they do not replace content.

For multi-role review, launch every selected role, native reviewer, routable reviewer, and external role fan-out in one assistant message. Persisted non-inherited effort is carried by the generated Task definition name; peer routes receive it through `--effort`.

A standalone review may synthesize successful reports while disclosing missing reviewers, but never passes with zero. An implementation-owned gate requires one success from every execution class present in its batch snapshot.

## Report Paths

Use `peer path`; never assemble `.peer` directories manually.

| Route | Subject | Stage |
|---|---|---|
| PR | `pr-<number>` | `review` |
| Commit | `commit-<sha7>` | `review` |
| Branch diff | `diff-<range>` | `review` |
| Working tree | `working` | `review` |
| Path | `path-<basename>` | `review` |
| Scope | `scope-<name>` | `review` |
| Implementation batch | scope name | `b<batch>-review-<role>` |
| Integration | scope name | `integration-review` |

Save every materialized prompt as `prompt.md`. The peer manifest/filename is authoritative provenance.

## Synthesis and Landing

Admit only findings with a reachable trigger and wrong outcome. Batch by mechanism, treat agreement as evidence rather than validity, and stop at the shared sufficiency cutoff. Land confirmed findings through `tfcp`; PR thread closure composes through `tfcprr`.
