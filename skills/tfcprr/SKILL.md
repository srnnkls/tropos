---
name: tfcprr
description: Close PR review threads you've addressed — tfcp (triage + fix + commit + push) then reply + resolve. Runs the `tfcp` skill over every accepted comment — triaging each into fix, residual, or needs-decision — then replies to and resolves the threads it fixed, referencing the commit. `--resolve-only` closes dismissed threads with a rationale reply and no fix. Use for "tfcprr", "close a review thread I fixed", "resolve threads I've addressed", "reply and resolve a dismissed thread".
metadata:
  type: domain
henia:
  targets:
    claude:
      frontmatter:
        argument-hint: --comment <id> [--comment <id>…] [--reply <text>] [-m <msg>] [--pr <n>] [--resolve-only] [paths…]
        allowed-tools: Bash(gh review *), Bash(gh pr *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
    codex:
      openai:
        interface:
          display_name: Tfcprr
          short_description: Apply the canonical tfcprr skill workflow
          default_prompt: Use $tfcprr for the requested task.
---

:::head{.context slots="git.commits review.criteria"}


# tfcprr — tfcp + reply + resolve

Run in order; a failure at any step stops the rest:

1. tfcp — triage, fix, commit (hook gate), push, owned by [`tfcp`](../tfcp/SKILL.md); returns the short SHA.
2. reply — `gh review reply`, naming the SHA. Never reply "Done in `<sha>`" unless the fix, commit, and push landed.
3. resolve — `gh review resolve`.

Both take the comment node id (`PRRC_…`) from `gh review comments <pr> --ids`.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--comment <id>` | — (≥1 required) | Comment node id to reply to and resolve; repeat per thread. |
| `--reply <text>` | composed from the fix | Reply note, posted as `Done in <sha> — <text>`. |
| `--pr <n>` | branch's PR | Override the PR. |
| `--resolve-only` | off | Dismissed thread: skip `tfcp`, post `--reply` verbatim, resolve. Ignores `-m` and `paths…`. |
| `-m, --message <text>` | derived | Commit message, forwarded to `tfcp`. |
| `[paths…]` | already-staged | Files to stage, forwarded to `tfcp`. |

## Workflow

1. Collect `--comment` ids into `COMMENT_IDS`; none → stop and ask. Resolve `PR`:

   ```bash
   PR="${pr_flag:-$(gh pr view --json number -q .number 2>/dev/null)}"
   [ -z "$PR" ] && { echo "no PR for this branch — pass --pr <n>"; exit 1; }
   ```

2. Invoke Skill `tfcp` with `-m` and `paths…` over the threads in `COMMENT_IDS` (the `comments` route's accepted set). It returns `$SHA` and a disposition per thread; only `fix` lands in the commit:

   | Disposition | Thread |
   |---|---|
   | `fix` | reply with the SHA, resolve |
   | `residual` | leave open; optionally reply the reason; never resolve |
   | `needs decision` | leave open; surface to the user with the constraint |

   Report an accepted thread that lands `residual` as a disagreement between the passes.

3. Per `fix` thread, reusing `$SHA`: show the body, confirm, then

   ```bash
   gh review reply "$PR" --comment "$COMMENT_ID" --body "Done in $SHA — <reply text>"
   gh review resolve "$PR" --comment "$COMMENT_ID"
   ```

   Resolve prints `✓ Resolved thread …`.

4. Report one line: SHA + hook result, push target, threads replied and resolved, threads left open and why. Format: `1f8e3a2 pushed (hooks green) → replied + resolved 3 threads; 1 left open (needs decision: new trait on the store)`.

## Resolve-only — dismissed threads

For a misread, already-addressed, or convention-contradicting thread. One invocation per thread with its own `--comment` and `--reply`; the rationale is posted verbatim:

```bash
gh review reply "$PR" --comment "$COMMENT_ID" --body "<rationale>"
gh review resolve "$PR" --comment "$COMMENT_ID"
```

## Error Handling

Triage, fix, commit, hook, and push failures follow `tfcp`'s table and stop the run before any reply.

| Condition | Action |
|-----------|--------|
| `--comment` missing | Stop |
| No thread lands in `fix` | No commit; leave threads open; report dispositions |
| `--resolve-only` with `-m`/`paths…` | Ignore them |
| No PR for branch and no `--pr` | Stop per workflow step 1 |
| `reply`/`resolve` finds no thread for the id | Wrong or already-resolved id — re-check with `gh review comments "$PR" --ids` |
| `gh` not authenticated | Report: run `gh auth login` |

:::

:::related
- `tfcp` — triage, fix, commit, push without the PR thread steps
- `pr` — `comments` produces the accepted and dismissed split this consumes
:::
