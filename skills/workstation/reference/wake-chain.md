# Wake chain

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

The first exec blocks until the box answers; the second redirects `HostName` when the LAN path is in use. Both share the path cached in `$TMPDIR/wake-nix.$(id -u).path` (fresh for 60 seconds).

## Path

1. Probe `nixos.tailb7c9ac.ts.net:22`, then `192.168.137.23:22`. If either answers, exit.
2. Take a `mkdir` lock so concurrent invocations send one magic packet.
3. If alpine is reachable over the tailnet, poll the MagicDNS name; if only over LAN, poll the LAN address.
4. Relay through the `alpine` ssh alias, which sends the packet to `00:D8:61:D5:5F:61` and polls.
5. On relay failure, broadcast locally with `wakeonlan`.
6. Poll until the chosen address answers, then record the path.

## Invariants

- Poll the address ssh will use; sshd answers before tailscaled re-registers. `TAILSCALE_GRACE` allows 30 seconds for the preferred path before accepting whichever answered.
- Relay through the `alpine` alias, never `192.168.137.44`; only `Host alpine` and its `Match` block supply `User root` and `IdentityFile ~/.ssh/alpine.pub`.
- Fall through to the local broadcast on any relay failure, even when alpine's port 22 answered.
- The lock holder touches the lock every poll; an unrefreshed lock is dead. Time loops by the clock, not counted sleeps (a failed `nc -z -G 2` costs 2 s).
- Check the nonce in the lock directory before releasing it. `INT` and `TERM` traps exit after releasing.

## Measured

| Transition | Packet to sshd | Total for `ssh nix` |
|---|---|---|
| S5, full poweroff | 47s | 52.9s |
| S3, suspend-to-RAM | 20s | 30s |

## Failure modes

- Remote with alpine down: unrecoverable; the script reports a timeout.
- `systemctl suspend` is asynchronous; port 22 answers for a few seconds while delay inhibitors run. A connection in that window dies; retry, which takes the normal wake path.

## Testing without a live box

Copy the script; rewrite host constants to `127.0.0.1` with an `nc -k -l` listener (plain `nc -l` accepts one connection and fakes failures), or to `192.0.2.0/24` for the unreachable case; zero the MAC.
