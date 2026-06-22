---
name: linux-packaging-sota
description: >-
  Modern Linux software installation and environment management — use whenever the
  task involves installing software, package managers (apt/dnf/pacman), repos,
  dependencies, dev toolchains, or "set up a reproducible environment". Builds on
  the cheat-sheet's apt/dnf/pacman basics and adds the SOTA layer the image omits:
  **deb822 `.sources`** files over legacy one-line repos, **Flatpak** for desktop
  apps, **distrobox/toolbx (rootless Podman)** to install dev toolchains without
  polluting the host, **Nix** for reproducible/declarative packaging, unattended
  security upgrades, and image-based/OSTree distros (Silverblue/Bluefin) where the
  OS is updated as an atomic image. Reach for it on "install X", "add a repo", "set
  up a dev environment", "keep this reproducible", "auto-apply security updates",
  or "stop my host getting messy".
---

# Linux package management (SOTA)

The cheat-sheet's apt / dnf / pacman commands are correct and still the daily
drivers. What it misses is the modern *strategy*: stop turning your host into a
hand-tuned snowflake. The SOTA shift is toward **layering and reproducibility** —
isolate dev toolchains in containers, install desktop apps as sandboxed Flatpaks,
pin environments with Nix, and on image-based distros treat the OS as an atomic,
rollback-able image rather than a pile of mutated packages.

> **Prime directive: keep the host minimal and reproducible; layer everything
> else.** Every `sudo apt install build-essential …` on a production or daily host
> is drift. Put the toolchain in a `distrobox`, the app in a Flatpak, the project
> deps in Nix — and keep the base OS boring and rebuildable.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)                       | SOTA                                                              |
|--------------------------------------------------|------------------------------------------------------------------|
| `add-apt-repository` → one-line `.list`          | a **deb822 `.sources`** file in `/etc/apt/sources.list.d/` (signed-by) |
| `apt-key add` a key                              | drop the key in `/etc/apt/keyrings/` + reference it in the `.sources` |
| `sudo apt install gcc cmake nodejs …` on host    | `distrobox`/`toolbx` container — toolchain isolated from the host |
| install a GUI app from a random PPA              | **Flatpak** from Flathub — sandboxed, distro-agnostic, auto-updating |
| "works on my machine" toolchain                  | **Nix** (`nix shell`/`flake.nix`) — pinned, reproducible, per-project |
| `apt upgrade` when you remember                  | `unattended-upgrades` (Debian) / `dnf-automatic` for *security* patches |
| mutate the base OS forever                       | image-based (OSTree: `rpm-ostree`) — atomic updates + rollback   |
| `apt`/`apt-get` interchangeably in scripts       | `apt` interactively; **`apt-get`/`apt-cache`** in scripts (stable output) |
| `curl url | sudo bash` to install                | a real package, Flatpak, or container — never pipe-to-root        |
| forget what you installed                        | declare it: a Nix flake, a Containerfile, or a documented `.sources` |

## The creed

1. **The base OS should be boring.** Fewer packages on the host = less to break,
   patch, and audit. Resist installing dev/build tooling directly; that's what
   containers and Nix are for.
2. **Layer dev environments, don't install them.** `distrobox`/`toolbx` give a
   full mutable distro userland (any distro) tightly integrated with your home
   dir, backed by rootless Podman — install `gcc`, SDKs, weird deps there and
   throw it away when done. Your host stays clean.
3. **Sandbox desktop apps with Flatpak.** Distro-agnostic, sandboxed via
   portals/bubblewrap, updated independently of the OS. Flathub is the de-facto
   source. (Snap exists and is fine on Ubuntu; Flatpak is the cross-distro norm.)
4. **Reproduce with Nix where it matters.** A `flake.nix` pins exact versions of a
   project's toolchain so every machine and CI run is identical — the strongest
   answer to "works on my machine". Steeper learning curve; worth it for teams.
5. **Automate security updates.** Unapplied patches are the most common real-world
   compromise. `unattended-upgrades`/`dnf-automatic` for the *security* channel,
   reviewed feature upgrades on your cadence.
6. **Modern repo hygiene.** deb822 `.sources` files are multi-line, support
   `Signed-By:` per repo, and are far less error-prone than legacy one-liners +
   `apt-key` (deprecated). Keep keys in `/etc/apt/keyrings/`.
7. **Never `curl | sudo bash`.** It runs unaudited code as root and leaves nothing
   to update or remove. Prefer a packaged source you can verify and uninstall.

## deb822 repo (the modern `.list`)

```ini
# /etc/apt/sources.list.d/example.sources
Types: deb
URIs: https://repo.example.com/apt
Suites: stable
Components: main
Signed-By: /etc/apt/keyrings/example.gpg
```

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://repo.example.com/key.gpg | sudo tee /etc/apt/keyrings/example.gpg >/dev/null
sudo apt update
```

## Isolated dev toolchains (distrobox / toolbx)

```bash
distrobox create --name dev --image fedora:latest     # any distro userland
distrobox enter dev                                    # full shell, your $HOME mounted
# inside: dnf install -y gcc cmake ...  — none of it touches the host
toolbox create && toolbox enter                        # the Fedora-native equivalent
```

## Flatpak (desktop apps)

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub org.inkscape.Inkscape
flatpak update
flatpak override --nofilesystem=home org.some.App      # tighten the sandbox
```

## Nix (reproducible, per-project)

```bash
nix shell nixpkgs#nodejs_22 nixpkgs#go        # ephemeral env with exact versions
# flake.nix pins the whole toolchain; `nix develop` enters it. Same bits everywhere.
```

## Unattended security updates

```bash
sudo apt install unattended-upgrades && sudo dpkg-reconfigure unattended-upgrades  # Debian/Ubuntu
sudo systemctl enable --now dnf-automatic-install.timer                            # Fedora/RHEL
```

## Image-based / immutable distros

On Fedora Silverblue/Kinoite/Bluefin, openSUSE MicroOS, etc., the OS is an atomic
image: `rpm-ostree install pkg` *layers* onto a new deployment you boot into and
can roll back from. Day-to-day software goes in Flatpak + distrobox, not on the
base. This is the same "cattle not pets" philosophy as
`linux-storage-filesystems-sota` (snapshots) and `linux-boot-uki-sota` (atomic,
signed boot artifacts). For containerizing your *own* app rather than installing
others', see `linux-containers-namespaces-sota`.
