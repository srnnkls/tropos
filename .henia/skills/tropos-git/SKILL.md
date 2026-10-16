---
name: tropos-git
description: Branching for the Tropos repository — every change lands as a commit on main. Use before committing or pushing in Tropos.
henia:
  provides:
    git.branching:
---

# Tropos Branching

Commit on `main` and push it; no feature branches, no pull requests.

```bash
git switch main                       # before the first commit
git pull --rebase origin main         # when the push is rejected
git push origin main
```
