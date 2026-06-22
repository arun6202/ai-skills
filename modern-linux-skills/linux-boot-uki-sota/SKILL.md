---
name: linux-boot-uki-sota
description: >-
  Modern Linux boot, bootloader, and initrd management — use whenever the task
  involves the boot process, bootloaders (GRUB/systemd-boot), the kernel command
  line, initramfs/initrd, Secure Boot, slow boots, or "the system won't boot /
  boots to emergency mode". Steers from the cheat-sheet's GRUB-hand-edit picture
  toward SOTA practice on UEFI machines: **systemd-boot (sd-boot)** over GRUB,
  **Unified Kernel Images (UKIs)** built with `ukify`/`kernel-install` for Secure
  Boot and measured boot, `dracut` for initramfs, `bootctl` to manage entries,
  **TPM2 measured boot** with LUKS auto-unlock, and `systemd-analyze` for boot
  performance. Reach for it on "set up the bootloader", "add a kernel parameter",
  "enable Secure Boot", "rebuild the initramfs", "speed up boot", or boot-failure
  triage.
---

# Linux boot process (SOTA)

The cheat-sheet's timeline — firmware/POST → bootloader → kernel → initramfs →
systemd → targets → login — is the correct mental model and worth memorizing. But
two things on it are legacy on a modern UEFI machine: **GRUB** (heavy, its own
config language, awkward with Secure Boot) and the assumption of a **separate
kernel + initrd + cmdline** you wire together by hand. The SOTA artifact is the
**UKI**: kernel + initrd + cmdline + signature in one signed EFI binary that
firmware can verify and the TPM can measure.

> **Prime directive: on UEFI, ship a signed UKI booted by sd-boot, with measured
> boot tying disk-unlock to a known-good chain.** Fewer moving parts, real Secure
> Boot, and TPM-sealed secrets that only release if the boot wasn't tampered with.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)                  | SOTA                                                              |
|---------------------------------------------|------------------------------------------------------------------|
| GRUB as the obvious bootloader              | **systemd-boot** (`bootctl install`) on UEFI — tiny, no scripting |
| Separate vmlinuz + initrd + `grub.cfg`      | **UKI**: one signed `.efi` (kernel+initrd+cmdline) via `ukify`/`kernel-install` |
| Edit `GRUB_CMDLINE_LINUX` + `update-grub`   | `/etc/kernel/cmdline` (UKI) or sd-boot entry; rebuild the image  |
| `mkinitramfs`/initramfs-tools hooks         | **dracut** (modular, used across most distros now)               |
| Secure Boot "off, too much hassle"          | sign the UKI/shim; firmware verifies the whole boot artifact     |
| LUKS passphrase typed at every boot         | **TPM2-sealed** unlock (`systemd-cryptenroll --tpm2-device=auto`) |
| Guess why boot is slow                      | `systemd-analyze` / `blame` / `critical-chain` / `plot`          |
| `init=/bin/bash` rescue hacks               | a proper sd-boot/UKI recovery entry; `rd.break` for initrd shell |
| Pass kernel params by editing GRUB live     | edit the entry once in sd-boot, or `/etc/kernel/cmdline` + rebuild |

## The creed

1. **The boot artifact should be one signed, measurable unit.** A UKI bundles
   kernel, initrd, and cmdline (and can embed microcode and firmware) into a
   single PE/EFI binary you sign once. Secure Boot verifies *that*, and the TPM
   measures *that* — no gap where an unsigned initrd or edited cmdline sneaks in.
2. **Prefer sd-boot on UEFI.** It just enumerates `.efi`/UKI entries in the ESP
   (`/efi` or `/boot`), shows a menu, and hands off. No Turing-complete config to
   misconfigure. GRUB still earns its place for BIOS/legacy, complex multi-boot,
   or btrfs-snapshot menus — pick deliberately.
3. **Measured boot over "Secure Boot on, done".** TPM2 PCRs record each boot
   stage; seal your LUKS key to a known PCR policy so the disk auto-unlocks *only*
   if the boot chain is unchanged. Tamper → unlock fails → you notice.
4. **dracut for the initramfs.** Modular, host-only or generic, the de-facto tool.
   Know how to rebuild it and how to drop to its emergency shell (`rd.break`).
5. **Treat boot time as a budget.** `systemd-analyze blame` and `critical-chain`
   tell you which units and which *dependency path* gate boot — optimize the
   chain, not whatever happens to be slowest in isolation.
6. **Know the rescue paths cold.** Emergency/rescue targets, the initrd shell, and
   a recovery entry are the difference between a 2-minute fix and a reinstall.

## The sequence (with the modern names)

`UEFI firmware (POST, Secure Boot verify)` → `sd-boot / shim` (reads the ESP) →
`UKI (.efi)`: stub (`sd-stub`) measures + extracts → `kernel` → `initramfs`
(dracut: load storage/crypto drivers, **TPM2-unlock LUKS**, find + mount real
root) → `systemd (PID 1)` → reaches `multi-user.target`/`graphical.target` →
login. Compared to the cheat-sheet: GRUB→sd-boot, and "kernel+initrd" collapses
into the signed UKI.

## systemd-boot + UKI

```bash
bootctl install                         # install sd-boot to the ESP
bootctl status                          # firmware + loader + entries + Secure Boot state
bootctl list                            # enumerate boot entries

# Kernel cmdline for UKIs lives here (rebuild the image after editing):
cat /etc/kernel/cmdline                 # e.g. "rw quiet rd.luks.options=tpm2-device=auto"
kernel-install add "$(uname -r)" /lib/modules/$(uname -r)/vmlinuz   # build+install UKI
ukify build --linux=vmlinuz --initrd=initrd.img --cmdline=@/etc/kernel/cmdline \
            --secureboot-private-key=db.key --secureboot-certificate=db.crt -o uki.efi
```

## initramfs with dracut

```bash
dracut --force                          # rebuild initramfs for the running kernel
dracut --force --kver 6.12.0            # for a specific kernel
lsinitrd | less                         # inspect what's inside the initramfs
# Emergency: append rd.break to the cmdline to drop to a shell inside the initrd
```

## TPM2-sealed disk unlock

```bash
systemd-cryptenroll --tpm2-device=auto --tpm2-prs=7 /dev/nvme0n1p3   # seal to PCR 7
# crypttab then auto-unlocks at boot if the measured chain matches:
# cryptdata UUID=...  none  tpm2-device=auto
```

## Boot performance & rescue

```bash
systemd-analyze                         # firmware/loader/kernel/userspace timings
systemd-analyze blame                   # slowest units
systemd-analyze critical-chain          # the dependency path that actually gated boot
systemctl rescue                        # single-user-ish maintenance mode
systemctl emergency                     # most minimal recovery target
```

The userspace half of boot (units, targets, ordering) is `linux-systemd-sota`; the
encrypted root this unlocks is set up in `linux-storage-filesystems-sota`; signing
keys and Secure Boot enrollment intersect with platform hardening in
`linux-users-auth-hardening-sota`.
