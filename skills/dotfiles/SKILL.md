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

<!-- Generated from skills/dotfiles/SKILL.md by henia build; edit the canonical source. -->

`~/dotfiles` deploys with [phora](https://github.com/srnnkls/phora). The deployment model and the Scrut checks live in `~/dotfiles/README.md`, `phora.toml` and `tests/scrut/`. Read them before changing mappings; this skill covers the day-to-day workflow only.

## Configuration split

| File | Holds | Tracked |
|---|---|---|
| `phora.toml` | Sources: what the repository offers (`path`, `root`, `include`/`exclude`, `deploy = "link"`), the `henia` build source, hooks | yes |
| `phora.local.toml` | Targets: home destinations and which sources bind to them (`take`, `collapse`) | no |
| `phora.local.example.toml` | Template for `phora.local.toml` | yes |

Run every command from `~/dotfiles` or pass `-C ~/dotfiles`.

## Preview

```sh
phora preview                       # offline, from the lock
phora preview --target claude --files
```

Preview before every sync that changes mappings.

## Add a dotfile

1. Place the file in the repository, e.g. `~/dotfiles/.config/app/config.toml`.
2. If an existing source already offers that directory, skip to step 4.
3. Add a source to `phora.toml`:

   ```toml
   app = { path = ".", root = ".config/app", deploy = "link" }
   ```

4. Bind it in `phora.local.toml` (and the example file, for new programs):

   ```toml
   app = { path = "~/.config/app", sources = ["app"] }
   ```

   Use `sources.app = { collapse = false }` when the program writes its own files into the directory.
5. `phora preview`, then `phora sync --prune`.

## Remove a dotfile

1. Delete the file, or its source and target entries.
2. `phora sync --prune` removes the deployed links phora no longer manages.

## Advance Tropos

Syncs build the locked Tropos commit. Move the pin explicitly:

```sh
phora update tropos --fast-forward --prune
```

## Live Tropos edits

Point the source at a working tree in `phora.local.toml`:

```toml
[sources.tropos]
path = "~/projects/tropos"
deploy = "link"
```

Remove the override and run `phora sync --prune` to return to the pin. A dotfiles override cannot replace a Tropos dependency such as Gestalt.

## Troubleshooting

| Need | Command |
|---|---|
| Deployed state per source and target | `phora list` |
| Deployed files match their recorded hashes | `phora verify` |
| Why a path is or is not deployed | `phora explain <target> <source> [path]` |
| Overwrite a conflicting file | `phora sync --force` |
| Deploy without hooks | `phora sync --no-hooks` |
