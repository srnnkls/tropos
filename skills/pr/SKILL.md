---
name: pr
description: GitHub PR review operations. `review` reviews a PR interactively — draft line comments, submit a verdict; `comments` assesses each review comment (relevant vs outdated, valid vs invalid) and proposes an action; `tfcprr` closes the threads you've addressed (tfcp — triage + fix + commit + push — then reply + resolve) by delegating to the `tfcprr` skill. Use for "review PR <n>", "pr comments", "assess PR feedback", "review PR comments", "reply to a PR comment", "resolve a thread", or "tfcprr".
metadata:
  type: domain
henia:
  targets:
    claude:
      frontmatter:
        argument-hint: '[review [N] | comments [N] | tfcprr <args>]'
        allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/pr-context), Bash(${CLAUDE_SKILL_DIR}/scripts/pr-context *), Bash(gh api *), Bash(gh pr *), Bash(gh review *), Bash(gh issue view *), Bash(gh repo view *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
    codex:
      openai:
        interface:
          display_name: Pr
          short_description: Apply the canonical pr skill workflow
          default_prompt: Use $pr for the requested task.
---

::::head{context slots="review.criteria"}

All other shell lives in [scripts/pr-context](scripts/pr-context), resolved against this skill's directory.

!`scripts/pr-context $ARGUMENTS`

Slot providers: the `review.criteria` providers; see [review slots](../review/SKILL.md#slots). Script sections, in order: `== pr ==` (metadata), `== inline comments ==` (`node_id` feeds `tfcprr --comment`; `original_line` anchors the outdated check), `== unresolved threads ==` (resolved threads collapse; don't re-litigate), `== review bodies ==` and `== conversation ==` (not line-anchored), `== diff ==` (HEAD, first 800 lines). The `review` route adds `== review context ==` (body, size, files, commits) and `== pending drafts ==` after `== pr ==`.

On the `tfcprr` route the script exits silently. If it printed `no-pr`, ask for the PR number and re-run with the route and `<number>`.

# PR Skill

Requires the `gh-review` extension (`gh extension install srnnkls/gh-review`), exposed as `gh review`.

:::routes{ordered protocol}
| Pattern | Route | Action |
|---|---|---|
| `tfcprr` (with or without args) | Close addressed threads | Read and follow [operations/tfcprr.md](operations/tfcprr.md) |
| `review` with or without a PR number or URL | Review a PR | Read and follow [operations/review.md](operations/review.md) |
| `comments`, a bare PR number, or empty | Assess comments | This file — `comments` below |
:::

## `comments` — assess review feedback

From the pre-loaded context, per inline review comment in file → line order:

1. Relevant vs outdated — locate `path:original_line` at HEAD (`headRefOid`) in the diff. Outdated if the hunk was removed or rewritten beyond recognition.
2. Valid vs invalid, judged against current code. Valid: the concern still applies and the suggestion is correct. Invalid: a misread, already addressed, or contradicts `CLAUDE.md` / `AGENTS.md` / `STYLE.md` or the listed `review.criteria` providers.
3. Review criteria — when providers are listed, map the concern onto them for the cited file; quote the canonical citation, else "no finding at this line".

Assess a thread once: resolved threads and replies (`in_reply_to_id`) collapse into their parent.

Review bodies and conversation comments: skip step 1, assess against the whole PR under a `PR-level` heading. Dismiss (not defer) a body that only restates the diff or carries no finding.

### Output

One block per comment, grouped by file:

```
<path>:<line>  @<reviewer>  [Relevant|Outdated] [Valid|Invalid]
  Comment:   <one-line gist>
  Current:   <what HEAD shows | "removed">
  Action:    accept | reject | defer | needs-discussion
```

Close with a two-bullet verdict: comments to address, comments to dismiss. Then close every unresolved thread in one pass via [operations/tfcprr.md](operations/tfcprr.md):

- Accepted: invoke Skill `tfcprr` with `--comment <node_id>` per thread, plus `--reply` and `-m`.
- Dismissed: `tfcprr --resolve-only` per thread. With nothing to address, this is the whole close-out.
- Deferred and needs-discussion threads stay open.

::::

:::related
- `review` — local and scope review; routes PR targets here
- `issue` — open a PR for the current branch
- `git` — branch and commit workflows
:::
