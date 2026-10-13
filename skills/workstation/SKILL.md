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

Operate `nixos`, the Threadripper 3970X workstation. It suspends after 20 idle minutes and wakes on `ssh nix`. Sleep config: [idle-suspend.md](reference/idle-suspend.md). Wake path: [wake-chain.md](reference/wake-chain.md).

## Topology

| Host | Role |
|---|---|
| `nixos` | the workstation. NixOS 24.05, wired NIC `enp69s0`, MAC `00:D8:61:D5:5F:61` |
| `alpine` | always-on LAN host. Relays the magic packet via `/usr/local/bin/wake-nix` |
| this Mac | client. `~/.ssh/bin/wake-nix` runs from an `ssh_config` `Match host nix exec` |

`ssh nix` uses Tailscale MagicDNS (`nixos`), falling back to LAN (`192.168.137.23`) only when the tailnet is unreachable. Over the tailnet it is Tailscale SSH (`PubkeyAuthentication no`, `IdentityAgent none`): no key or 1Password prompt, equivalent to `tailscale ssh srnnkls@nixos`. `nix-lan` uses a key and may prompt; run bench campaigns (two-box protocol) over `ssh nix`.

Config: `/etc/nixos/idle-suspend.nix`, imported from `configuration.nix`.

## Commands

The login shell is nushell: wrap every remote command in `bash -c`; an unwrapped `&&` or `||` fails to parse.

| Task | Command |
|---|---|
| Wake and connect (cold wake blocks up to 150 s; wrapper timeouts must be ≥150 s) | `ssh nix` |
| Suspend | `ssh nix bash -c 'systemctl suspend'` |
| Hold awake through a job | `ssh nix bash -c 'keepawake cargo build --release'` |
| Why awake or asleep (matched check per minute) | `ssh nix bash -c 'journalctl -u autosuspend -n 40 --no-pager'` |
| Find a forgotten hold | `ssh nix bash -c 'pgrep -x systemd-inhibit -u srnnkls -a'` |
| Clear it | `ssh nix bash -c 'pkill -x systemd-inhibit -u srnnkls'` |
| Resume vs reboot (unchanged `boot_id` = suspend-to-RAM) | `ssh nix bash -c 'cat /proc/sys/kernel/random/boot_id; uptime'` |
| Check bench profile (default `performance` governor, THP `never`; non-zero on drift) | `ssh nix bash -c '/etc/bench-profile'` |
| Apply config change (reboot reverts) | `ssh nix bash -c 'sudo nixos-rebuild test'` |
| Evaluate without applying | `ssh nix bash -c 'cd ~/build-test && nixos-rebuild build -I nixos-config=/etc/nixos/configuration.nix'` |

Promote `test` to `switch` after a day without mid-job suspends. Power-saving profile: `powerManagement.cpuFreqGovernor = schedutil` in `configuration.nix`, remove the `bench-thp` service, rebuild.

## Traps

- `pkill -f who=keepawake` matches its own command line and kills the ssh session; use `pkill -x systemd-inhibit -u srnnkls`.
- A bare `keepawake` holds `sleep` until killed; nothing expires it. It supplies its own blocker, since `systemd-inhibit` with no COMMAND means `--list`: it exits 0 and holds nothing.
- Multi-bit masks map to another polkit action: `--what=sleep:idle` is not covered by the `inhibit-block-sleep` grant; use `--what=sleep`.
- Tailscale SSH sessions are absent from `who` and `ss -t 'sport = :22'`; only logind sees them, as `Remote=yes`.
- A remote seatless session needs an explicit polkit grant to suspend or take a block inhibitor ([polkit](reference/idle-suspend.md#polkit)).
