---
allowed-tools: Bash(gh review *), Bash(gh pr *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
---

# fcprr — delegate to the `fcprr` skill

The fix → commit → push → reply → resolve workflow lives in its own skill. Invoke Skill `fcprr`, forwarding the `$ARGUMENTS` after the leading `fcprr` token (`--comment <id>…`, `--reply`, `-m`, `--pr`, `paths…`).

Feed it the comments from the `comments` route: one `--comment <id>` per accepted (valid) thread for the full fix → resolve chain, and `--resolve-only` per dismissed thread to reply the rationale and resolve without a fix. Deferred and needs-discussion threads stay open.
