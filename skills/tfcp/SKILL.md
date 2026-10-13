---
name: tfcp
description: Land the fixes for a local review — triage, fix, commit, push. Dispositions every finding of a code review (in-context or from a `.peer/` report directory) as fix, residual, or needs-decision, applies the fix bucket, commits once behind the hook gate, and pushes. Use for "tfcp", "triage the review findings", "apply the review findings", "fix and push the review issues"; `tfcprr` composes on it for PR threads.
metadata:
  type: domain
henia:
  targets:
    claude:
      frontmatter:
        argument-hint: '[--issue <id>…] [--report <path>] [-m <msg>] [paths…]'
        allowed-tools: Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git status *), Bash(git rev-parse *), Bash(git branch *)
    codex:
      openai:
        interface:
          display_name: Tfcp
          short_description: Apply the canonical tfcp skill workflow
          default_prompt: Use $tfcp for the requested task.
---

:::head{context slots="git.commits review.criteria"}


# tfcp — triage + fix + commit + push

Run the steps in order; a failure at any step stops the rest. Never report a fix as landed unless its commit and push succeeded. The whole fix set rides one commit and one push.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--issue <id>` | every finding | Triage only this synthesized-report finding id (`C1`, `H2`, …); repeat per finding. |
| `--report <path>` | findings in context | Read findings from this synthesized report or [`peer path` report directory](../peer/SKILL.md#report-layout--peer). |
| `-m, --message <text>` | derived | Commit message, in the format of step 3. |
| `[paths…]` | already-staged | Files to stage before committing. |

## Workflow

### 1. Triage

Read findings from the review in context or `--report`; `--issue` narrows them. Carry a synthesized report's dispositions without reopening triage. Apply the [finding bar](../review/reference/finding-bar.md) and listed `review.criteria` providers ([review slots](../review/SKILL.md#slots)) to raw findings, giving each exactly one disposition:

| Disposition | Outcome |
|-------------|---------|
| `fix` | step 2 |
| `residual` | report without fixing |
| `needs decision` | return the forcing constraint to the user |

State the dispositions before touching a file.

### 2. Fix — apply the triaged subset

Apply the whole `fix` bucket and edit nothing outside it; if already applied, skip to staging. Make each fix the smallest change at the shared root, not per caller; hardening the finding doesn't name is `residual`.

### 3. Stage and commit

Confirm the staged set is the fixes and nothing unrelated. Write the message in the format the `git.commits` providers ([git slots](../git/SKILL.md#slots)) set.

```bash
git status --short          # confirm the staged set
git add <paths…>            # skip if already staged
git commit -m "<message>"
SHA=$(git rev-parse --short HEAD)   # this skill's return value
```

### 4. Push

Push before anything downstream names the SHA.

```bash
git push                    # or: git push -u origin <branch> on first push
```

### 5. Report

One line carrying the whole triage, naming each `needs decision` finding with its forcing constraint, e.g. `C1, H2 fixed → 1f8e3a2 pushed (hooks green); M4 residual (no reachable trigger), H3 needs decision (new trait on the store)`.

## Error Handling

| Condition | Action |
|-----------|--------|
| No findings in context and no `--report` | Stop — ask which review to work from |
| `--issue <id>` matches no finding | Stop — list the available ids |
| Triage leaves the `fix` bucket empty | Stop — report the dispositions; there is nothing to commit |
| Nothing staged and no `paths…` | Stop — the fix never landed in the working tree |
| Commit fails (hooks red) | Stop, surface hook output, fix, retry; do not push |
| Push rejected (non-fast-forward) | Stop, reconcile (pull/rebase), retry; do not report as landed |
| No upstream for the branch | `git push -u origin <branch>` |

:::

:::related
- `tfcprr` — the PR variant: this chain, then reply to and resolve each review thread
- `review` — produces the findings this operates on
:::
