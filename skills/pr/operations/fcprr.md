---
allowed-tools: Bash(gh review *), Bash(gh pr *), Bash(git add *), Bash(git commit *), Bash(git push *), Bash(git rev-parse *), Bash(git branch *)
---

# fcprr — delegate to the `fcprr` skill

The fix → commit → push → reply → resolve workflow lives in its own skill. Invoke Skill `fcprr`, forwarding the `$ARGUMENTS` after the leading `fcprr` token (`--comment <id>…`, `--reply`, `-m`, `--pr`, `paths…`).

Feed it the addressworthy comments from the `comments` route — one `--comment <id>` per accepted (valid) thread; invalid comments are dismissed, not fixed.
