# Wake chain

`ssh nix` wakes the box with no extra command. Two `ssh_config` stanzas drive it:

```
Match host nix exec "~/.ssh/bin/wake-nix"
Match host nix exec "~/.ssh/bin/wake-nix --lan"
    HostName 192.168.137.23
Host nix
    HostName nixos
    User srnnkls
    SetEnv LC_ALL=C.UTF-8
    ConnectionAttempts 3
    ServerAliveInterval 30
```

The first invocation blocks until the box answers. The second reports whether the LAN address is the path in use, which is what redirects `HostName`. They share a cached path in `$TMPDIR/wake-nix.$(id -u).path` with a 60-second freshness window.

## Path

1. Probe `nixos.tailb7c9ac.ts.net:22`, then `192.168.137.23:22`. If either answers, exit.
2. Take a `mkdir` lock, so concurrent invocations issue one magic packet between them.
3. Choose the target from alpine's reachability: reachable over the tailnet means the tailnet works, so poll the MagicDNS name; only LAN-reachable means poll the LAN address.
4. Relay through the `alpine` ssh alias, which sends the packet to `00:D8:61:D5:5F:61` and polls.
5. On relay failure, broadcast locally with `wakeonlan`.
6. Poll until the chosen address answers, then record the path.

## Invariants

Poll the address ssh will use. sshd answers several seconds before tailscaled has re-registered the node, so polling the LAN address and connecting over MagicDNS hands ssh a half-ready tailnet. `TAILSCALE_GRACE` allows 30 seconds for the preferred path before accepting whichever answered.

Relay through the alias, never a raw address. `Host alpine` and its `Match` block supply `User root` and `IdentityFile ~/.ssh/alpine.pub` on the LAN path. Connecting to `192.168.137.44` directly matches no `Host` block and authenticates as the wrong user.

A failed relay must fall through to the local broadcast. Probing alpine's port 22 proves only that it answers TCP; the ssh can still fail on a changed host key or a locked agent under `BatchMode`.

Lock liveness is refresh-based. A failed `nc -z -G 2` probe costs a full 2 seconds, so a poll iteration burns about 6 seconds of wall time and a loop counting sleeps rather than the clock runs roughly three times its nominal timeout. The holder touches the lock every poll; absence of a refresh marks it dead.

Release only a lock you still own. A nonce inside the lock directory is checked before removal, so a reaped holder's exit trap cannot delete the next owner's lock. The `INT` and `TERM` traps exit after releasing rather than continuing lock-free.

## Measured

| Transition | Packet to sshd | Total for `ssh nix` |
|---|---|---|
| S5, full poweroff | 47s | 52.9s |
| S3, suspend-to-RAM | 20s | 30s |

Most of the S5 figure is the box booting; the wake machinery itself costs about 6 seconds of probing.

## Failure modes

Remote with alpine down is unrecoverable. Alpine is the only always-on sender on that L2, and a broadcast from a remote laptop cannot reach the workstation's LAN. The script reports a timeout.

Caller timeouts below 150 seconds truncate a cold wake, leaving wake diagnostics on stderr and no command output.

`systemctl suspend` is asynchronous, so port 22 keeps answering for a few seconds while delay inhibitors run. A connection landing in that window dies when the box goes down; retrying takes the normal wake path.

## Testing without a live box

Copy the script and rewrite the host constants to `127.0.0.1` with a listener, or to `192.0.2.0/24` for the unreachable case, and zero the MAC. That exercises the lock, the path selection, and the fallbacks without touching the workstation.

Use `nc -k -l` for the listener. A plain `nc -l` accepts one connection and exits, so concurrent probes consume each other and the run reports a failure that is not there.
