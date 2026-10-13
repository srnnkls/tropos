---
name: issue
description: GitHub issue operations — author or update issues against a canonical template, and create PRs from a branch/issue. Authoring drafts to a git-ignored `.issues/` folder, clears the default reviewer gate resolved through canonical routing, then publishes with issue type and parent/depends-on/blocks edges. Use for "create an issue", "open an issue", "update issue
metadata:
  type: domain
henia:
  slots:
    issue.template:
  provides:
    issue.template: {section: template}
  targets:
    claude:
      frontmatter:
        argument-hint: '[number|pr] [args]'
        allowed-tools: Bash(gh issue *), Bash(gh pr *), Bash(gh api *), Bash(gh repo view *), Bash(git branch *), Bash(git push *), Bash(git rev-parse *), Bash(git log *), Bash(git merge-base *), Bash(issue *), Bash(peer *)
    codex:
      openai:
        interface:
          display_name: Issue
          short_description: Apply the canonical issue skill workflow
          default_prompt: Use $issue for the requested task.
  variables:
    context_commands:
      - label: Current branch
        command: git branch --show-current 2>/dev/null || true
      - label: Default reviewers
        command: peer defaults reviewers 2>/dev/null || true
      - label: Next issue number (predicted; for the `.issues/` draft filename on **create**)
        command: gh api 'repos/{owner}/{repo}/issues?state=all&per_page=1' --jq '(.[0].number // 0) + 1' 2>/dev/null || echo "?"
---

::::head{context slots="issue.template"}


Publish reconciles the predicted number to the real one. On update, use the edited issue's number.

# Issue Skill

## Slots

