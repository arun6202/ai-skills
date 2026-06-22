---
name: linux-storage-filesystems-sota
description: >-
  Modern disk, partition, filesystem, and mount management — use whenever the task
  involves disks/partitions, filesystems (ext4/xfs/btrfs/zfs), LVM, mounting,
  `/etc/fstab`, encryption, snapshots, free space, or "add/resize/encrypt a
  volume". Steers from the cheat-sheet's LVM-on-ext4 + device-name fstab toward
  SOTA practice: **btrfs/ZFS subvolumes with copy-on-write snapshots** (snapshot
  before every risky change), LUKS2 full-disk encryption, **UUID/PARTUUID-pinned**
  mounts and `systemd.mount` units, SSD/NVMe care (`fstrim`/discard), and the
  modern inspectors (`lsblk`, `findmnt`, `blkid`, `duf`/`dust`/`ncdu`). Also covers
  the FHS in its modern form (/usr-merge, /run, XDG, immutable /usr). Reach for it
  on "set up storage", "make a snapshot", "encrypt this disk", "why is fstab not
  mounting", "what's filling the disk", or filesystem-choice questions.
---

# Linux storage & filesystems (SOTA)

The cheat-sheet's stack — physical disk → partitions → ext4/xfs → mount, with LVM
underneath — still works and is fine for many servers. But the SOTA default for
anything where you care about **data integrity and reversible changes** is a
copy-on-write filesystem (**btrfs** or **OpenZFS**): checksummed data, instant
snapshots, send/receive, and built-in volume management that subsumes most of
what LVM did. And the cheat-sheet's device-name `fstab` (`/dev/sda1`) is a
reboot-roulette bug waiting to happen.

> **Prime directive: checksum your data, snapshot before you change it, and pin
> mounts by UUID.** Device names reorder; UUIDs don't. CoW snapshots make "oops"
> a one-command rollback instead of a restore-from-backup incident.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)                    | SOTA                                                            |
|-----------------------------------------------|----------------------------------------------------------------|
| LVM + ext4 for everything                     | **btrfs subvolumes** (or ZFS datasets) — CoW, checksums, snapshots |
| `fstab` line by `/dev/sda1`                   | by `UUID=` or `PARTUUID=` (`blkid` to find it) — survives reorder |
| Back up before a risky upgrade                | `btrfs subvolume snapshot` / `zfs snapshot` first — instant, rollback-able |
| `fdisk` MBR partitioning                      | GPT via `parted`/`sgdisk`/`fdisk` (modern fdisk does GPT)       |
| Plaintext disk                                | **LUKS2** (`cryptsetup luksFormat`), ideally TPM2-bound auto-unlock |
| `df -h` and eyeball                           | `duf` (pretty df), `dust`/`ncdu` to find *what* is big          |
| `du -sh *` to hunt big dirs                   | `ncdu` (interactive) / `dust` (visual tree)                    |
| Manually edit fstab then reboot to test       | `systemd-mount` / `findmnt --verify`; `mount -a` to test first  |
| Ignore SSD trim                               | enable `fstrim.timer` (weekly TRIM) — keeps SSD/NVMe healthy   |
| Resize ext4 with downtime                     | btrfs/xfs online grow; `btrfs filesystem resize`, `xfs_growfs`  |
| `mount` device on a path imperatively         | a `.mount` unit or fstab entry — declarative, boot-persistent  |

## The creed

