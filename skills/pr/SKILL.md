---
name: pr
description: GitHub PR review-comment operations. `comments` assesses each review comment (relevant vs outdated, valid vs invalid) and proposes an action; `tfcprr` closes the threads you've addressed (tfcp — triage + fix + commit + push — then reply + resolve) by delegating to the `tfcprr` skill. Use for "pr comments", "assess PR feedback", "review PR comments", "reply to a PR comment", "resolve a thread", or "tfcprr".
argument-hint: "[comments [N] | tfcprr <args>]"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/pr-context), Bash(${CLAUDE_SKILL_DIR}/scripts/pr-context *), Bash(gh api *), Bash(gh pr *), Bash(gh review *), Bash(gh repo view *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
metadata:
  type: domain
---

## Pre-loaded Context

PR comment context, fetched at skill-load for the `comments` route. The PR is `$ARGUMENTS` (a bare number, or after a leading `comments` token) or the current branch's PR. Each block is fail-safe: with no PR resolvable it prints `no-pr`. The `tfcprr` route skips these blocks — it delegates to the `tfcprr` skill via [operations/tfcprr.md](operations/tfcprr.md).

> Dynamic `!` blocks only execute in this SKILL.md, not in Read-loaded operation files — which is why the comment fetch lives here, not in an operation.

All shell lives in [scripts/pr-context](scripts/pr-context). `${CLAUDE_SKILL_DIR}` is substituted in both the block below and the `allowed-tools` rule, so the rule matches the command verbatim and the fetch runs without a permission check.

!`${CLAUDE_SKILL_DIR}/scripts/pr-context $ARGUMENTS`

Sections, in order: `== pr ==` (metadata), `== inline comments ==` (`node_id` feeds `tfcprr --comment`, `original_line` anchors the relevant-vs-outdated check), `== unresolved threads ==` (resolved threads collapse — don't re-litigate), `== review bodies ==` and `== conversation ==` (not line-anchored), `== diff ==` (HEAD, first 800 lines).

On the `tfcprr` route the script exits silently. If it printed `no-pr`, ask the user for the PR number, then re-run `${CLAUDE_SKILL_DIR}/scripts/pr-context comments <number>` via Bash.

# PR Skill

Two operations on a pull request's review feedback:

- **`comments`** — assess every review comment and say what to do about it.
- **`tfcprr`** — close the addressworthy threads: `tfcp` (triage + fix + commit + push), then reply + resolve. Delegates to the `tfcprr` skill.

Requires the `gh-review` extension (`gh extension install srnnkls/gh-review`), exposed as `gh review`.

> **Protocol:** [../dispatch/protocol.md](../dispatch/protocol.md)

---

## Auto-Detect Rules

Apply to `$ARGUMENTS` in order, first match wins:

| Pattern | Route | Action |
|---|---|---|
| `tfcprr` (with or without args) | Close addressed threads | Read and follow [operations/tfcprr.md](operations/tfcprr.md) |
| `comments`, a bare PR number, or empty | Assess comments | This file — `comments` below |

---

## `comments` — assess review feedback

Work from the pre-loaded context above. For each **inline review comment**, in file → line order:

1. **Relevant vs outdated** — locate `path:original_line` at HEAD (`headRefOid`) using the diff. Outdated if the cited hunk was removed or rewritten beyond recognition; otherwise still relevant.
2. **Valid vs invalid** — judge against the *current* code, not the snapshot the reviewer saw:
   - *Valid*: the concern still applies and the suggestion is correct.
   - *Invalid*: a misread, already addressed, or contradicts the repo's own conventions (`CLAUDE.md` / `AGENTS.md` / `STYLE.md`, and any project review skill).
3. **Structural view (optional)** — if the project ships a structural-review skill (e.g. an `effect` / `lens` skill), run it on the cited file and map the reviewer's concern onto it; quote the canonical citation, else "no finding at this line". Skip if no such skill exists.

Resolved threads (from the resolution map) and replies (`in_reply_to_id`) collapse with their parent — assess the thread, not each turn.

**Review bodies** (`== review bodies ==`) and **conversation comments** (`== conversation ==`) are not line-anchored: skip step 1 and assess relevant-vs-valid against the PR as a whole, grouped under a `PR-level` heading. A body that only restates the diff or carries no finding (bot overviews, sunset notices) is dismissed, not deferred.

### Output

One block per comment, grouped by file:

```
<path>:<line>  @<reviewer>  [Relevant|Outdated] [Valid|Invalid]
  Comment:   <one-line gist>
  Current:   <what HEAD shows | "removed">
  Action:    accept | reject | defer | needs-discussion
```

Close with a two-bullet verdict: comments to address, comments to dismiss.

Once the verdict is set, close every unresolved thread in one pass — no relevant thread is left open, whether or not anything was addressed:

- **Accepted** threads route through the full `tfcprr` (tfcp + reply + resolve): invoke Skill `tfcprr` with `--comment <node_id>` per accepted thread, plus `--reply` and `-m`. It triages the accepted set, applies and pushes the fixes in one commit, then replies to and resolves each thread it fixed — a thread its triage lands `residual` or `needs decision` stays open.
- **Dismissed** threads route through `tfcprr --resolve-only` — no fix, commit, or push: reply with the dismissal rationale and resolve. When the verdict is *all dismiss* (nothing to address), this resolve-only pass is the whole close-out.

Threads you defer or flag needs-discussion stay open. See [operations/tfcprr.md](operations/tfcprr.md).

---

## `tfcprr` — close the addressed threads

*tfcp* (triage + fix + commit + push) + *r*eply + *r*esolve, over every addressworthy comment. Delegates to the `tfcprr` skill, which runs the `tfcp` skill for the first four steps; see [operations/tfcprr.md](operations/tfcprr.md).

Order is load-bearing — triage decides what gets touched, `tfcp` must land the commit on the remote before the reply names its SHA, and the reply precedes the resolve. A failure at any step stops the rest.

Dismissed threads take the `--resolve-only` path — the `rr` of `(tfcp)rr` — skipping triage, fix, commit, and push: reply the rationale, resolve. Your `comments` verdict already dispositioned them.

---

## Related Skills

- `review pr` — interactive review of a PR (draft comments, submit a verdict)
- `issue pr` — open a PR for the current branch
- `git` — branch and commit workflows