| Slot | Covers |
|---|---|
| `issue.template` | Title format, section structure, and type and parent conventions; replaces the [Template](#template) defaults |

:::routes{ordered protocol}
| Pattern | Route | Action |
|---|---|---|
| `pr` (with or without args) | Create PR | Read and follow [operations/pr.md](operations/pr.md) |
| Issue number (`172`, `#172`, "update #172") | Update issue | Fetch with `gh issue view <n>`; [Workflow](#workflow), publish with `issue edit <n>` |
| Anything else (free-text subject, or empty) | Create issue | [Workflow](#workflow), publish with `issue create` |
:::

Resolve the repo with `gh repo view --json nameWithOwner -q .nameWithOwner`, not from the remote URL.

## `issue` helper (the `issue` command)

`issue <subcommand>` (source and GraphQL in `skills/issue/scripts/issue`; `issue help` lists subcommands) resolves the repo and node/type IDs at runtime.

| Endpoint | Does |
|---|---|
| `issue next` | predicted next number |
| `issue draft <n> <type> "<title>"` | create `.issues/`, print the draft path |
| `issue review <n>\|<draft> [--reviewers aliases] [--effort level]` | peer half of the [Review gate](#review-gate-before-publish); mints the report directory via `peer path`, embeds the prompt, fans out |
| `issue create --type T --title … --body-file F [--parent N] [--depends-on L] [--blocks L]` | publish (workflow step 6); prints `<number>\t<url>` |
| `issue verify <n>` | read back type, parent, blockedBy, blocking |
| `issue parent <parent#> <child#>`, `issue depends-on <n> <dep#,…>`, `issue blocks <n> <target#,…>` | set one edge (`addSubIssue` / `addBlockedBy`) |
| `issue set-type <n> "<Type>"`, `issue type-id "<Type>"`, `issue node <n>` | set type; look up type / node IDs |
| `issue purge [<n>]` | `trash` drafts in `.issues/` and reports in `.peer/issue-*` (all, or one issue's) |

Requires `issue`, `peer`, authenticated `gh`; the review gate also needs `peer route sync` routes and authenticated peer harnesses.

## Template

- Sections: [`references/template.md`](references/template.md).
- Title: `<Module> — <short summary>`, em-dash (—).
- Type and parent: [Choosing the type](#choosing-the-type), [Choosing the parent](#choosing-the-parent).

## Workflow

1. Read the `issue.template` providers. Orient per [AGENTS.md](../../instructions/AGENTS.md#tools-and-context) and [match the repo](references/sketches.md#the-one-rule-match-the-repo), including its layering.
2. Draft the body and title per the template; sketches per [`references/sketches.md`](references/sketches.md).
3. Settle type, parent, and depends-on / blocks per [Issue metadata](#issue-metadata-type-parent-dependencies) before submitting. On update, read existing metadata with `issue verify <n>`; change only what the user asked.
4. Draft into `.issues/<n>-<type>-<slug>.md` via `issue draft <n> <type> "<title>"`; never `$TMPDIR`. `.issues/` holds drafts only; if `issue draft` warns it is not git-ignored, ignore it in a local excludes file, not `.gitignore`.
   - Create: `<n>` from `issue next`.
   - Update: save the live body first, `gh issue view <n> --json body -q .body > ".issues/<n>-<type>-<slug>.orig.md"`; when rewriting, show `diff ".issues/<n>-<type>-<slug>.orig.md" ".issues/<n>-<type>-<slug>.md"` before the gate.
5. Clear the [Review gate](#review-gate-before-publish).
6. Publish, then `issue verify <number>`:
   - Create: `issue create --type "<Feature|Task>" --title "..." --body-file ".issues/<next>-<type>-<slug>.md" [--parent <n>] [--depends-on <a,b>] [--blocks <c,d>]`. It renames the draft and `.peer/issue-<predicted>/` to the real number before applying edges.
   - Update: `issue edit <n> [--type "<Feature|Task>"] --body-file ".issues/<n>-<type>-<slug>.md" [--parent …] [--depends-on …] [--blocks …]`.
7. Apply edges not passed at publish with `issue parent` / `issue depends-on` / `issue blocks`.
8. When done, `issue purge [<n>]`. Report-directory and Git-state behavior: [`peer path` interface](../peer/SKILL.md#report-layout--peer).

## Review gate (before publish)

Publish nothing until the ensemble clears the [result gate](../review/reference/harnesses.md#results). Ensemble, overrides, compatibility, effort, and execution: [peer routing contract](../peer/reference/routing.md); registry, dispatch, and harness auth: `$peer`.

1. Use the complete `peer defaults reviewers` ensemble unless the caller supplied a reviewer configuration.
2. In one message, dispatch `native` and `native-proxy` entries through the host and one backgrounded `issue review <full draft path>` for the `peer` entries (`--reviewers` for an explicit subset). An unavailable required execution class blocks the gate.
3. Give every reviewer the same embedded draft, canonical template, criteria, exact [reviewer report schema](../review/reference/report.md#reviewer-report), and verbatim [finding bar](../review/reference/finding-bar.md).
4. Read every successful report (malformed = unsuccessful); apply the finding bar, result gate, and [review synthesis](../review/reference/synthesis.md).
5. Fold admitted blocking findings into the draft and re-run the whole gate under canonical synthesis limits; each round mints a fresh `<run>`.

::::

## Issue metadata (type, parent, dependencies)

Set type, parent, and depends-on / blocks (`A depends on B` = `B blocks A`) only on GitHub's native fields via `issue` flags or subcommands, never as body lines or sections. Never hardcode type or node IDs.

### Choosing the type

- Feature — user-facing capability or slice of behavior with value on its own.
- Task — implementation unit under a parent Feature (or Initiative).
- Bug / Initiative — only on explicit request.

Unstated type: `AskUserQuestion` with header `"Issue type"`, options `Feature` and `Task`; never infer it from the body.

### Choosing the parent

Features sit under an Initiative or at top level; Tasks under a Feature. The parent is a sub-issue relationship (`addSubIssue` GraphQL mutation).

Unstated parent (never set one the user has not confirmed):

- Task: `AskUserQuestion` pre-seeded from `gh issue list --state open --search "type:Feature" --json number,title --limit 20`; offer `No parent` only when context suggests a standalone Task.
- Feature: ask for a parent Initiative; default `No parent` when the repo has no open Initiative.

### Choosing depends-on / blocks

Depends on: this issue cannot start/merge until the referenced one lands. Blocks: the reverse. Set each edge once, in the user's direction.

- User said "depends on #N" / "blocks #N": set it without asking.
- Sketch references prior or future work: `AskUserQuestion` with questions `"Depends on"` and `"Blocks"`, option `None`, free text allowed. Never derive edges from the body alone.
- Trivial standalone issues: do not ask.

### Raw mutations

For operations `issue` lacks:

| Mutation | Arguments |
|---|---|
| `updateIssueIssueType` | `issueId`, `issueTypeId` (`null` clears the type) |
| `addSubIssue` / `removeSubIssue` | `issueId` = parent, `subIssueId` = child; `replaceParent: true` moves a child |
| `addBlockedBy` / `removeBlockedBy` | `issueId` = blocked side, `blockingIssueId` = blocker; `A blocks B` → `issueId` = B; remove when an updated issue's dependencies changed |

### Verifying after submit

Run `issue verify <number>` and report issue URL, type, parent, depends-on (`blockedBy`), blocks (`blocking`). If a requested relationship did not resolve, stop and ask the user.

## Companion skills

- `$git` — branch naming, commit prefixes.
- `$review` — review checklist for drafts.

:::references
- [operations/pr.md](operations/pr.md) — create a PR from the current branch, optionally linked to an issue.
- [`references/template.md`](references/template.md) — section-by-section template structure.
- [`references/sketches.md`](references/sketches.md) — patterns and anti-patterns for implementation sketches.
:::