1. **Copy-on-write by default.** btrfs/ZFS checksum every block (catching silent
   corruption ext4 can't see), snapshot in O(1), and support compression and
   send/receive. Use a CoW filesystem unless you have a specific reason (e.g. a
   database that wants `nodatacow`, or XFS for certain large-file workloads).
2. **Snapshot before change.** The cheapest insurance in Linux. Before a package
   upgrade, config edit, or migration: snapshot. Tools like `snapper` or `timeshift`
   automate this on btrfs; the rollback is a metadata operation.
3. **Pin mounts by identity, not by name.** `UUID=`/`PARTUUID=`/`LABEL=` in fstab
   so adding a disk or a kernel reordering `sd*` doesn't fail the boot. Test with
   `mount -a` / `findmnt --verify` *before* rebooting.
4. **Encrypt at rest with LUKS2.** Whole-block-device encryption; bind unlock to
   the TPM2 (`systemd-cryptenroll --tpm2-device=auto`) for unattended boot, or to
   FIDO2/recovery key. Don't ship laptops or portable disks unencrypted.
5. **Care for SSD/NVMe.** Enable periodic TRIM (`fstrim.timer`) rather than the
   continuous `discard` mount option (which can hurt throughput). Mind alignment;
   modern tools handle it, but verify on manual partitioning.
6. **Inspect with the structured tools.** `lsblk` (tree of devices), `findmnt`
   (mount tree), `blkid` (UUID/type) — all take `--json`. Reach for `ncdu`/`dust`
   to answer "what's filling the disk", not a wall of `du`.

## Inspect

```bash
lsblk -f                      # tree of devices with FS type, UUID, mountpoint
findmnt /                     # what's mounted there, with options
blkid /dev/nvme0n1p2          # UUID + filesystem type (for fstab)
duf                           # readable df across all mounts
ncdu /var                     # interactive: drill into what's using space
btrfs filesystem usage /      # real btrfs space accounting (df lies on CoW)
```

## btrfs snapshots (the headline feature)

```bash
btrfs subvolume list /                                  # list subvolumes
btrfs subvolume snapshot -r / /.snapshots/pre-upgrade   # read-only snapshot, instant
# ... do the risky thing ...
btrfs subvolume snapshot /.snapshots/pre-upgrade /      # roll back (or set as default)
btrfs scrub start /                                     # verify checksums, repair from copies
```

ZFS equivalent: `zfs snapshot pool/data@pre-upgrade`, `zfs rollback`,
`zfs scrub pool`. (Note: **bcachefs** left the mainline kernel in 6.18 / Sept
2025 and is now an out-of-tree DKMS module — not a default choice yet.)

## Encryption (LUKS2)

```bash
cryptsetup luksFormat --type luks2 /dev/nvme0n1p3       # create encrypted volume
cryptsetup open /dev/nvme0n1p3 cryptdata                 # unlock → /dev/mapper/cryptdata
mkfs.btrfs /dev/mapper/cryptdata
systemd-cryptenroll --tpm2-device=auto /dev/nvme0n1p3    # bind unlock to the TPM2
```

## fstab, done right

```fstab
# <UUID>                                   <mount>  <fstype> <options>                 <dump> <pass>
UUID=1234-abcd                              /        btrfs    subvol=@,compress=zstd,noatime  0 0
UUID=5678-ef01                              /home    btrfs    subvol=@home,noatime            0 0
```

Always `mount -a` after editing and before rebooting; a typo here can drop you to
emergency mode. Or declare mounts as `systemd .mount`/`.automount` units for
on-demand mounting.

## The FHS, modernized (cheat-sheet #2)

The hierarchy is stable, with modern refinements worth knowing:

- **/usr-merge:** `/bin`, `/sbin`, `/lib` are now symlinks into `/usr` on current
  distros — treat `/usr` as the single home of the OS, enabling read-only/immutable
  `/usr` (OSTree, image-based systems).
- **/run:** tmpfs for runtime state (replaced `/var/run`); gone on reboot.
- **XDG base dirs:** user data/config/cache live under `~/.local/share`,
  `~/.config`, `~/.cache` (the `$XDG_*` vars), not scattered dotfiles.
- **/etc layering:** many configs ship vendor defaults in `/usr/lib/...` and let
  you override under `/etc` (the systemd drop-in pattern); `systemd-confext` can
  layer `/etc` on immutable systems.
- **/proc, /sys, /dev** are virtual kernel interfaces, not disk — the real "API
  surface" of the kernel (see `linux-observability-ebpf-sota`).

For *which CoW features map to your workload* and snapshot automation policy,
combine this with `linux-systemd-sota` (a `.timer` running `btrfs scrub`/`fstrim`)
and `linux-boot-uki-sota` (encrypted root + TPM2 unlock at boot).
