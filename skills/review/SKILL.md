---
name: review
description: Unified review dispatcher for code, PR, scope, structural, and bounded test-quality review.
metadata:
  type: generic
henia:
  slots:
    review.criteria:
    review.general:
    review.architecture:
    review.tests:
    review.abstractions:
    review.detectors: keyed(list(command))
  variables:
    context_commands:
      - label: Git status
        command: git status --short 2>/dev/null || true
      - label: Recent commits
        command: git log --oneline -5 2>/dev/null || true
      - label: Current branch
        command: git branch --show-current 2>/dev/null || true
      - label: Active scopes
        command: find scopes -maxdepth 3 -name scope.md 2>/dev/null || true
      - label: Open PRs
        command: gh pr list --limit 5 --json number,title,headRefName --jq '.[] | "#\(.number) \(.title) (\(.headRefName))"' 2>/dev/null || true
      - label: Available peers
        command: peer list 2>/dev/null || true
      - label: Default reviewers
        command: peer defaults reviewers 2>/dev/null || true
      - label: Resolved routes
        command: peer route show -C . 2>/dev/null || true
  targets:
    claude:
      frontmatter:
        argument-hint: '[target]'
        allowed-tools: Bash(git status *), Bash(git log *), Bash(git branch *), Bash(find *), Bash(gh pr list *), Bash(peer *)
    codex:
      openai:
        interface:
          display_name: Review dispatcher
          short_description: Review code, PRs, scopes, and test quality
          default_prompt: Use $review to review the requested target.
---

::::head{context slots="review.criteria review.general review.architecture review.tests review.abstractions review.detectors"}


# Review Dispatcher

:::routes
Pre-parse `--reviewers <aliases>` and pass it to downstream review operations.

| Target | Action |
|---|---|
| PR number, `#N`, or GitHub PR URL | Invoke `$pr` with `review <target>` |
| Commit SHA | Invoke `$code` with `review --rev <sha>` |
| `--final <scope>` | Standalone holistic scope review |
| Scope path/name | Invoke `$scope` with `review <name>` |
| `--structural` | Structural review of `<target>` from its definition-level diff and the changed symbols' callers |
| `--test-audit [path]` or test path | [operations/test-audit.md](operations/test-audit.md), explicit or changed tests only |
| Existing file path | Invoke `$code` with `review --path <path>` |
| Missing | Ask for PR, commit, diff, path, scope, structural, or test target |
:::

::::

## Slots

| Slot | Covers |
|---|---|
| `review.criteria` | Repository review requirements with their canonical citations; reviewers check them as applicable requirements, and triage and PR comment assessment cite them |
| `review.general` | Correctness, security, and performance criteria for the General role |
| `review.architecture` | Layering, dependency direction, and seam rules for the Architecture role |
| `review.tests` | Test-review criteria for the General role on changed tests and for [test audits](operations/test-audit.md); the [test failure modes](../test/reference/failure-modes.md) stay |
| `review.abstractions` | Owned modules, sanctioned dependencies, and abstraction boundaries for the Abstractions role |
| `review.detectors` | Commands run on the change whose output the Abstractions role takes as candidates, never as gate results; keyed by language as `review.detectors.<language>` |

Every slot except `review.criteria` and `review.detectors` is keyed `review.<slot>.<domain>`; all providers apply together. The [code review roles](../code/SKILL.md#review-roles) stay the gates; providers add criteria. Style criteria come from `code.style`.

## Canonical Contracts

[models.md](reference/models.md) (live registry), [peer routing](../peer/reference/routing.md) (host compatibility, dispatch), [harnesses.md](reference/harnesses.md) (materialization, result coverage), [finding-bar.md](reference/finding-bar.md) (admission, sufficiency), [report.md](reference/report.md) (YAML schemas), [synthesis.md](reference/synthesis.md) (merge, disposition, fix-round limits), [peer skill](../peer/SKILL.md) (external fan-out, report layout).

## Reviewer Selection

Take the first present: `--reviewers` aliases; `validation.yaml.review_config` for standalone scope review; live `peer defaults reviewers`. Validate under [peer routing](../peer/reference/routing.md). Standalone scope selection persists to `validation.yaml.review_config`; implementation-owned review ignores that file and uses its immutable batch routing snapshot.

::::head

:::instruction{priority=high}
## Dispatch

Build each prompt per [materialization](reference/harnesses.md#materialization), dispatch per [concurrent dispatch](reference/harnesses.md#concurrent-dispatch), and apply the [result gate](reference/harnesses.md#results).
:::

::::

## Report Paths

Create directories through [`peer path`](../peer/SKILL.md#report-layout--peer).

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

## Synthesis and Landing

Synthesize per [review synthesis](reference/synthesis.md). Land admitted findings through `$tfcp`; close PR threads through `$tfcprr`.
