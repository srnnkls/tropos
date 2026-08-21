---
name: tfcprr
description: Close PR review threads you've addressed — tfcp (triage + fix + commit + push) then reply + resolve. Runs the `tfcp` skill over every accepted comment — triaging each into fix, residual, or needs-decision — then replies to and resolves the threads it fixed, referencing the commit. `--resolve-only` closes dismissed threads with a rationale reply and no fix. Use for "tfcprr", "close a review thread I fixed", "resolve threads I've addressed", "reply and resolve a dismissed thread".
argument-hint: "--comment <id> [--comment <id>…] [--reply <text>] [-m <msg>] [--pr <n>] [--resolve-only] [paths…]"
allowed-tools: Bash(gh review *), Bash(gh pr *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
metadata:
  type: domain
---

# tfcprr — tfcp + reply + resolve

Close the loop on the PR review threads you've addressed: land the fixes through [`tfcp`](../tfcp/SKILL.md), then reply to each thread referencing the commit and resolve it.

`tfcprr` is `tfcp` plus the two PR steps, strictly ordered — each gates the next:

1. *tfcp* — triage, fix, commit (hook gate), push. Owned by the [`tfcp` skill](../tfcp/SKILL.md); it returns the short SHA.
2. *reply* — `gh review reply` posts to the thread, naming the SHA, which is why the push must land first.
3. *resolve* — `gh review resolve` marks the thread resolved.

A failure at any step stops the rest. Never reply "Done in `<sha>`" when the fix, commit, or push didn't land.

`reply` and `resolve` both take the comment node id (`PRRC_…`) from `gh review comments <pr> --ids` and map it to the thread internally — no manual id juggling.

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--comment <id>` | — (≥1 required) | Review comment node id to reply to and whose thread to resolve; repeat once per addressed thread. From `gh review comments <pr> --ids`. |
| `--reply <text>` | — | Reply note; the short SHA is prepended automatically (`Done in <sha> — <text>`). If omitted, compose one from the fix. |
| `--pr <n>` | branch's PR | Override the PR (otherwise resolved from the current branch). |
| `--resolve-only` | off | Close a *dismissed* thread — skip `tfcp` entirely. Post `--reply` verbatim (no `Done in <sha>` prefix) and resolve. Ignores `-m` and `paths…`. |
| `-m, --message <text>` | derived | Forwarded to `tfcp` — commit message. |
| `[paths…]` | already-staged | Forwarded to `tfcp` — files to stage. |

---

## Workflow

### 1. Parse arguments and resolve the PR

- At least one `--comment <id>` is required (→ `COMMENT_IDS`). Without one there's no thread to reply to or resolve — stop and ask.
- Resolve the PR into `PR`: use `--pr <n>` if given, else the branch's PR. Stop if neither yields one.

```bash
PR="${pr_flag:-$(gh pr view --json number -q .number 2>/dev/null)}"
[ -z "$PR" ] && { echo "no PR for this branch — pass --pr <n>"; exit 1; }
```

### 2. tfcp — triage, fix, commit, push

Invoke Skill `tfcp`, forwarding `-m` and `paths…`. Its triage input is the threads behind `COMMENT_IDS` — the ones the `comments` route accepted as valid. The invalid ones (misreads, already-addressed, convention-contradicting) never reach here; they take the `--resolve-only` path below.

`tfcp` dispositions each one and returns the buckets along with the short SHA (`$SHA`). Only the `fix` bucket lands in the commit, and only those threads earn a `Done in <sha>` reply:

| tfcp disposition | Thread |
|------------------|--------|
| `fix` | replied with the SHA, resolved (steps 3–4) |
| `residual` | left open — reply the reason it wasn't fixed if it helps the reviewer, but never resolve a thread whose finding wasn't addressed |
| `needs decision` | left open and surfaced to the user with the constraint; it's a design call, not a close-out |

A thread accepted by `comments` but landed `residual` by `tfcp` is a disagreement between the two passes, not a bug — say so in the report rather than resolving it quietly.

`tfcp` owns the hook gate and the push. Any failure there stops this run — do not continue to the reply. See [`tfcp`](../tfcp/SKILL.md).

### 3. Reply

Lead with the SHA so the reviewer can trace the fix. Show the body and confirm before posting — this is outward-facing.

```bash
gh review reply "$PR" --comment "$COMMENT_ID" --body "Done in $SHA — <reply text>"
```

`gh review reply` errors if the comment id isn't a thread on this PR — re-check with `gh review comments "$PR" --ids`.

### 4. Resolve

```bash
gh review resolve "$PR" --comment "$COMMENT_ID"
```

Prints `✓ Resolved thread …` on success.

Repeat steps 3–4 per `--comment` id whose finding landed in the `fix` bucket, reusing the same `$SHA`.

### 5. Report

State the outcome in one line: commit SHA + hook result, push target, the threads replied to and resolved, and any left open with why. e.g. `1f8e3a2 pushed (hooks green) → replied + resolved 3 threads; 1 left open (needs decision: new trait on the store)`.

---

## Resolve-only — dismissed threads

`--resolve-only` closes a thread you're *dismissing*, not fixing (a misread, an already-addressed point, a convention-contradicting suggestion). It skips `tfcp` — there's no fix to commit — and runs only reply + resolve, the `rr` of `(tfcp)rr`:

```bash
gh review reply "$PR" --comment "$COMMENT_ID" --body "<rationale>"
gh review resolve "$PR" --comment "$COMMENT_ID"
```

The reply is the dismissal rationale, posted verbatim — no `Done in <sha>` prefix, since nothing was committed. Rationales differ per thread, so invoke once per dismissed thread with its own `--comment` and `--reply`.

---

## Error Handling

Triage, fix, commit, and push failures are `tfcp`'s — see its table. They stop this run before the reply.

| Condition | Action |
|-----------|--------|
| `--comment` missing | Stop — nothing to reply to or resolve |
| Every `--comment` lands outside `tfcp`'s `fix` bucket | No commit, no SHA — leave the threads open and report the dispositions |
| `--resolve-only` with `-m`/`paths…` | Ignore them — resolve-only never commits |
| No PR for branch and no `--pr` | Stop — report `none` |
| `tfcp` stops (hooks red, push rejected) | Stop — do not reply; the SHA must exist on the remote |
| `reply`/`resolve` reports no thread for the comment | Wrong or already-resolved id — re-check with `gh review comments "$PR" --ids` |
| `gh` not authenticated | Report: run `gh auth login` |

---

## Related Skills

- `tfcp` — the local-review half: triage + fix + commit + push, without the PR thread steps
- `pr comments` — assesses the threads, producing the accepted/dismissed split this consumes
