---
allowed-tools: Bash(gh review *), Bash(gh pr *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
---

# tfcprr — delegate to the `tfcprr` skill

The reply → resolve workflow, and the `tfcp` (triage → fix → commit → push) chain it runs first, live in their own skills. Triage is `tfcp`'s: it dispositions each accepted thread before anything is edited, and only the threads it puts in the `fix` bucket get replied to and resolved. Invoke Skill `tfcprr`, forwarding the `$ARGUMENTS` after the leading `tfcprr` token (`--comment <id>…`, `--reply`, `-m`, `--pr`, `paths…`).

Feed it the comments from the `comments` route: one `--comment <id>` per accepted (valid) thread for the full fix → resolve chain, and `--resolve-only` per dismissed thread to reply the rationale and resolve without a fix. Deferred and needs-discussion threads stay open.
