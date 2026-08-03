---
name: issue
description: GitHub issue operations — author or update issues against a canonical template, and create PRs from a branch/issue. Authoring drafts to a git-ignored `.issues/` folder, clears a host-aware four-report gate (two host-native and two cross-host peer reviewers), then publishes with issue type and parent/depends-on/blocks edges. Use for "create an issue", "open an issue", "update issue #N", "draft/sketch issue for X", "file an issue", or "pr" to open a pull request.
argument-hint: "[number|pr] [args]"
allowed-tools: Bash(gh issue *), Bash(gh pr *), Bash(gh api *), Bash(gh repo view *), Bash(git branch *), Bash(git push *), Bash(git rev-parse *), Bash(git log *), Bash(git merge-base *), Bash(issue *)
metadata:
  type: domain
---

## Pre-loaded Context

Current branch:
!`git branch --show-current 2>/dev/null || true`

Next issue number (predicted; for the `.issues/` draft filename on **create**):
!`gh api 'repos/{owner}/{repo}/issues?state=all&per_page=1' --jq '(.[0].number // 0) + 1' 2>/dev/null || echo "?"`

GitHub shares one number sequence across issues and PRs. This is a best-effort prediction — the draft filename is reconciled to the real number after publish (step 8). On update, the number is the issue you're editing.

# Issue Skill

Authoring and updating GitHub issues against a canonical template, plus PR creation from the current branch.

> **Protocol:** [../dispatch/protocol.md](../dispatch/protocol.md)

---

## Auto-Detect Rules

Apply to `$ARGUMENTS` in order, first match wins:

| Pattern | Route | Action |
|---|---|---|
| `pr` (with or without args) | Create PR | Read and follow [operations/pr.md](operations/pr.md) |
| Issue number (`172`, `#172`, "update #172") | Update issue | This file — Mode dispatch → update |
| Anything else (free-text subject, or empty) | Create issue | This file — Mode dispatch → create |

---

## Mode dispatch

- **No issue number** → create a new issue (`issue create`).
- **Issue number provided** (`172`, `#172`, "update #172") → fetch with `gh issue view <n>`, edit the body in place with `issue edit <n>`.

Resolve the repo via `gh repo view --json nameWithOwner -q .nameWithOwner` rather than parsing the remote URL.

## `issue` helper (the `issue` command)

The gh/GraphQL plumbing is wrapped by the **`issue` command** (on PATH via `mise run install-issue`; source `skills/issue/scripts/issue`). Invoke it as `issue <subcommand>`; `issue help` lists them. It resolves the repo and looks up node/type IDs at runtime. Endpoints:

