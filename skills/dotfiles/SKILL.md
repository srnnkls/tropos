---
name: dotfiles
description: Manage dotfiles deployed with phora (git-based artifact deployer) and the Henia-compiled Tropos harnesses. Use when deploying, adding, removing, previewing, or organizing configuration files in ~/dotfiles.
metadata:
  type: domain
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Dotfiles
          short_description: Apply the canonical dotfiles skill workflow
          default_prompt: Use $dotfiles for the requested task.
---

`~/dotfiles` deploys with [phora](https://github.com/srnnkls/phora). Before changing mappings, read `~/dotfiles/README.md`, `phora.toml` and `tests/scrut/`. Run every command from `~/dotfiles` or with `-C ~/dotfiles`.

## Configuration split

| File | Holds | Tracked |
|---|---|---|
| `phora.toml` | Sources (`path`, `root`, `include`/`exclude`, `deploy = "link"`), the `henia` tool, hooks | yes |
| `phora.local.toml` | Targets: home destinations and their sources (`take`, `collapse`); local source overrides | no |
| `phora.local.example.toml` | Template for `phora.local.toml` | yes |

## Preview

```sh
phora preview                       # offline, from the lock
phora preview --target claude --files
```

Preview before every sync that changes mappings.

## Add a dotfile

1. Place the file in the repository, e.g. `~/dotfiles/.config/app/config.toml`.
2. Skip to step 4 if a source already offers that directory.
3. Add a source to `phora.toml`:

   ```toml
   app = { path = ".", root = ".config/app", deploy = "link" }
   ```

4. Bind it in `phora.local.toml` (and, for new programs, the example file):

   ```toml
   app = { path = "~/.config/app", sources = ["app"] }
   ```

   Use `sources.app = { collapse = false }` when the program writes into the directory.
5. `phora preview`, then `phora sync --prune`.

## Remove a dotfile

Delete the file, or its source and target entries, then `phora sync --prune`.

## Advance Tropos

Syncs build the locked Tropos commit. Move the pin with:

```sh
phora update tropos --fast-forward --prune
```

## Live Tropos edits

Point both Tropos sources at a working tree in `phora.local.toml`:

```toml
[sources.tropos]
path = "~/projects/tropos"
deploy = "link"

[sources.tropos-fas]
path = "~/projects/tropos"
deploy = "link"
```

FAS rules link into the working tree; skills and harnesses stay copied Henia build output, so `phora sync` after editing them. Remove the overrides and `phora sync --prune` to return to the pin. The override cannot replace a Tropos dependency such as Gestalt.

## Troubleshooting

| Need | Command |
|---|---|
| Deployed state per source and target | `phora list` |
| Deployed files match their recorded hashes | `phora verify` |
| Why a path is or is not deployed | `phora explain <target> <source> [path]` |
| Overwrite a conflicting file | `phora sync --force` |
| Deploy without hooks | `phora sync --no-hooks` |
