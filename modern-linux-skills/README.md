# Modern Linux SOTA Skill Pack

A family of Claude skills that take the popular **"12 Linux Concepts Every
Developer Must Know"** cheat-sheet and teach each concept *the way the running
system actually works in 2026* — not the ~2012 commands the cheat-sheet still
lists. The value isn't re-teaching the basics; it's the **legacy → SOTA** shift
each skill carries (`ifconfig→ip`, `netstat→ss`, `iptables→nft`, `chmod 777→ACL/
caps`, `cron→timer`, `sudo→run0`, `GRUB→UKI`, `LVM→btrfs subvol`).

Install target (same as the ETL pack):

`C:\Users\arunb\.claude\skills`

## Start here

- `modern-linux` — the umbrella/router (analogous to `idiomatic-code`). States the
  cross-topic creed once and points to the right topic skill. **Open this first.**

## The twelve concepts, modernized

Each row maps a cheat-sheet box to its skill and the headline shift.

| #  | Cheat-sheet concept            | Skill                              | Legacy → SOTA headline |
|----|--------------------------------|------------------------------------|------------------------|
| 1  | Linux architecture             | `linux-containers-namespaces-sota` | user/kernel split → **namespaces + cgroups v2 + caps + seccomp** |
| 2  | Filesystem hierarchy (FHS)     | `linux-storage-filesystems-sota`   | static FHS → **/usr-merge, /run, XDG, immutable /usr** |
| 3  | File permissions & `chmod`     | `linux-permissions-acl-caps-sota`  | `chmod 777`/setuid → **ACLs + file capabilities** |
| 4  | Process management             | `linux-process-cgroups-sota`       | `kill -9`/`nice` → **cgroup limits, `systemd-run`, oomd** |
| 5  | stdin/stdout/stderr & pipes    | `idiomatic-bash`                   | text scraping → **strict mode, procsub, `jq`/`jc` structured streams** |
| 6  | Users, groups & sudo           | `linux-users-auth-hardening-sota`  | raw `sudo`/`su` → **`run0`, polkit, key-only SSH, PAM** |
| 7  | Package management             | `linux-packaging-sota`             | `apt install` snowflake → **deb822, Flatpak, distrobox, Nix** |
| 8  | Shell scripting anatomy        | `idiomatic-bash`                   | naive `#!/bin/bash` → **`set -euo pipefail`, ShellCheck, `trap`** |
| 9  | Networking commands            | `linux-networking-sota`            | `ifconfig`/`netstat`/`iptables` → **`ip`/`ss`/`nftables`** |
| 10 | systemd & services             | `linux-systemd-sota`               | init scripts/`cron` → **units, timers, sandboxing, journal** |
| 11 | Disk & storage management      | `linux-storage-filesystems-sota`   | LVM+ext4 → **btrfs/ZFS subvols+snapshots, LUKS2, `fstrim`** |
| 12 | Linux boot process             | `linux-boot-uki-sota`              | GRUB hand-edit → **systemd-boot + UKI, TPM2 measured boot** |

## What the cheat-sheet omits entirely (the senior-operator gap)

| Skill                              | Why it matters |
|------------------------------------|----------------|
| `linux-containers-namespaces-sota` | the real isolation model: a container is a constrained process (8 namespaces + cgroups + caps + seccomp); rootless Podman, Buildah, **Quadlet** |
| `linux-observability-ebpf-sota`    | how you debug a box you can't `printf`: **eBPF** (`bpftrace`, `execsnoop`/`opensnoop`/`biolatency`/`tcplife`), `perf` + flame graphs, PSI, USE triage |

## Family conventions

- `idiomatic-bash` joins the existing **`idiomatic-code`** family (philosophy +
  reflex→idiomatic table + `references/`). Bash can't enforce types, so it leans
  on discipline + ShellCheck/shfmt to reach the same safety.
- The `*-sota` skills follow the same posture as the ETL pack: opinionated,
  single `SKILL.md`, copy-pasteable commands, cross-links between siblings.

## 2026 reality checks baked in

- cgroup **v1 and SysV init scripts removed** in systemd 258 → assume cgroup v2.
- **`run0`** (systemd ≥256) is the setuid-free `sudo` replacement.
- **UKIs** are the Secure-Boot/measured-boot artifact; GRUB hand-edits are legacy
  on UEFI.
- **btrfs/OpenZFS** are the production CoW filesystems; **bcachefs left mainline**
  (kernel 6.18, Sept 2025) → out-of-tree DKMS, not a default.
- The **journal is persistent by default** (systemd 259).

Usage: open `modern-linux` to pick the philosophy and the topic skill, then open
exactly the topic skill the table names.
