---
name: linux-systemd-sota
description: >-
  Modern service, timer, and init management with systemd — use whenever the task
  involves running something as a service/daemon, scheduling jobs, `cron`, startup
  scripts, `nohup`/`&` backgrounding, logging, or "make this start on boot and
  restart on failure". Steers from init scripts/`cron`/`nohup` toward the SOTA
  path: unit files with drop-in overrides (`systemctl edit`), `--user` services,
  **timers instead of cron**, socket activation, hardening directives
  (`ProtectSystem`, `DynamicUser`, `NoNewPrivileges`, `SystemCallFilter`,
  capability bounding), `systemd-run` transient units, structured `journalctl`
  logging, and `systemd-analyze security/blame`. Reach for it on "daemonize this",
  "run X every night", "why won't my service start", "harden this service", or
  any boot-time/scheduling/logging task.
---

# systemd & services (SOTA)

The cheat-sheet's `systemctl start/enable/status` and "systemd replaced SysVinit"
are the right starting point. What it misses is that systemd is a **whole
platform**: it schedules (timers), isolates (sandboxing), logs (journal),
activates on demand (sockets), and runs throwaway jobs (`systemd-run`). SysV init
scripts and cgroup v1 were *removed* in systemd 258 — there is no "later" to put
this off to.

> **Prime directive: make it a unit.** Anything that must start on boot, restart
> on failure, run on a schedule, or be logged and resource-bounded belongs in a
> unit file — not in `rc.local`, not in `nohup … &`, not in a user's crontab.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)                  | SOTA                                                                |
|---------------------------------------------|---------------------------------------------------------------------|
| `nohup ./app &` / `screen` to keep it up    | a `.service` unit with `Restart=on-failure`                        |
| `crontab -e` for scheduled jobs             | a `.timer` + `.service` pair — logged, dependency-aware, catch-up   |
| Edit the vendor unit in `/lib/systemd/...`  | `systemctl edit app` → drop-in override in `/etc/systemd/system/`   |
| Run a one-off heavy job with `&`            | `systemd-run --unit=job ./batch.sh` (cgroup-bounded, journaled)     |
| App listens on a port at all times          | **socket activation**: a `.socket` starts the service on first conn |
| `tail -f /var/log/app.log`                  | `journalctl -u app -f` (structured, indexed, per-unit, filterable)  |
| Service runs as root, full FS access        | sandbox it: `ProtectSystem=strict`, `DynamicUser=`, drop caps       |
| `systemctl start` and hope it stays         | `systemctl enable --now app` (start + boot-persist in one)          |
| Per-user daemons via `.bashrc` hacks        | `systemctl --user enable --now app` (user manager, lingering)       |
| Guess why boot is slow                      | `systemd-analyze blame` / `critical-chain`                          |

## The creed

1. **Units are declarative state.** A unit says *what* should be true (running,
   enabled, after-network); systemd makes it so and keeps it so. Dependencies
   (`After=`, `Wants=`, `Requires=`) replace ordering hacks in init scripts.
2. **Override with drop-ins, never edit vendor units.** `systemctl edit app`
   creates `/etc/systemd/system/app.service.d/override.conf`; package upgrades
   keep your changes. Editing the shipped unit loses them and breaks updates.
3. **Timers beat cron.** Timers are units: they log to the journal, respect
   dependencies, support `Persistent=true` (catch up missed runs after downtime),
   `RandomizedDelaySec=` (avoid thundering herds), and monotonic schedules. Cron
   has none of that.
4. **Sandbox every service.** systemd is a security tool. `ProtectSystem=strict`,
   `ProtectHome=`, `PrivateTmp=`, `NoNewPrivileges=`, `DynamicUser=`,
   `CapabilityBoundingSet=`, `SystemCallFilter=@system-service`, and
   `RestrictAddressFamilies=` shrink a compromised service's blast radius to
   almost nothing — for free, in the unit file.
5. **The journal is the log.** Structured, indexed, per-unit, with metadata. Query
   it (`-u`, `-p`, `--since`, `-o json`) instead of grepping flat files. It's
   persistent by default on current systemd.
6. **Activate on demand where it fits.** Socket/path/timer activation means the
   service runs only when needed, started by systemd holding the socket — faster
   boots and clean restarts.

## A real service unit (hardened)

```ini
# /etc/systemd/system/app.service
[Unit]
Description=App API
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/app --config /etc/app/config.toml
Restart=on-failure
RestartSec=2s

# --- least privilege / sandboxing ---
DynamicUser=yes                     # ephemeral, unprivileged user just for this svc
ProtectSystem=strict                # / read-only except explicitly allowed paths
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE   # bind :443 without being root
SystemCallFilter=@system-service
RestrictAddressFamilies=AF_INET AF_INET6
MemoryMax=512M
StateDirectory=app                  # managed /var/lib/app, owned by the dynamic user

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now app.service
systemd-analyze security app.service     # scores the sandbox; aim to reduce "exposure"
```

## Timers (the cron replacement)

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Nightly backup

[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true            # run on next boot if the box was off at 02:30
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
```

```bash
systemctl enable --now backup.timer
systemctl list-timers                 # next/last run for every timer
journalctl -u backup.service --since today
```

The timer triggers a `backup.service` of the same name (or set `Unit=`).

## Transient jobs & inspection

```bash
systemd-run --unit=reindex -p MemoryMax=4G ./reindex.sh   # throwaway service, journaled
systemd-run --on-active=10m --unit=ping curl https://...  # one-shot timer
systemctl edit app                       # create/extend a drop-in override
systemctl cat app                        # show effective unit + all drop-ins
systemd-analyze blame                    # what took longest at boot
systemd-analyze critical-chain           # the dependency path that gated boot
```

## journalctl essentials

```bash
journalctl -u app -f                 # follow one unit
journalctl -u app -p err --since "1 hour ago"   # errors+ in a window
journalctl -b -1 -p warning          # warnings from the previous boot
journalctl -o json | jq …            # structured for pipelines
journalctl --disk-usage; journalctl --vacuum-time=2weeks   # manage retention
```

Resource control lives one level down in `linux-process-cgroups-sota`; the
sandbox's filesystem labels intersect with SELinux/AppArmor in
`linux-permissions-acl-caps-sota`; the boot sequence systemd sits inside is in
`linux-boot-uki-sota`.
