---
name: pr
description: GitHub PR review-comment operations. `comments` assesses each review comment (relevant vs outdated, valid vs invalid) and proposes an action; `fcprr` closes the threads you've addressed (fix + commit + push + reply + resolve) by delegating to the `fcprr` skill. Use for "pr comments", "assess PR feedback", "review PR comments", "reply to a PR comment", "resolve a thread", or "fcprr".
argument-hint: "[comments [N] | fcprr <args>]"
allowed-tools: Bash(gh api *), Bash(gh pr *), Bash(gh review *), Bash(gh repo view *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
metadata:
  type: domain
---

## Pre-loaded Context

PR comment context, fetched at skill-load for the `comments` route. The PR is `$ARGUMENTS` (a bare number, or after a leading `comments` token) or the current branch's PR. Each block is fail-safe: with no PR resolvable it prints `no-pr`. The `fcprr` route skips these blocks — it delegates to the `fcprr` skill via [operations/fcprr.md](operations/fcprr.md).

> Dynamic `!` blocks only execute in this SKILL.md, not in Read-loaded operation files — which is why the comment fetch lives here, not in an operation.

These are inline `!` blocks (single-line, like the role-model skill) — the form proven to expand `$ARGUMENTS` at load. Each re-resolves the PR independently and skips the `fcprr` route.

PR metadata:
!`A="$ARGUMENTS"; case "$A" in fcprr*) exit 0;; esac; case "$A" in comments) A="";; "comments "*) A="${A#comments }";; esac; PR="${A%% *}"; [ -z "$PR" ] && PR=$(gh pr view --json number -q .number 2>/dev/null); [ -z "$PR" ] && { echo no-pr; exit 0; }; gh pr view "$PR" --json number,title,state,headRefName,headRefOid,baseRefName,url 2>/dev/null || echo no-pr`

Inline review comments (node_id feeds `fcprr --comment`; original_line anchors the relevant-vs-outdated check):
!`A="$ARGUMENTS"; case "$A" in fcprr*) exit 0;; esac; case "$A" in comments) A="";; "comments "*) A="${A#comments }";; esac; PR="${A%% *}"; [ -z "$PR" ] && PR=$(gh pr view --json number -q .number 2>/dev/null); [ -z "$PR" ] && { echo no-pr; exit 0; }; REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null); gh api "repos/$REPO/pulls/$PR/comments" --paginate --jq '.[] | {node_id, user: .user.login, path, line, original_line, side, in_reply_to_id, body}' 2>/dev/null || echo no-pr`

Thread resolution map (unresolved head comments with their node ids; resolved threads collapse, don't re-litigate):
!`A="$ARGUMENTS"; case "$A" in fcprr*) exit 0;; esac; case "$A" in comments) A="";; "comments "*) A="${A#comments }";; esac; PR="${A%% *}"; [ -z "$PR" ] && PR=$(gh pr view --json number -q .number 2>/dev/null); [ -z "$PR" ] && { echo no-pr; exit 0; }; gh review comments "$PR" --unresolved --ids --flat 2>/dev/null | head -60 || true`

Review bodies and conversation comments (not line-anchored):
!`A="$ARGUMENTS"; case "$A" in fcprr*) exit 0;; esac; case "$A" in comments) A="";; "comments "*) A="${A#comments }";; esac; PR="${A%% *}"; [ -z "$PR" ] && PR=$(gh pr view --json number -q .number 2>/dev/null); [ -z "$PR" ] && { echo no-pr; exit 0; }; REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null); echo "== review bodies =="; gh api "repos/$REPO/pulls/$PR/reviews" --jq '.[] | select(.body != "") | {user: .user.login, state, body}' 2>/dev/null; echo "== conversation =="; gh api "repos/$REPO/issues/$PR/comments" --jq '.[] | {user: .user.login, body}' 2>/dev/null`

HEAD diff:
!`A="$ARGUMENTS"; case "$A" in fcprr*) exit 0;; esac; case "$A" in comments) A="";; "comments "*) A="${A#comments }";; esac; PR="${A%% *}"; [ -z "$PR" ] && PR=$(gh pr view --json number -q .number 2>/dev/null); [ -z "$PR" ] && { echo no-pr; exit 0; }; gh pr diff "$PR" 2>/dev/null | head -800 || echo no-pr`

If a block printed `no-pr`, ask the user for the PR number before continuing.

# PR Skill

Two operations on a pull request's review feedback:

- **`comments`** — assess every review comment and say what to do about it.
- **`fcprr`** — close the addressworthy threads: fix + commit + push + reply + resolve. Delegates to the `fcprr` skill.

Requires the `gh-review` extension (`gh extension install srnnkls/gh-review`), exposed as `gh review`.

> **Protocol:** [../dispatch/protocol.md](../dispatch/protocol.md)

---

## Auto-Detect Rules

Apply to `$ARGUMENTS` in order, first match wins:

| Pattern | Route | Action |
|---|---|---|
| `fcprr` (with or without args) | Close addressed threads | Read and follow [operations/fcprr.md](operations/fcprr.md) |
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

- **Accepted** threads route through the full `fcprr` (fix + commit + push + reply + resolve): invoke Skill `fcprr` with `--comment <node_id>` per accepted thread, plus `--reply` and `-m`. It applies the fixes, commits and pushes once, then replies to and resolves each thread.
- **Dismissed** threads route through `fcprr --resolve-only` — no fix, commit, or push: reply with the dismissal rationale and resolve. When the verdict is *all dismiss* (nothing to address), this resolve-only pass is the whole close-out.

Threads you defer or flag needs-discussion stay open. See [operations/fcprr.md](operations/fcprr.md).

---

## `fcprr` — close the addressed threads

**f**ix + **c**ommit + **p**ush + **r**eply + **r**esolve, over every addressworthy comment. Delegates to the `fcprr` skill; see [operations/fcprr.md](operations/fcprr.md).

Order is load-bearing — the fixes land first, the commit must pass hooks before the push, the push must land before the reply (so the referenced SHA exists on the remote), and the reply precedes the resolve. A failure at any step stops the rest.

Dismissed threads take the `--resolve-only` path — the `rr` of `(fcp)rr` — skipping fix, commit, and push: reply the rationale, resolve.

---

## Related Skills

- `review pr` — interactive review of a PR (draft comments, submit a verdict)
- `issue pr` — open a PR for the current branch
- `git` — branch and commit workflows
