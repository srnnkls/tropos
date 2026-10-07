---
name: git
description: Modern git workflows plus dispatched operations (rebase strategy analysis). Use when managing branches, structuring commits, choosing development strategies, or planning a rebase.
metadata:
  type: domain
henia:
  slots:
    git.branching:
    git.commits:
  provides:
    git.branching: {section: development-model}
    git.commits: {section: commits}
  targets:
    claude:
      frontmatter:
        argument-hint: '[operation] [args]'
        allowed-tools: Bash(git status *), Bash(git log *), Bash(git branch *), Bash(git rev-parse *)
    codex:
      openai:
        interface:
          display_name: Git
          short_description: Apply the canonical git skill workflow
          default_prompt: Use $git for the requested task.
  variables:
    context_commands:
      - label: Current branch
        command: git branch --show-current 2>/dev/null || true
      - label: Status
        command: git status --short 2>/dev/null | head -10
---

::::head{.context title="Git" slots="git.branching git.commits"}
Trunk-based development with short-lived branches, squash merges and modern git commands, plus a dispatched `rebase` operation that analyzes branch state and recommends a strategy.

:::routes{.protocol}
| `$ARGUMENTS` | Action |
|---|---|
| `rebase [args]` | Read and follow [operations/rebase.md](operations/rebase.md) |
| None | Use the sections below as reference |
:::

## Slots

| Slot | Covers |
|---|---|
| `git.branching` | Branch naming and merge strategy; replaces [Development Model](#development-model) |
| `git.commits` | Commit format, scope vocabulary, signing and granularity; replaces [Commits](#commits) |
::::

:::head

## Development Model

- `main` is always deployable.
- One branch per feature or fix, squash-merged back within hours to days.
- Branch names: `<type>/<short-description>` (`feat/auth`, `fix/null-check`); a scope uses `feat/<scope-name>` unless it records another branch; a GitHub issue uses `<issue-number>-<issue-title>`, which `issue pr` reads.

## Commits

Conventional commits, imperative and lowercase: `<type>(<scope>): <description>` with type `feat`, `fix`, `refactor`, `chore`, `docs`, `test` or `perf`. One logical change per commit; stage specific paths.

:::

## Commands

| Legacy | Modern |
|---|---|
| `git checkout <branch>` | `git switch <branch>` |
| `git checkout -b <branch>` | `git switch -c <branch>` |
| `git checkout -- <file>` | `git restore <file>` |
| `git push --force` | `git push --force-with-lease` |
| manual fixup | `git commit --fixup <sha>` + `git rebase -i --autosquash main` |

## Cascading Branches

Rebase downstream branches before the upstream ref changes identity through a squash merge, force-push or delete. After squash-merging `A`:

```bash
git switch B
git rebase --onto main A
git branch -d A
```

Merge a chain bottom-up: merge `A`, rebase `B` onto main, merge `B`.

## Anti-Patterns

- Squash-merging a branch that downstream branches still build on.
- `git push --force` without `--lease`.
- Inverting `rebase --onto`: state "X will sit on top of Y" before running it.
- Committing, force-pushing or squash-merging after a rebase without checking `git log --oneline --graph <base>..HEAD`.

:::related
- `bash` — shell command patterns
- `issue` — PRs and issue links to branches
:::
