---
name: modern-linux
description: >-
  The shared house style for operating, configuring, and reasoning about Linux
  the modern, correct-by-default way — and the router to the per-topic Linux
  skills. Use this whenever the task touches Linux administration, the shell,
  permissions, processes, services, networking, storage, boot, packaging,
  containers, or debugging — even a casual "how do I check listening ports" or
  "write a startup script". Most cheat-sheet Linux is a decade behind the
  running system: it reaches for `ifconfig`, `netstat`, `iptables`, `chmod 777`,
  `cron`, raw `sudo`, GRUB hand-edits, and LVM+ext4 when the SOTA stack is `ip`,
  `ss`, `nftables`, ACLs/capabilities, systemd timers, `run0`, UKIs, and
  btrfs/ZFS snapshots. This skill states the cross-topic creed once
  (everything-is-an-fd, declarative-over-imperative, systemd-is-the-platform,
  least-privilege-by-construction, observability-over-guesswork, immutable and
  reproducible) and points to the right topic skill for the concrete commands.
  Reach for it as the umbrella; reach for the topic skill it names for specifics.
---

# Modern Linux — the house style

One operating system, twelve concerns. The classic "Linux concepts every dev
must know" cheat-sheet is a fine *map of the territory*, but its **commands are
frozen ~2012**: `ifconfig`, `netstat`, `iptables`, `route`, `chmod 777`, raw
`cron`, hand-edited GRUB, init scripts, LVM-on-ext4. The system you actually run
in 2026 moved on. This meta-skill states the shared philosophy and routes you to
the topic skill that turns it into current syntax.

> **Prime directive: target the running system, not the textbook.** When your
> muscle memory fires a legacy tool, prefer its modern successor — it is not
> nostalgia, it is that the successor is structured, scriptable, namespaced, and
> still maintained. Each topic skill carries a **legacy → SOTA** reflex table.

## The creed (apply across every topic)

1. **Everything is a file descriptor, and the kernel exposes itself as files.**
   `/proc`, `/sys`, `/dev`, cgroupfs, and `bpffs` are the real API. Read state
   from there; don't scrape `ps`/`ifconfig` text when a structured source exists.
2. **Declarative over imperative.** A unit file, a `.network` file, an `fstab`
   line by UUID, a `nft` ruleset, a `tmpfiles.d` drop-in — describe the desired
   state and let the system converge. Imperative one-liners are for exploration,
   not for configuration that must survive reboot.
3. **systemd is the platform, not just an init.** Services, timers, sockets,
   logind, resolved, networkd, homed, `run0`, sandboxing, credentials, and
   cgroup resource control are one coherent surface. Learn it as a platform.
4. **Least privilege by construction.** Capabilities over the setuid bit, ACLs
   over `chmod 777`, `run0`/polkit over blanket `sudo`, rootless containers,
   per-service sandboxing. Privilege should be *dropped*, never casually granted.
5. **Namespaces + cgroups v2 are the real architecture.** "User space vs kernel
   space" is the 101 view; isolation (8 namespaces) and resource control (one
   unified cgroup v2 tree) are how modern Linux actually partitions a host.
6. **Observe, don't guess.** `/proc`, PSI, `perf`, and eBPF (`bpftrace`, bcc)
   answer "what is it actually doing" without printf-debugging the kernel.
7. **Immutable and reproducible where it counts.** UUID-pinned mounts, UKIs,
   image-based/OSTree systems, declarative packages, snapshots before change.
   Treat servers as cattle: rebuildable, not hand-tuned snowflakes.
8. **Text streams are an interface — make them structured.** Pipes are great;
   parsing fragile ASCII tables is not. Reach for `-j/--json` flags, `jq`, `jc`,
   and `yq` so a pipeline carries data, not whitespace.

## The twelve concepts, modernized (router)

Each row maps a cheat-sheet concept to the skill that teaches its SOTA form.

| Cheat-sheet concept            | The headline legacy→SOTA shift                         | Skill to open |
|--------------------------------|-------------------------------------------------------|---------------|
| 1. Linux architecture          | user/kernel split → **namespaces + cgroups v2**       | `linux-containers-namespaces-sota` |
| 2. Filesystem hierarchy (FHS)  | static FHS → **/usr-merge, /run, XDG, immutable /usr** | `linux-storage-filesystems-sota` |
| 3. Permissions & `chmod`       | `chmod 777`/setuid → **ACLs + file capabilities**     | `linux-permissions-acl-caps-sota` |
| 4. Process management          | `kill -9`/`nice` → **cgroup limits, `systemd-run`, oomd** | `linux-process-cgroups-sota` |
| 5. stdin/stdout/stderr & pipes | text scraping → **strict mode, procsub, structured streams** | `idiomatic-bash` |
| 6. Users, groups & sudo        | raw `sudo`/`su` → **`run0`, polkit, key-only SSH, PAM** | `linux-users-auth-hardening-sota` |
| 7. Package management          | `apt install` snowflake → **deb822, Flatpak, distrobox, Nix** | `linux-packaging-sota` |
| 8. Shell scripting anatomy     | naive `#!/bin/bash` → **`set -euo pipefail`, ShellCheck, `trap`** | `idiomatic-bash` |
| 9. Networking commands         | `ifconfig`/`netstat`/`iptables` → **`ip`/`ss`/`nftables`** | `linux-networking-sota` |
| 10. systemd & services         | init scripts/`cron` → **units, timers, sandboxing, journal** | `linux-systemd-sota` |
| 11. Disk & storage             | LVM+ext4 → **btrfs/ZFS subvols+snapshots, LUKS2, `fstrim`** | `linux-storage-filesystems-sota` |
| 12. Linux boot process         | GRUB hand-edit → **systemd-boot + UKI, TPM2 measured boot** | `linux-boot-uki-sota` |

Plus the two concerns the cheat-sheet omits entirely, which are where a senior
operator actually lives: **`linux-containers-namespaces-sota`** (the real
isolation model) and **`linux-observability-ebpf-sota`** (how you debug a box you
can't `printf`).

## How to use this family

- Start here to pick the philosophy and the right topic skill.
- Open exactly the topic skill the table names; each is self-contained with its
  own reflex table, creed, and copy-pasteable commands.
- When a task spans topics (e.g. "ship a hardened service that listens on 443"),
  pull `linux-systemd-sota` (unit + sandbox), `linux-networking-sota` (nft +
  socket), and `linux-users-auth-hardening-sota` (least privilege) together.
- These are **operations** skills. For *writing the script itself* idiomatically,
  `idiomatic-bash` is the shell-language skill and joins the `idiomatic-code`
  family already in this pack.

## Stable ground vs moving edge (2026 reality check)

- **cgroup v1 is gone.** systemd 258 removed it; assume **cgroup v2 unified
  hierarchy** everywhere. SysV init scripts were removed in the same release.
- **`run0` (systemd ≥256) is the modern privilege path** — a transient unit run
  by PID 1 under polkit, dropping rather than gaining privilege; no setuid.
- **UKIs are the boot artifact** for Secure Boot + measured boot; GRUB hand-edits
  are legacy on UEFI systems.
- **btrfs and OpenZFS are the production COW filesystems**; bcachefs left
  mainline (kernel 6.18, Sept 2025) and is now out-of-tree DKMS — not a default.
- The journal is now **persistent by default** (systemd 259) — stop assuming logs
  vanish on reboot.

When a fact here could have moved, say so and check `systemctl --version`,
`uname -r`, and the distro release rather than trusting memory.