| Endpoint | Does |
|---|---|
| `issue next` | predicted next number (the [Pre-loaded Context](#pre-loaded-context) one-liner) |
| `issue draft <n> <type> "<title>"` | ensure `.issues/`, print `.issues/<n>-<type>-<slug>.md` |
| `issue review <n>\|<draft> [--reviewers aliases] [--effort level]` | external half of the four-report gate through `peer --agent reviewer`; host-native reports stay agent-native |
| `issue create --type T --title … --body-file F [--parent N] [--depends-on L] [--blocks L]` | publish, auto-reconcile the draft filename to the real number, apply parent/dependency edges; prints `<number>\t<url>` |
| `issue edit <n> [--type T] [--body-file F] [--parent N] [--depends-on L] [--blocks L]` | update body/type + edges |
| `issue verify <n>` | read-back (type, parent, blockedBy, blocking) |
| `issue purge [<n>]` | `trash` `.issues/` contents (all, or one issue's drafts+reviews) |

The raw `gh api graphql` mutations are documented below as the reference the wrapper implements.

## Workflow

1. **Read the template structure.** Consult [`references/template.md`](references/template.md) for the section list, header ordering, and what each section must contain.
2. **Orient in the target repo before sketching.** Before drafting implementation sketches, learn the repo's existing idioms so sketches match rather than impose a stack:
   - `gestalt map` / `gestalt analyze` for structure, hotspots, and seams.
   - `/loqui` for language-specific patterns and style.
   - Read `CLAUDE.md` / `AGENTS.md` and a couple of neighbouring modules for naming, error handling, and layering conventions.
3. **Draft the issue body.** Use the section order in `references/template.md`. For implementation sketches, follow [`references/sketches.md`](references/sketches.md) — illustrative shapes (signatures, not bodies) written in the repo's own idioms.
4. **Title format.** `<Module> — <short summary>` with an em-dash (—), not a hyphen. Examples: `Discovery — dependency traversal from activities to tables`, `Catalog — migration catalog with priority, stats, and export`.
5. **Determine issue type, parent, and dependencies (depends-on / blocks) before submitting** (see [Issue metadata](#issue-metadata-type-parent-dependencies) below). If the user hasn't specified type or parent, ask via `AskUserQuestion` — don't guess. Ask about depends-on / blocks only when the body sketch hints at sequencing between issues; skip for standalone work. For updates, inspect the existing metadata first via `gh api graphql` and only change what the user asked to change.
6. **Draft to the local `.issues/` folder** (repo-local, git-ignored — never `$TMPDIR`, the draft and its reviews persist there). Name the file `<issue-number>-<type>-<slug>.md` — e.g. `745-feature-discovery-dependency-traversal.md` (`<type>` is `feature`/`task` lowercase; `<slug>` is the kebab-cased title). `issue draft <n> <type> "<title>"` prints the path and creates `.issues/`.
   - Create: use the next issue number from `issue next`. Draft the body into `.issues/<next>-<type>-<slug>.md`.
   - Update: the number is the issue you're editing. Preserve the live body first — `gh issue view <n> --json body -q .body > ".issues/<n>-<type>-<slug>.orig.md"` — then draft into `.issues/<n>-<type>-<slug>.md`. Surface a diff (`diff ".issues/<n>-<type>-<slug>.orig.md" ".issues/<n>-<type>-<slug>.md"`) before the gate if rewriting an existing body.
7. **Review gate (mandatory four reports) — run before any publish.** The drafted body must clear two host-native reviews and two cross-host peer reviews before it reaches GitHub. Detect the current host, validate the external aliases with live `peer list` metadata, and dispatch all four in one message (see [Review gate](#review-gate-four-reports-before-publish) below):
   - **Codex host** — spawn two independent `codex-native` reviewer subagents with inherited session settings, plus `issue review ".issues/<n>-<type>-<slug>.md" --reviewers opus-cli,sonnet-cli --effort high`.
   - **Claude host** — spawn native reviewer Tasks on `opus` and `sonnet`, plus `issue review ".issues/<n>-<type>-<slug>.md" --reviewers gpt,terra --effort high`.
   - **Other host** — block before review or publish: this fixed gate requires one of the two supported native subagent mechanisms.

   Pass the **draft path**, not the bare number — a bare number globs `.issues/<n>-*.md` and errors if more than one draft shares that number. Never replace the prescribed native family with its same-host CLI peer; if a required alias or native mechanism is unavailable, stop and report it.

   Read all four reports, fold blocking findings back into the draft, and re-run the gate until it passes. **Do not publish until the gate passes.**
8. **Publish (auto-reconciles the number).** `issue create` runs `gh issue create --type`, then renames the draft (and its `-reviews/` dir) to the real number before applying edges.
   - Create: `issue create --type "<Feature|Task>" --title "..." --body-file ".issues/<next>-<type>-<slug>.md" [--parent <n>] [--depends-on <a,b>] [--blocks <c,d>]` → prints `<number>\t<url>`.
   - Update: `issue edit <n> [--type "<Feature|Task>"] --body-file ".issues/<n>-<type>-<slug>.md" [--parent …] [--depends-on …] [--blocks …]`. No reconciliation — `<n>` is already real.

   `issue create/edit` fold the parent and depends-on/blocks edges in (step 9) so this is usually the only publish call. Verify with `issue verify <number>`.
9. **Edges, if not folded into publish.** `issue create/edit --parent/--depends-on/--blocks` set them already; otherwise apply them directly — `issue parent <parent#> <child#>`, `issue depends-on <n> <dep#,…>`, `issue blocks <n> <target#,…>` (these wrap the `addSubIssue` / `addBlockedBy` GraphQL mutations documented below).

The `.issues/` drafts and review reports are kept (git-ignored). Use `issue purge [<n>]` to clear them when done.

> **Prerequisites:** `issue` on PATH (`mise run install-issue`), `gh` authenticated, and for the review gate `peer` installed (`mise run install-peer`) with its harnesses authenticated. Add `.issues/` to `.gitignore` (or `.gitignore.local`).

## Review gate (four reports, before publish)

No issue body reaches GitHub until it has four independent reports: two through the current host's native subagent mechanism and two from the other primary model family through `peer`. Every reviewer checks the drafted `.issues/<…>.md` against [`references/template.md`](references/template.md) and the target repository's conventions. This is the same strict host-routing matrix used by the implementation pipeline: a model family runs natively on its own host and through peer only when it is cross-host.

| Current host | Two native reports | Two external peer reports |
|---|---|---|
| **Codex** | two independent `codex-native` reviewer subagents; inherit the session model and reasoning | live aliases `opus-cli`, `sonnet-cli` |
| **Claude** | native reviewer Tasks on `opus`, `sonnet`; effort inherits | live Codex-family aliases `gpt`, `terra` |
| **Other** | unsupported — block the gate and publish | do not dispatch |

Before dispatch, resolve the external aliases through `peer list` and verify that both are external, cross-host, reviewer-capable entries. Validate the explicit peer effort against both entries; `high` is valid for the fixed pairs above. Do not silently substitute an alias, run same-host Claude through Claude CLI, run same-host Codex through Codex CLI, or degrade the gate to fewer than four successful reports.

Give all four reviewers the same embedded draft, canonical template, review criteria, and exact YAML output contract. The native reviews remain independent even on a Codex host where both inherit the same model: label one `native-template` with primary focus on template/metadata completeness and the other `native-feasibility` with primary focus on feasibility and repository idioms, while requiring both to perform the full review. Dispatch both native calls and one backgrounded helper call in one message:

```text
Codex host:
  native: codex-native reviewer "native-template" (inherit; no model/effort override)
  native: codex-native reviewer "native-feasibility" (inherit; no model/effort override)
  peer:   issue review ".issues/<n>-<type>-<slug>.md" \
            --reviewers opus-cli,sonnet-cli --effort high

Claude host:
  native: Task reviewer model=opus (inherit)
  native: Task reviewer model=sonnet (inherit)
  peer:   issue review ".issues/<n>-<type>-<slug>.md" \
            --reviewers gpt,terra --effort high
```

`issue review` accepts `--reviewers <comma-separated-live-aliases>`; its legacy direct-call default remains `gpt,gemini` for compatibility, but the skill must always pass the host-selected cross-host pair. The helper embeds the draft and canonical template in `.issues/<number>-reviews/prompt.md`, then calls canonical peer fan-out as `peer -C <workdir> -d <review-dir> --agent reviewer --peers <aliases> --effort <level> --prompt-file <review-dir>/prompt.md`. The native prompts must use that same self-contained content and output contract:

```yaml
issue_review:
  status: pass|fail
  blocking_findings:
    - concise evidence-backed finding with draft section and remediation
  nits:
    - concise optional improvement
```

Require `status: fail` exactly when `blocking_findings` is non-empty and `[]` for an empty list. Reject malformed output as an unsuccessful report rather than guessing its meaning. Read the two native results and exactly two `ok` peer report rows under `.issues/<number>-reviews/`. The gate passes only when all four reports are successful, parseable, and contain no blocking finding; nits are optional. Fold blocking findings back into the draft and re-run the entire four-report gate until clean. Keep the reports and materialized prompt in `.issues/` as the audit trail, then proceed to Publish.

Consult the `/peer` skill for the live registry, dispatch contract, and harness authentication requirements.

## Issue metadata (type, parent, dependencies)

Every issue carries metadata that is not part of the body:

- **Issue type** — `Feature` or `Task` (see below).
- **Parent** — hierarchical sub-issue relationship (`addSubIssue`).
- **Depends on / Blocks** — dependency relationships (`addBlockedBy`). `A depends on B` and `B blocks A` are the same edge viewed from opposite sides.

All three live exclusively on GitHub's native issue fields, set via `gh api graphql` mutations. GitHub renders type, parent, and dependencies in the sidebar and sub-issue tree automatically. Keep the issue body focused on Goal / Implementation plan / Definition of done — leave structural relationships to metadata.

### Choosing the type

- **Feature** — user-facing capability or a coherent slice of behavior that delivers value on its own. Architecture-level Features ship with a `# Layout`; non-architecture Features don't.
- **Task** — implementation unit that exists in service of a parent Feature (or Initiative). Tasks almost always have a parent.
- Bug / Initiative — exist but are out of scope for this skill's default dispatch. Only use when the user explicitly asks for a bug report or an initiative.

If the user didn't state the type, ask via `AskUserQuestion` with header `"Issue type"`, options `Feature` and `Task`. Don't guess from the body — the same body can describe either.

### Choosing the parent

- Features usually sit under an Initiative (or stand alone at the top level).
- Tasks almost always sit under a Feature.
- The parent is a sub-issue relationship (`addSubIssue` GraphQL mutation), not a body-level `Parent: #N` line. Write the body line and set the GraphQL parent.

If the user didn't state the parent:

- For a **Task**: ask via `AskUserQuestion`. Pre-seed the options with plausible parents from `gh issue list --state open --search "type:Feature" --json number,title --limit 20` so the user can pick an existing Feature. Include `No parent` only if the user context suggests a standalone Task.
- For a **Feature**: ask whether it has a parent Initiative. Default to `No parent` if the repo has no open Initiative.

Never invent or infer a parent silently. The user confirms the relationship.

### Fetching IDs

Issue type IDs and issue node IDs are required for the mutations. Fetch them at runtime — do not hardcode IDs across repos.

```bash
# Resolve repo once, reuse below.
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
OWNER="${REPO%/*}"; NAME="${REPO#*/}"

# All issue types the repo supports, with IDs.
gh api graphql -f query='
  query($owner:String!,$name:String!){
    repository(owner:$owner,name:$name){
      issueTypes(first:10){ nodes{ id name } }
    }
  }' -f owner="$OWNER" -f name="$NAME"

# Node ID for an issue (new or existing) by number.
gh api graphql -f query='
  query($owner:String!,$name:String!,$n:Int!){
    repository(owner:$owner,name:$name){
      issue(number:$n){ id title issueType{name} parent{number title} }
    }
  }' -f owner="$OWNER" -f name="$NAME" -F n=<number>
```

### Setting the type

Prefer the `--type` flag (gh ≥ 2.94) — pass the type **name** at create or edit time, no ID lookup needed:

```bash
gh issue create --title "..." --type "Feature" --body-file "$BODY"   # at creation
gh issue edit <n> --type "Task"                                       # retype later
```

If you need the GraphQL path (older gh, or scripting against node IDs):

```bash
gh api graphql -f query='
  mutation($issueId:ID!,$typeId:ID!){
    updateIssueIssueType(input:{issueId:$issueId, issueTypeId:$typeId}){
      issue{ number issueType{ name } }
    }
  }' -f issueId="$ISSUE_ID" -f typeId="$TYPE_ID"
```

To clear the type (rare), pass `issueTypeId: null` — `updateIssueIssueType` accepts a nullable type.

### Setting the parent

```bash
gh api graphql -f query='
  mutation($parentId:ID!,$childId:ID!){
    addSubIssue(input:{issueId:$parentId, subIssueId:$childId}){
      issue{ number }
      subIssue{ number title }
    }
  }' -f parentId="$PARENT_ID" -f childId="$CHILD_ID"
```

Note the argument naming: in `AddSubIssueInput`, `issueId` is the **parent**, `subIssueId` is the **child**. To move a child under a different parent, pass `replaceParent: true`. To detach, use `removeSubIssue` with the same shape.

### Choosing depends-on / blocks

Dependency relationships capture sequencing between issues that don't share a parent/child hierarchy:

- **Depends on** — this issue cannot start/merge until the referenced issue lands. `A depends on B` ⇒ A is blocked by B.
- **Blocks** — this issue must land before the referenced issue can start/merge. `A blocks B` ⇒ B is blocked by A.

These are two views of the same directed edge. Pick whichever direction the user naturally phrased; don't double-set them.

When to ask:

- If the user already said "depends on #N" or "blocks #N", take that literally — no `AskUserQuestion` needed.
- If the issue body sketch references prior work or unblocks future work, and the user hasn't stated the relationship, ask via `AskUserQuestion` with two questions: `"Depends on"` and `"Blocks"`. Offer `None` as an option and allow free-text entry ("Other" in the AskUserQuestion UI). Do not invent edges from body content alone.
- For trivial standalone issues (doc tweaks, isolated bug fixes) skip the ask.

Write the body-level line and set the GraphQL edge.

### Setting depends-on (`addBlockedBy` from the dependent side)

`A depends on B`:

```bash
gh api graphql -f query='
  mutation($issueId:ID!,$blockingIssueId:ID!){
    addBlockedBy(input:{issueId:$issueId, blockingIssueId:$blockingIssueId}){
      issue{ number }
      blockingIssue{ number title }
    }
  }' -f issueId="$A_ID" -f blockingIssueId="$B_ID"
```

### Setting blocks (`addBlockedBy` from the blocker side)

`A blocks B` is the same edge as `B depends on A`, so the mutation flips the arguments:

```bash
gh api graphql -f query='
  mutation($issueId:ID!,$blockingIssueId:ID!){
    addBlockedBy(input:{issueId:$issueId, blockingIssueId:$blockingIssueId}){
      issue{ number }
      blockingIssue{ number title }
    }
  }' -f issueId="$B_ID" -f blockingIssueId="$A_ID"
```

`issueId` is the blocked side; `blockingIssueId` is the blocker. Translate the user's phrasing once before running the mutation.

### Removing a dependency

Symmetric with `removeBlockedBy` — same `{ issueId, blockingIssueId }` shape. Use when rewriting an existing issue whose stated dependencies have shifted.

### Verifying after submit

After `gh issue create`/`edit` plus the applicable mutations, re-query the issue and surface the full metadata:

```bash
gh api graphql -f query='
  query($owner:String!,$name:String!,$n:Int!){
    repository(owner:$owner,name:$name){
      issue(number:$n){
        number title
        issueType{ name }
        parent{ number title }
        blockedBy(first:10){ nodes{ number title } }
        blocking(first:10){ nodes{ number title } }
      }
    }
  }' -f owner="$OWNER" -f name="$NAME" -F n=<number>
```

Report back: issue URL, type, parent, depends-on (= `blockedBy`), blocks (= `blocking`). If the user originally asked for any relationship that didn't resolve, stop and clarify — don't leave the issue half-configured.

## Companion skills

- `/git` — branch naming, commit prefixes (relevant when the issue references commits or you follow up with `pr`).
- `/peer` — external reviewer dispatch contract, registry, and auth for the review gate.
- `/review` — review checklist for verifying drafts conform.
- `/loqui` — language-specific patterns and idioms, consulted before writing sketches.
- `/gestalt` — repo orientation (map / analyze / callers) before sketching.

## Reference

- [operations/pr.md](operations/pr.md) — create a PR from the current branch, optionally linked to an issue.
- [`references/template.md`](references/template.md) — section-by-section template structure.
- [`references/sketches.md`](references/sketches.md) — patterns and anti-patterns for implementation sketches.
