# Base-Drift Preflight

## Checkpoints

Run only:

1. before the first mutating batch on an existing branch, unless the branch was created in this invocation from a freshly fetched `origin/<trunk>`;
2. on resume when the initial gate was never recorded, upstream movement is known, or new overlap evidence exists;
3. immediately before final integration validation and PR creation.

Never fetch/rebase after a batch or loop iteration.

## Initial Procedure

1. Resolve the base from `--base`, recorded branch metadata, or the branch merge base.
2. Fetch that remote base once and measure divergence:

```bash
git rev-list --left-right --count "origin/<base>...HEAD"
```

When `behind == 0`, proceed. When behind, compare upstream-changed files with the branch's changed files and the upcoming batch's declared mutation paths:

```bash
git diff --name-only "HEAD...origin/<base>"
git diff --name-only "$(git merge-base "origin/<base>" HEAD)" HEAD
```

No overlap: report drift in one line and proceed. A shared path: stop and ask whether to rebase, proceed knowingly, or abort; hand rebase strategy to [git](../../git/SKILL.md) with `rebase`. Do not enumerate indirect callers or infer collision from conceptual similarity.

## Pre-PR Sync

```bash
git fetch origin <trunk> --quiet
behind=$(git rev-list --count "HEAD..origin/<trunk>")
```

If behind, rebase once. Clean rebase: rerun the smallest native validation covering changed integration behavior. Conflict: stop for rebase strategy. Never open or merge a PR while `behind > 0` or GitHub reports it conflicting/dirty.

A code-changing rebase invalidates only affected evidence: rerun bounded integration review when cross-batch behavior changed; never repeat cleared batch-local role reviews.
