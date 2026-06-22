---
name: linux-process-cgroups-sota
description: >-
  Modern process and resource management — use whenever the task involves
  processes, PIDs, signals, killing/restarting something, "what's eating CPU/RAM",
  the OOM killer, nice/priority, or limiting a job's resources. Steers from the
  cheat-sheet's `ps aux`/`kill -9`/`nice` reflexes toward the SOTA model: cgroup
  v2 unified hierarchy for real resource control, `systemd-run` to launch work in
  a constrained transient scope/slice, memory protection (`MemoryHigh`/`Max`,
  `systemd-oomd`/earlyoom) instead of waiting for the kernel OOM killer, signals
  done right (SIGTERM before SIGKILL), and reading process state from `/proc`.
  Reach for it on "this job is hogging the box", "cap this process's memory",
  "why did the kernel kill my service", "stop a runaway", or scheduling/priority
  questions.
---

# Linux processes & cgroups v2 (SOTA)

The cheat-sheet's process lifecycle (created → running → sleeping → zombie),
`ps`/`top`, `fork()`, and `kill -STOP` are all correct. What it omits is the
thing that actually governs processes on a modern box: **cgroup v2**. CPU,
memory, IO, and PIDs are accounted and limited per-cgroup, every service lives in
one, and `systemd-run` lets you drop any command into a constrained scope.

> **Prime directive: bound the resource, don't babysit the process.** Don't sit
> on `top` waiting to `kill -9` a runaway — put it in a cgroup with a ceiling so
> it physically *cannot* take the box down, and let SIGTERM do orderly shutdown.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)                       | SOTA                                                                |
|--------------------------------------------------|---------------------------------------------------------------------|
| `kill -9 <pid>` first                            | `kill <pid>` (SIGTERM) → wait → `-9` only if it ignores; -9 skips cleanup |
| `nice -19 ./job` to be polite                    | run it in a slice with `CPUWeight=`/`MemoryHigh=` — real, enforced  |
| `./heavy &` then hope                            | `systemd-run --scope -p MemoryMax=2G -p CPUQuota=50% ./heavy`       |
| Wait for the kernel OOM killer                   | set `MemoryHigh`/`MemoryMax`; run `systemd-oomd`/earlyoom for graceful kills |
| `ps aux | grep foo`                              | `pgrep -a foo` / `pidof foo` (no self-match, no awk)                |
| `top` to watch                                   | `btop`/`htop` interactively; `/proc/<pid>/` + PSI programmatically  |
| `renice` a misbehaving service                   | `systemctl set-property svc CPUWeight=50 MemoryMax=4G` (persisted)  |
| `ulimit` for memory caps                         | cgroup `MemoryMax=` (per-service, hierarchical) over per-shell rlimits |
| "find what's using the disk IO"                  | `iotop`/PSI io pressure, or cgroup `io.stat`                        |
| Pin to CPUs with hand-rolled affinity            | `taskset -c`/`AllowedCPUs=`; `chrt` for real-time class             |

## The creed

1. **cgroup v2 is the unit of control, not the PID.** Every process belongs to a
   cgroup; limits and accounting are hierarchical. cgroup v1 is gone (systemd
   258), so assume the single unified tree at `/sys/fs/cgroup`.
2. **Constrain at launch.** `systemd-run --scope`/`--slice` wraps any command in a
   transient cgroup with CPU/memory/IO/PID ceilings — the modern, safe way to run
   a heavy or untrusted job interactively.
3. **Protect memory before the OOM killer fires.** `MemoryHigh=` throttles
   (reclaim pressure) and `MemoryMax=` hard-caps a single service so it OOMs
   *itself* instead of triggering a kernel kill that may take an innocent victim.
   `systemd-oomd` acts on PSI to kill gracefully and predictably.
4. **Signals are a protocol.** SIGTERM asks for orderly shutdown (flush, close,
   checkpoint); SIGKILL is non-catchable and skips all of that. Default to TERM,
   escalate to KILL only after a timeout. SIGSTOP/SIGCONT pause/resume.
5. **Read state from `/proc`, not from scraped text.** `/proc/<pid>/status`,
   `cmdline`, `fd/`, `limits`, `cgroup`, and PSI (`/proc/pressure/{cpu,memory,io}`)
   are the structured truth. Tools like `ps` are just formatters over them.
6. **Reap zombies by fixing the parent.** A zombie is a finished child whose
   parent hasn't `wait()`ed. You can't `kill -9` a zombie — signal or restart the
   *parent* so it reaps. PID 1 adopts and reaps orphans.

## Constrain any command (the killer feature)

```bash
# Run a heavy job that physically cannot exceed 2G RAM or half a core:
systemd-run --scope -p MemoryMax=2G -p CPUQuota=50% -p IOWeight=50 ./batch.sh

# As a transient *service* (survives your shell, logged to the journal):
systemd-run --unit=reindex -p MemoryMax=4G ./reindex.sh
journalctl -u reindex -f

# Adjust limits on a running service, persisted as a drop-in:
systemctl set-property nginx.service CPUWeight=200 MemoryMax=1G

# Inspect a service's resource accounting:
systemd-cgtop                          # live top-style cgroup resource view
systemctl status nginx                 # shows the cgroup + current Memory/CPU
cat /sys/fs/cgroup/system.slice/nginx.service/memory.current
```

## Signals & lifecycle, done right

```bash
kill <pid>            # SIGTERM — ask nicely; let the process clean up
kill -KILL <pid>      # SIGKILL — last resort; no cleanup, possible corruption
kill -HUP <pid>       # many daemons reload config on HUP
pkill -TERM -f 'pattern'   # by name/cmdline (careful with the regex)
systemctl kill --signal=TERM app.service   # signal a whole service's cgroup
```

For services, configure `TimeoutStopSec=` and `KillSignal=` in the unit rather
than scripting the term→kill dance yourself (see `linux-systemd-sota`).

## Inspecting processes (modern)

```bash
pgrep -a nginx                 # PIDs + cmdline, no grep-self noise
ps -eo pid,ppid,stat,rss,comm --sort=-rss | head   # top RSS, scriptable columns
cat /proc/<pid>/status         # state, threads, caps, memory, cgroup
ls -l /proc/<pid>/fd           # open file descriptors (find the leak/lock)
cat /proc/pressure/memory      # PSI: is the box actually under memory pressure?
```

Priority/scheduling: `nice`/`renice` set CPU niceness, `ionice` sets IO class,
`chrt` sets real-time scheduling, `taskset -c 0-3 cmd` pins to CPUs. But for
anything persistent, encode it as cgroup properties on the service rather than
per-process knobs. For deep "what is it *actually* doing" (syscalls, off-CPU
time, latency), drop to `linux-observability-ebpf-sota`.
