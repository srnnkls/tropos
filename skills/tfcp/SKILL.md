---
name: tfcp
description: Land the fixes for a local review — triage, fix, commit, push. Dispositions every finding of a code review (in-context or from a `.peer/` report directory) as fix, residual, or needs-decision, applies the fix bucket, commits once behind the hook gate, and pushes. Use for "tfcp", "triage the review findings", "apply the review findings", "fix and push the review issues"; `tfcprr` composes on it for PR threads.
argument-hint: "[--issue <id>…] [--report <path>] [-m <msg>] [paths…]"
allowed-tools: Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git status *), Bash(git rev-parse *), Bash(git branch *)
metadata:
  type: domain
---

# tfcp — triage + fix + commit + push

Land the findings of a local review: give every finding a disposition, apply the ones that clear, commit behind the hook gate, push.

The four steps are strictly ordered. Each gates the next:

1. *triage* — disposition every finding as `fix`, `residual`, or `needs decision`. Verdicts only; no file is touched here.
2. *fix* — apply the `fix` bucket, and only it.
3. *commit* — fails if pre-commit hooks (lint, typecheck, tests) are red → stop, surface the output, fix, retry.
4. *push* — publishes the commit; anything downstream that names the SHA needs it on the remote first.

A failure at any step stops the rest. Never report a fix as landed when the commit or push didn't.

Everything addressed in one run rides one commit: the fix set is applied together, then committed and pushed once.

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--issue <id>` | every finding | Restrict triage input to specific finding ids (`C1`, `H2`, …) from the synthesized report; repeat once per finding. |
| `--report <path>` | findings in context | Synthesized report or `.peer/<subject>/<run>/<stage>/` report directory to read findings from when they aren't already in the conversation. |
| `-m, --message <text>` | derived | Commit message (conventional commit format). |
| `[paths…]` | already-staged | Files to stage before committing. With none, commits whatever is already staged. |

---

## Workflow

### 1. Triage

Findings come from the review already in context, or from `--report <path>` (a synthesized report, or a `.peer/<subject>/<run>/<stage>/` directory of per-reviewer reports — see [`review` reference/report.md](../review/reference/report.md)). `--issue <id>` narrows the input set.

A synthesized report arrives pre-dispositioned: its `issues:` are `fix`, its `residual:` entries stay residual, and a `suggestion` prefixed `needs decision:` is `needs decision`. Carry those verdicts — a run that re-argues them is a refinement spiral, not a fix round. Raw findings — an in-context review, a reviewer's report you're reading directly — get dispositioned here against the [finding bar](../review/reference/finding-bar.md).

Every finding lands in exactly one bucket, judged against the [finding bar](../review/reference/finding-bar.md) — which owns the criteria; triage only sorts by them:

| Disposition | Test | Outcome |
|-------------|------|---------|
| `fix` | clears the bar's admission test — a reachable trigger *and* the wrong outcome the change removes | step 2 |
| `residual` | fails it, by the bar's out-of-bounds rules (this is where a narrower variant of an already-fixed finding lands, unless it names a trigger that fix left reachable) | not fixed, reported in step 5 |
| `needs decision` | removing the failure mode takes new API surface, a new type, or a signature change | back to the user with the constraint that forces it — never invent the design to close it |

Unsure between `fix` and `residual` means it isn't a `fix`. A finding you can't disposition at all is `needs decision` when a design call is what's missing, `residual` otherwise — never an unlabelled edit.

State the dispositions before touching a file. That table is what step 2 is permitted to change; anything outside the `fix` bucket gets no edit.

Stop here — no fix, no commit — when nothing is triageable (ask which review to work from), when `--issue` matches no finding, or when the `fix` bucket comes out empty (report the dispositions instead).

### 2. Fix — apply the triaged subset

Apply the `fix` bucket, whole set, before committing. Whatever lands in the working tree here is what the commit message describes. If the fixes are already applied, skip to staging.

Each fix is the smallest change at the shared root, not per caller. Hardening the finding doesn't name is out of scope — that ambition is `residual`, not a bonus.

### 3. Stage and commit

Inspect what's staged, then commit. Confirm it's the fixes and nothing unrelated.

```bash
git status --short          # confirm the staged set
git add <paths…>            # skip if already staged
git commit -m "<message>"
```

Message: conventional commit format (`<type>(<scope>): <description>`), imperative and lowercase, describing the fix.

*Hooks gate this step.* If the commit fails (hooks red), stop — report the failing output, fix, and retry. Do not proceed to push.

Capture the short SHA — it's this skill's return value:

```bash
SHA=$(git rev-parse --short HEAD)
```

### 4. Push

```bash
git push                    # or: git push -u origin <branch> on first push
```

If the push fails (e.g. non-fast-forward), stop and reconcile before claiming the commit landed.

### 5. Report

One line, and it carries the whole triage — what was fixed, and what wasn't and why. e.g. `C1, H2 fixed → 1f8e3a2 pushed (hooks green); M4 residual (no reachable trigger), H3 needs decision (new trait on the store)`.

A `needs decision` finding is the user's next move, so it never gets buried under the SHA.

---

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

---

## Related Skills

- `tfcprr` — the PR variant: this chain, then reply to and resolve each review thread
- `review` / `code review` — produces the findings this operates on
