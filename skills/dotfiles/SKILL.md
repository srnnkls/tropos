---
name: dotfiles
description: Manage dotfiles deployed with phora (git-based artifact deployer) and the Tropos skills and harnesses Henia installs. Use when deploying, adding, removing, previewing, or organizing configuration files in ~/dotfiles.
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
| `.config/henia/henia.toml` | Skill packages, slots, harness files and config that `henia install --global` writes | yes |
| `~/.config/henia/henia.local.toml` | Local package overrides | no |

Phora deploys the Tropos scripts and FAS rules; Henia deploys skills, agents and harness config.

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

```sh
henia update --global                       # skills, agents, harness config
phora update tropos --fast-forward --prune  # scripts
phora update tropos-fas --fast-forward --prune  # FAS rules
```

## Live Tropos edits

Point Henia at a working tree in `~/.config/henia/henia.local.toml`:

```toml
[dependencies.tropos]
path = "~/projects/tropos"
link = true
```

Installed skills render the working tree through `henia show`, so edits apply at once; run `henia install --global` after adding or removing a skill, an agent or harness config.

Point both phora Tropos sources at the same tree in `phora.local.toml`, then `phora sync`:

```toml
[sources.tropos]
path = "~/projects/tropos"
deploy = "link"

[sources.tropos-fas]
path = "~/projects/tropos"
deploy = "link"
```

Remove the overrides, then `henia sync --global` and `phora sync --prune` to return to the pins.

## Troubleshooting

| Need | Command |
|---|---|
| Deployed state per source and target | `phora list` |
| Deployed files match their recorded hashes | `phora verify` |
| Why a path is or is not deployed | `phora explain <target> <source> [path]` |
| Overwrite a conflicting file | `phora sync --force` |
| Deploy without hooks | `phora sync --no-hooks` |
