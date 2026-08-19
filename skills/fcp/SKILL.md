---
name: fcp
description: Land the fixes for a local review — fix, commit, push. Applies the fix for every confirmed finding of a code review (in-context or from a `.reviews/<slug>/` report), commits once behind the hook gate, and pushes. Use for "fcp", "apply the review findings", "fix and push the review issues"; `fcprr` composes on it for PR threads.
argument-hint: "[--issue <id>…] [--report <path>] [-m <msg>] [paths…]"
allowed-tools: Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git status *), Bash(git rev-parse *), Bash(git branch *)
metadata:
  type: domain
---

# fcp — fix + commit + push

Land the findings of a local review: apply the fixes, commit them behind the hook gate, push.

The three steps are strictly ordered. Each gates the next:

1. **fix** — apply the change that addresses the finding.
2. **commit** — fails if pre-commit hooks (lint, typecheck, tests) are red → stop, surface the output, fix, retry.
3. **push** — publishes the commit; anything downstream that names the SHA needs it on the remote first.

A failure at any step stops the rest. Never report a fix as landed when the commit or push didn't.

Everything addressed in one run rides **one commit**: the fix set is applied together, then committed and pushed once.

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--issue <id>` | every confirmed finding | Restrict to specific finding ids (`C1`, `H2`, …) from the synthesized report; repeat once per finding. |
| `--report <path>` | findings in context | Synthesized report or `.reviews/<slug>/` directory to read findings from when they aren't already in the conversation. |
| `-m, --message <text>` | derived | Commit message (conventional commit format). |
| `[paths…]` | already-staged | Files to stage before committing. With none, commits whatever is already staged. |

---

## Workflow

### 1. Resolve the fix set

The findings come from the review already in context, or from `--report <path>` (a synthesized report, or a `.reviews/<slug>/` directory of per-reviewer reports — see [`review` reference/report.md](../review/reference/report.md)).

Address every **confirmed** finding — the entries under `issues:`, which cleared triage. Entries under `residual:` were ruled out and are not fixed. `--issue <id>` narrows that set further.

With no findings resolvable, stop and ask which review to work from.

### 2. Fix

Apply the fixes for the whole set before committing. Whatever lands in the working tree here is what the commit message describes. If the fixes are already applied, skip to staging.

### 3. Stage and commit

Inspect what's staged, then commit. Confirm it's the fixes and nothing unrelated.

```bash
git status --short          # confirm the staged set
git add <paths…>            # skip if already staged
git commit -m "<message>"
```

Message: conventional commit format (`<type>(<scope>): <description>`), imperative and lowercase, describing the fix.

**Hooks gate this step.** If the commit fails (hooks red), stop — report the failing output, fix, and retry. Do not proceed to push.

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

One line: the findings addressed, commit SHA + hook result, push target. e.g. `C1, H2 fixed → 1f8e3a2 pushed (hooks green)`.

---

## Error Handling

| Condition | Action |
|-----------|--------|
| No findings in context and no `--report` | Stop — ask which review to work from |
| `--issue <id>` matches no finding | Stop — list the available ids |
| Nothing staged and no `paths…` | Stop — the fix never landed in the working tree |
| Commit fails (hooks red) | Stop, surface hook output, fix, retry; do not push |
| Push rejected (non-fast-forward) | Stop, reconcile (pull/rebase), retry; do not report as landed |
| No upstream for the branch | `git push -u origin <branch>` |

---

## Related Skills

- `fcprr` — the PR variant: this chain, then reply to and resolve each review thread
- `review` / `code review` — produces the findings this operates on
