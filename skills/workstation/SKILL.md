---
name: workstation
description: Operate the nixos workstation, reached as `ssh nix` — wake it from the Mac, suspend it on demand, hold it awake through long jobs with keepawake, and diagnose why it slept or did not. Use for the nix or nixos host, the wake-nix Wake-on-LAN chain through alpine, or its autosuspend config. Not for the Nix package manager or general NixOS module authoring.
metadata:
  type: domain
henia:
  targets:
    codex:
      openai:
        interface:
          display_name: Workstation
          short_description: Apply the canonical workstation skill workflow
          default_prompt: Use $workstation for the requested task.
---

<!-- Generated from skills/workstation/SKILL.md by henia build; edit the canonical source. -->

Operate `nixos`, the Threadripper 3970X workstation. It suspends after 20 idle minutes and wakes from `ssh nix`.

> Reference: [idle-suspend.md](reference/idle-suspend.md) for the sleep config and its tuning, [wake-chain.md](reference/wake-chain.md) for the wake path.

## Topology

| Host | Role |
|---|---|
| `nixos` | the workstation. NixOS 24.05, wired NIC `enp69s0`, MAC `00:D8:61:D5:5F:61` |
| `alpine` | always-on LAN host. Relays the magic packet via `/usr/local/bin/wake-nix` |
| this Mac | client. `~/.ssh/bin/wake-nix` runs from an `ssh_config` `Match host nix exec` |

Two addresses: Tailscale MagicDNS (`nixos`, preferred) and LAN (`192.168.137.23`). The `ssh_config` selects the LAN one only when the tailnet is unreachable.

Config lives at `/etc/nixos/idle-suspend.nix`, imported from `configuration.nix`.

## Remote commands need a bash wrapper

The login shell is nushell:

```bash
ssh nix bash -c 'systemctl is-active autosuspend'
```

An unwrapped `&&` or `||` fails with a Nushell parser error.

## Everyday use

Wake and connect. The `ssh_config` hook handles it:

```bash
ssh nix
```

A cold wake blocks up to 150 seconds. A wrapper timeout below that kills the wake mid-flight, leaving its stderr diagnostics and no command output.

Suspend on demand:

```bash
ssh nix bash -c 'systemctl suspend'
```

Hold it awake through a long job:

```bash
ssh nix bash -c 'keepawake cargo build --release'
```

`keepawake` with no arguments holds until killed.

## Diagnosing

Why it is awake, or why it slept. One line per minute naming the check that matched:

```bash
ssh nix bash -c 'journalctl -u autosuspend -n 40 --no-pager'
```

Find and clear a forgotten hold:

```bash
ssh nix bash -c 'pgrep -x systemd-inhibit -u srnnkls -a'
ssh nix bash -c 'pkill -x systemd-inhibit -u srnnkls'
```

Tell a resume from a reboot — an unchanged `boot_id` across the gap means suspend-to-RAM:

```bash
ssh nix bash -c 'cat /proc/sys/kernel/random/boot_id; uptime'
```

## Traps

Clearing inhibitors with `pkill -f who=keepawake` kills the ssh session running it, because the pattern matches its own command line. Use `pkill -x systemd-inhibit -u srnnkls`.

A bare `keepawake` holds `sleep` indefinitely. Nothing expires it, and the box will not suspend while it lives.

`systemd-inhibit` with no COMMAND is a synonym for `--list`. It prints the inhibitor table and exits 0 while holding nothing.

Multi-bit inhibitor masks resolve to a different polkit action than single-bit ones. `--what=sleep:idle` is not authorized by a grant for `inhibit-block-sleep`. Use `--what=sleep`.

Tailscale SSH sessions do not appear in `who` or `ss -t 'sport = :22'`. Only logind sees them, as `Remote=yes`.

A remote seatless session cannot suspend or take a block inhibitor without an explicit polkit grant.

## Benchmark profile

The `performance` governor and THP `never` are the default, so a benchmark run needs no
preparation. `/etc/bench-profile` verifies the machine matches that and exits non-zero if it has
drifted:

```bash
ssh nix bash -c '/etc/bench-profile'
```

To go back to a power-saving profile, set `powerManagement.cpuFreqGovernor` to `schedutil` in
`configuration.nix` and remove the `bench-thp` service, then rebuild.

## Changing the config

Edit `/etc/nixos/idle-suspend.nix`, then:

```bash
ssh nix bash -c 'sudo nixos-rebuild test'
```

`test` activates without becoming the boot default, so a reboot reverts it. Promote to `switch` once it has run a day without suspending mid-job.

Evaluate without applying, from any writable directory on the box:

```bash
ssh nix bash -c 'cd ~/build-test && nixos-rebuild build -I nixos-config=/etc/nixos/configuration.nix'
```
