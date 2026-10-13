# Modern Git Commands

## Command Reference

```bash
git config --global alias.fpush "push --force-with-lease"   # fails if the remote diverged
git range-diff main..@{1} main..@        # branch before/after rebase
git range-diff v1..v2 v1..v3             # two update series
```

## Hunk-level staging

To split a dirty tree into several commits, stage one subset of hunks at a time. Never use `-p` or `-i` (with stdin at EOF they exit 0 having staged nothing) or discard and redo with `git checkout <file>` / `git reset --hard` (deletes the work being split). Inspect with `git diff --stat` and `git diff -- f.txt`, then filter the patch, keeping the file preamble:

```bash
git diff -- f.txt > /tmp/p.patch
awk '/^@@/{n++} n==0 || n==1' /tmp/p.patch > /tmp/h1.patch   # preamble + hunk 1
git apply --cached /tmp/h1.patch
git commit -m "..."
```

After each commit, re-derive the patch and select the next hunk by its content, never by a hunk number from an earlier diff. Without the preamble (`diff --git`, `---`, `+++`), `git apply` fails with `patch fragment without header`. Only whole hunks move; lines inside a hunk need recomputed `@@` counts, and binary or renamed files need `--binary`. Unstage a hunk with the cached diff in reverse:

```bash
git diff --cached -- f.txt > /tmp/p.patch
awk '/^@@/{n++} n==0 || n==1' /tmp/p.patch > /tmp/h1.patch
git apply --cached --reverse /tmp/h1.patch
```

## Scripted rebase

Todo lines are oldest-first: line 1 is the older commit. Works over any range; for folds prefer `git commit --fixup` with `--autosquash`.

```bash
# Fold the last commit into the one before it
GIT_SEQUENCE_EDITOR="sed -i '' '2s/^pick/squash/'" git rebase -i HEAD~2

# Reword the older of the last two
GIT_SEQUENCE_EDITOR="sed -i '' '1s/^pick/reword/'" \
GIT_EDITOR="sed -i '' '1s/.*/new subject/'" git rebase -i HEAD~2

# Drop the older of the last two
GIT_SEQUENCE_EDITOR="sed -i '' '1s/^pick/drop/'" git rebase -i HEAD~2
```

## Commit to another branch without checking it out

Commits the index (stage first); HEAD and the worktree are untouched.

```bash
T=$(git write-tree)
C=$(git commit-tree "$T" -p "$(git rev-parse other)" -m "msg")
git update-ref refs/heads/other "$C"
```
