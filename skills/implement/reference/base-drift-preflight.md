# Base-Drift Preflight

Catch overlapping upstream work before mutation and ensure a proposed PR is based on current trunk. Do not turn drift checking into a per-batch ritual.

## Checkpoints

Run only:

1. before the first mutating batch on an existing branch;
2. on resume when the initial gate was never recorded, upstream movement is known, or new overlap evidence exists;
3. immediately before final integration validation and PR creation.

Skip the initial check when the branch was created in the same invocation from a freshly fetched `origin/<trunk>`. Do not fetch/rebase after every batch or loop iteration.

## Initial Procedure

1. Resolve the base from `--base`, recorded branch metadata, or the branch merge base.
2. Fetch that remote base once.
3. Measure divergence:

```bash
git rev-list --left-right --count "origin/<base>...HEAD"
```

When `behind == 0`, proceed.

When behind, compare upstream-changed files against the branch's changed files and the upcoming batch's declared mutation paths:

```bash
git diff --name-only "HEAD...origin/<base>"
git diff --name-only "$(git merge-base "origin/<base>" HEAD)" HEAD
```

No overlap means report drift in one line and proceed. A shared path is a concrete semantic-collision risk; stop and ask whether to rebase, proceed knowingly, or abort. Hand rebase strategy to `/git rebase`.

Do not enumerate indirect callers or infer collision from conceptual similarity alone.

## Pre-PR Sync

Before final integration validation or PR creation, fetch trunk and require the branch to be current:

```bash
git fetch origin <trunk> --quiet
behind=$(git rev-list --count "HEAD..origin/<trunk>")
```

If behind, rebase once. On a clean rebase, rerun the smallest native validation that covers changed integration behavior. On conflict, stop for rebase strategy. Never open or merge a PR while `behind > 0` or GitHub reports it conflicting/dirty.

A code-changing rebase invalidates only evidence affected by the rebase. Re-run bounded integration review when cross-batch behavior changed; do not automatically repeat cleared batch-local role reviews.
