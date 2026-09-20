---
name: dotfiles
description: Manage dotfiles using dotter (symlink manager and templater). Use when deploying, adding, removing, or organizing configuration files in ~/dotfiles.
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

Manage dotfiles using [dotter](https://github.com/SuperCuber/dotter) - a dotfile manager and templater.

## Select the deployment path

Check the active checkout's deployment documentation before changing mappings.
On the Phora migration branch, use `bin/phora-tropos` to compile the selected
Tropos checkout and deploy all four harness bundles into its probe home. The
runner's Scrut post-sync hook verifies that tree. `bin/phora-shadow` separately
checks equivalence with the existing Dotter deployment. Neither command performs
a live home cutover. On the established Dotter branch, use the workflow below.

## Environment

- **Dotfiles repo**: `~/dotfiles`
- **Dotter config**: `~/dotfiles/.dotter/`
  - `global.toml`: Package definitions (files to deploy)
  - `local.toml`: Machine-specific package selection
  - `cache.toml`: Deployment state cache

## Core Commands

```bash
dotter deploy
dotter deploy --dry-run
dotter undeploy
dotter watch
```

## Workflow: Add New Dotfile

### Step 1: Add Source File

Place the configuration file in `~/dotfiles`:

```bash
cp ~/.config/app/config.toml ~/dotfiles/.config/app/config.toml
```

### Step 2: Define in global.toml

Add a new package or extend existing one in `~/dotfiles/.dotter/global.toml`:

```toml
[myapp.files]
".config/app/config.toml" = "~/.config/app/config.toml"

# Or extend existing package
[existing-package.files]
".config/app/config.toml" = "~/.config/app/config.toml"
```

Source is a relative path from the dotfiles repo root; target is an absolute path or `~`-relative.

### Step 3: Enable Package (if new)

Add package to `~/dotfiles/.dotter/local.toml`:

```toml
packages = ["doom", "myapp"]
```

### Step 4: Deploy

```bash
cd ~/dotfiles && dotter deploy
```

## Workflow: Remove Dotfile

1. **Undeploy first**: `dotter undeploy`
2. **Remove from global.toml**: Delete the file mapping
3. **Remove package from local.toml** (if removing entire package)
4. **Redeploy**: `dotter deploy`
5. Remove file from dotfiles repo if desired

## Package Organization

Group related files into packages:

```toml
[shell.files]
".zshrc" = "~/.zshrc"
".zprofile" = "~/.zprofile"
".config/starship.toml" = "~/.config/starship.toml"

[nvim.files]
".config/nvim" = "~/.config/nvim"

[git.files]
".gitconfig" = "~/.gitconfig"
".gitignore_global" = "~/.gitignore_global"
```

## Templating

Dotter supports Handlebars templating for machine-specific values:

In `global.toml`:

```toml
[package.variables]
email = "default@example.com"
```

In `local.toml` (machine override):

```toml
[variables]
email = "work@company.com"
```

In template files, enclose the variable name `email` in two opening and two closing braces.

## Troubleshooting

### Conflict with existing file

```bash
dotter deploy --force
```

### Check deployment status

```bash
dotter deploy --dry-run --verbose
```

### View what's currently deployed

```bash
cat ~/dotfiles/.dotter/cache.toml
```
