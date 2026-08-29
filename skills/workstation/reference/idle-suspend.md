# Idle suspend

`services.autosuspend` (autosuspend 7.0.0) decides when `nixos` sleeps. Config is generated from `/etc/nixos/idle-suspend.nix` into a store-path ini; the daemon logs one decision per minute.

Governing settings: `interval = 60`, `idle_time = 1200`. Twenty consecutive idle minutes are required, and any matching check resets the timer to zero.

## The checks

| Check | Catches | Threshold |
|---|---|---|
| `Load` | anything CPU-bound | loadavg1 > 0.75 |
| `Processes` | long low-CPU jobs by name | cargo, rustc, cc1, ninja, make, nix, nixos-rebuild, rsync, scp, borg, restic, dd, tar, zstd |
| `NetworkBandwidth` | transfers over `enp69s0`, `wlo2` | 200 kB/s either direction |
| `LogindSessionsIdle` | any live session, Tailscale SSH included | `IdleHint` per session |
| `ActiveConnection` | `ssh -N` tunnels, which create no session | port 22 |
| `DiskIo` | local bulk copies | 5 MB/s, sampled in-process over 2s |
| `SleepInhibitor` | a held `keepawake` | block-mode inhibitor whose WHAT is sleep |

`Load` at 0.75 on a 64-core box is deliberately conservative. If the machine never reaches twenty idle minutes, this is the first knob; the journal names the offending check every minute.

## Constraints on any new check

Checks short-circuit. `execute_checks` stops at the first match, and `set_up_checks` returns a Python set, so execution order is hash-arbitrary rather than ini order. An `ExternalCommand` check can go many iterations without running.

A check must therefore not derive a rate from state stored between invocations — across a long gap, a burst averages down below any threshold and reports idle. Sample within the single invocation.

`ExternalCommand` exit codes are inverted from shell convention: exit 0 means activity detected, non-zero means idle.

Check failures are read as idle. `_safe_execute_activity` catches `TemporaryCheckError`, logs a warning, and returns "no activity"; `CommandActivity` treats any non-zero exit as idle by contract. An erroring check is indistinguishable from one that found nothing, so every `ExternalCommand` here exits 0 on internal failure — unreadable `/proc/diskstats`, a device regex matching nothing, `systemd-inhibit --list` failing.

`suspend_cmd` and `wakeup_cmd` are both required keys in `[general]`. Neither has a fallback in `config.get`, and the daemon refuses to start without them, whether or not a wakeup check is configured.

`NetworkBandwidth` validates that every listed interface exists at startup and raises `ConfigurationError` otherwise. The unit has no `Restart=`, so a renamed or removed NIC leaves autosuspend dead until the next reboot, silently. Every interface listed is a liability as well as coverage.

## polkit

A remote ssh session has no seat, and logind demands interactive authentication from seatless sessions. The rule grants `srnnkls`:

- `org.freedesktop.login1.inhibit-block-sleep` — for `keepawake`
- `org.freedesktop.login1.suspend`
- `org.freedesktop.login1.suspend-multiple-sessions` — logind selects between the two by session count, and this box always carries the autologin tty plus the gdm greeter

Multi-bit masks are not decomposed into their per-bit actions, so the policy file's per-action defaults do not predict which action logind checks. Test a mask directly:

```bash
ssh nix bash -c 'for w in sleep shutdown shutdown:sleep; do
  printf "%-16s " "$w"
  systemd-inhibit --what=$w --mode=delay --who=probe --why=test true 2>&1 | head -1
  done'
```

On this host both single-bit masks succeed under `allow_any=yes` delay actions while `shutdown:sleep` returns `Access denied` — the combination resolves elsewhere. Hence `--what=sleep` alone in `keepawake`.

## keepawake

```bash
keepawake cargo build --release   # holds for the life of the command
keepawake                         # holds until killed
```

The argument-less form supplies its own blocker, because `systemd-inhibit` with no COMMAND behaves as `--list`: it prints the inhibitor table, exits 0, and holds nothing.

`SleepInhibitor` matches the word sleep anywhere in a block-mode row, so an inhibitor whose reason text mentions sleep also counts as activity. This errs toward staying awake.

## Power

Around 243 of 720 hours a month are idle. At an estimated 130 W that was 31.6 of about 41 kWh; in S3 those hours cost perhaps 5-8 W, putting the month near 11 kWh.

The 130 W figure is a platform estimate for a 3970X on TRX40, not a measurement of this machine, and it drives three quarters of the total. A metering plug would settle it.
