# Idle suspend

`services.autosuspend` (autosuspend 7.0.0) logs one decision per minute. With `interval = 60` and `idle_time = 1200`, suspend needs twenty consecutive idle minutes; any matching check resets the timer.

## The checks

| Check | Catches | Threshold |
|---|---|---|
| `Load` | anything CPU-bound | loadavg1 > 0.75 |
| `Processes` | long low-CPU jobs by name | cargo, rustc, cc1, ninja, make, nix, nixos-rebuild, rsync, scp, borg, restic, dd, tar, zstd |
| `NetworkBandwidth` | transfers over `enp69s0`, `wlo2` | 200 kB/s either direction |
| `LogindSessionsIdle` | any live session, Tailscale SSH included | `IdleHint` per session |
| `ActiveConnection` | `ssh -N` tunnels, which create no session | port 22 |
| `DiskIo` | local bulk copies | 5 MB/s, sampled in-process over 2s |
| `SleepInhibitor` | a held `keepawake` | block-mode inhibitor whose WHAT is sleep; matches "sleep" anywhere in the row, reason text included |

If it never idles, find the matching check in the journal; raise `Load` first.

## Constraints on any new check

- Checks run in hash-arbitrary order and stop at the first match, so a check can skip many iterations. Sample any rate within one invocation, never from stored state.
- `ExternalCommand`: exit 0 means activity, non-zero means idle. Errors also read as idle, so every `ExternalCommand` here exits 0 on internal failure: unreadable `/proc/diskstats`, a device regex matching nothing, `systemd-inhibit --list` failing.
- `[general]` requires `suspend_cmd` and `wakeup_cmd`, or the daemon will not start.
- `NetworkBandwidth` raises `ConfigurationError` at startup for a missing interface, and the unit has no `Restart=`: a renamed or removed NIC leaves autosuspend dead until reboot. List only required interfaces.

## polkit

Grants for `srnnkls`:

- `org.freedesktop.login1.inhibit-block-sleep` (for `keepawake`)
- `org.freedesktop.login1.suspend`
- `org.freedesktop.login1.suspend-multiple-sessions` (always needed: autologin tty and gdm greeter are permanent sessions)

Policy defaults do not predict a multi-bit mask's action (`shutdown:sleep` is denied here); test masks directly:

```bash
ssh nix bash -c 'for w in sleep shutdown shutdown:sleep; do
  printf "%-16s " "$w"
  systemd-inhibit --what=$w --mode=delay --who=probe --why=test true 2>&1 | head -1
  done'
```
