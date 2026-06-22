---
name: linux-observability-ebpf-sota
description: >-
  Modern Linux performance analysis and debugging — use whenever the task is "the
  box/app is slow", "find what's using CPU/memory/IO/network", "trace what this
  process is doing", "why is latency high", or any production-debugging or
  profiling question. Goes far beyond the cheat-sheet's `ps`/`top`: the SOTA
  toolkit reads the kernel's own interfaces (`/proc`, `/sys`, **PSI** pressure
  metrics) and uses **eBPF** (`bpftrace`, bcc tools, `execsnoop`/`opensnoop`/
  `biolatency`/`tcplife`) plus `perf` and flame graphs to answer "what is it
  *actually* doing" without printf-debugging. Covers `strace`/`ltrace` for syscall
  tracing and a USE-method-style triage order. Reach for it on "diagnose this slow
  service", "trace syscalls/files/connections", "profile CPU", "find the latency",
  or "I can't reproduce it but it's slow in prod".
---

# Linux observability & eBPF (SOTA)

The cheat-sheet's debugging story is `ps aux` and `top`. Those tell you *that*
something is busy; they don't tell you *what it's doing* or *why it's slow*. The
modern answer is **eBPF**: safe, JIT-compiled programs you attach to kernel and
user probes to measure syscalls, file opens, disk latency, TCP lifetimes, and
off-CPU time on a *running production box* — no recompiling, no restart, near-zero
overhead. Combined with `/proc`, **PSI**, `perf`, and flame graphs, it's the
difference between guessing and knowing.

> **Prime directive: measure the actual path, don't guess from aggregates.** "CPU
> is at 90%" is a symptom, not a diagnosis. eBPF and `perf` show you the exact
> functions, syscalls, files, and queries responsible — observe first, change
> second.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)                  | SOTA                                                              |
|---------------------------------------------|------------------------------------------------------------------|
| `top` and stare                             | `btop`/`atop` interactively; **PSI** (`/proc/pressure/*`) for real saturation |
| "high CPU" → kill something                 | `perf top` / on-CPU flame graph → the actual hot functions       |
| guess which files an app touches            | `opensnoop` (bcc/bpftrace) — every open() live, with PID + path  |
| guess why a fork storm is happening         | `execsnoop` — every new process exec, system-wide, in real time  |
| "disk is slow" hunch                        | `biolatency` (histogram of block-IO latency), `biosnoop`         |
| "network is slow" hunch                     | `tcplife`/`tcpconnect`/`tcpretrans` — per-connection truth       |
| `strace` everything (heavy, can stall prod) | targeted `strace -f -e trace=openat -p <pid>`; prefer eBPF in prod |
| add `printf` and redeploy                   | a one-line `bpftrace` probe on the function — no code change      |
| profile with print timestamps               | `perf record` + flame graph; off-CPU profiling for blocking      |
| read `/var/log` flat files                  | `journalctl -o json | jq` (structured, indexed)                  |

## The creed

1. **Observe before you change.** The first move on a slow system is to *measure
   the path*, not to restart or tune. Most "fixes" applied before measurement are
   superstition.
2. **Use a triage order (USE/RED).** For each resource — CPU, memory, disk, net —
   check **U**tilization, **S**aturation, **E**rrors. PSI (`/proc/pressure/{cpu,
   memory,io}`) gives saturation directly: it tells you whether work is *waiting*,
   which utilization alone hides.
3. **eBPF is the production microscope.** Safe, attach/detach live, minimal
   overhead. The bcc/bpftrace "tools" (`execsnoop`, `opensnoop`, `biolatency`,
   `tcplife`, `runqlat`, `cachestat`, …) answer the most common "what is it
   doing" questions out of the box. Learn five of them.
4. **`perf` + flame graphs for CPU.** `perf record -F 99 -g` then fold into a flame
   graph to see exactly where on-CPU time goes. Off-CPU profiling (eBPF) shows
   where it's *blocked* — often the real latency source.
5. **`strace`/`ltrace` are scalpels, not in prod by default.** They pause the
   target on every syscall and can wreck a hot service. Scope them tightly
   (`-e trace=`, one PID) or reach for eBPF, which doesn't stall the target.
6. **The kernel reports on itself.** `/proc/<pid>/{status,stack,wchan,sched}`,
   `/sys`, slabinfo, and PSI are structured truth. Tools are formatters over them.

## Triage in order (a worked path)

```bash
uptime                              # load average — is the box busy at all?
cat /proc/pressure/cpu              # PSI: is CPU work actually *waiting*? (saturation)
cat /proc/pressure/io               # PSI: is IO the bottleneck?
vmstat 1 5; mpstat -P ALL 1         # CPU/run-queue/context-switch overview
pidstat 1                           # per-process CPU/IO, repeating
```

Then drill with eBPF/perf into whichever resource PSI flags.

## eBPF tools (the high-value five)

```bash
execsnoop-bpfcc                     # every process exec, system-wide (catch fork storms)
opensnoop-bpfcc                     # every file open with PID + path (what is it reading?)
biolatency-bpfcc                    # histogram of block-IO latency (is the disk the problem?)
tcplife-bpfcc                       # each TCP connection: peers, bytes, duration
runqlat-bpfcc                       # scheduler run-queue latency (CPU contention)
```

Ad-hoc one-liners with `bpftrace` (no tool needed):

```bash
bpftrace -e 'tracepoint:syscalls:sys_enter_openat { @[comm] = count(); }'   # opens by process
bpftrace -e 'kprobe:vfs_read { @bytes = hist(arg2); }'                       # read-size histogram
bpftrace -e 'tracepoint:sched:sched_process_exec { printf("%s %d\n", str(args.filename), pid); }'
```

(Tool names vary: `execsnoop-bpfcc` on Debian/Ubuntu, `execsnoop` from
`bcc-tools` on Fedora/RHEL. `bpftrace` is the same everywhere.)

## CPU profiling with perf + flame graphs

```bash
perf top -g                                   # live, where on-CPU time goes right now
perf record -F 99 -a -g -- sleep 30           # sample the whole system for 30s
perf script | stackcollapse-perf.pl | flamegraph.pl > cpu.svg   # → interactive flame graph
```

## Targeted syscall tracing (scalpel)

```bash
strace -f -e trace=openat,connect -p <pid>    # only these syscalls, one process
strace -c -p <pid>                            # syscall count/time summary (then detach)
ltrace -p <pid>                               # library calls (less prod-safe; use carefully)
lsof -p <pid>                                 # open files/sockets snapshot (or ls /proc/<pid>/fd)
```

This is the layer beneath every other skill: when `linux-process-cgroups-sota`
says a service is hitting `MemoryMax`, eBPF/`/proc` tell you *why*; when
`linux-networking-sota` shows retransmits, `tcpretrans`/`tcplife` show *which
connections*. Observe with these, then act with the topic skill.
