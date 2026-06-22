---
name: linux-containers-namespaces-sota
description: >-
  The real modern Linux isolation model — namespaces, cgroups, capabilities,
  seccomp — and running containers correctly. Use whenever the task involves
  containers (Docker/Podman/OCI), "what actually is a container", isolating a
  process, rootless containers, container security, or `docker-compose`-style
  service definitions. The cheat-sheet's "user space vs kernel space" is the 101
  view; this skill teaches what genuinely partitions a modern host: the **8 Linux
  namespaces**, **cgroup v2**, **capabilities**, **seccomp/LSM**, and OverlayFS —
  and the SOTA tooling on top: **rootless Podman** over the Docker daemon,
  **Buildah** for builds, and **Quadlet** to run containers as systemd units.
  Reach for it on "containerize this", "run this isolated", "why is my container
  root", "replace docker-compose", "make containers rootless", or "explain
  namespaces/cgroups".
---

# Linux containers & namespaces (SOTA)

The cheat-sheet's architecture page stops at "apps in user space, kernel in
privileged mode, syscalls bridge the gap". True — but it's the 1990s view. What
actually partitions a modern Linux host is **namespaces** (what a process can
*see*), **cgroups v2** (what it can *use*), and **capabilities + seccomp + LSMs**
(what it can *do*). A "container" is not a VM and not a magic box — it's a normal
process with those four knobs turned. Understanding that is the difference between
running containers and *operating* them.

> **Prime directive: a container is a constrained process, so constrain it.**
> Rootless, least-capabilities, seccomp-on, read-only-rootfs by default. The goal
> is that a compromised container can see almost nothing and do almost nothing.

## What a container actually is (the four pillars)

1. **Namespaces** — isolate the *view* of a global resource. The kernel has eight:
   `mount` (filesystem tree), `pid` (process IDs — its own PID 1), `net` (its own
   interfaces/ports/routes), `uts` (hostname), `ipc`, `user` (UID mapping — the
   key to rootless), `cgroup`, and `time`. `lsns` lists them; `unshare`/`nsenter`
   create/enter them by hand.
2. **cgroup v2** — limit and account the *usage*: CPU, memory, IO, PIDs. Same
   mechanism as `linux-process-cgroups-sota`; a container is just a cgroup.
3. **Capabilities** — slice up root. A container should hold the *minimum* caps
   (often none), not full root. See `linux-permissions-acl-caps-sota`.
4. **seccomp + LSM** — filter syscalls (`seccomp-bpf`) and apply mandatory access
   control (SELinux/AppArmor). The default seccomp profile blocks ~dozens of
   dangerous syscalls; keep it on.

Layered storage (**OverlayFS**) gives the copy-on-write image layers. That's the
whole trick — no virtualization, just kernel features composed.

## Break the muscle memory (reflex → SOTA)

| Reflex (common habit)                         | SOTA                                                              |
|-----------------------------------------------|------------------------------------------------------------------|
| Docker daemon running as root                 | **rootless Podman** — daemonless, runs as your user via userns    |
| `docker build`                                | `podman build` / **Buildah** (daemonless, scriptable, rootless)  |
| `docker-compose.yml` + a long-running daemon  | **Quadlet**: declare containers as systemd units (`.container`)   |
| `--privileged` to "make it work"              | grant the one capability needed; keep seccomp + read-only rootfs |
| run as root inside the container              | `USER` a non-root UID; rootless maps it to an unprivileged host UID |
| writable container rootfs                     | `--read-only` + explicit `--tmpfs`/volumes for writable paths    |
| `:latest` image tag                           | pin by digest (`@sha256:…`) for reproducibility                  |
| huge image with build tools baked in          | multi-stage build → minimal/distroless runtime image            |
| "container = lightweight VM" mental model     | container = constrained process (namespaces + cgroups + caps)    |
| `docker run` and forget restart/logging       | Quadlet unit → `Restart=`, journal logging, boot integration     |

## The creed

1. **Rootless by default.** A **user namespace** maps in-container root to an
   unprivileged host UID, so a container breakout lands as nobody, not root.
   Podman is rootless-native; it's the single biggest container security win.
2. **Daemonless where you can.** Podman/Buildah run as your user with no
   privileged background daemon — smaller attack surface, better multi-user story,
   and `podman generate`/Quadlet integrate cleanly with systemd.
3. **Least privilege inside, too.** Drop all caps and add back only what's needed;
   keep the default seccomp profile; run a non-root `USER`; mount the rootfs
   read-only with explicit writable volumes. `--privileged` is a code smell.
4. **Run containers as systemd units (Quadlet).** Instead of a compose daemon,
   describe each container in a `.container` file; systemd gives you `Restart=`,
   ordering, journald logging, resource limits, and boot integration — one model
   for all services (see `linux-systemd-sota`).
5. **Reproducible images.** Pin base images by digest, prefer multi-stage builds
   to ship a minimal runtime (distroless/`scratch`), and scan images. An image is
   a build artifact; treat it like one.
6. **Understand the pillars so you can debug them.** When a container "can't see
   the network" or "is killed at 512M", you're looking at a net namespace or a
   cgroup memory limit — not magic.

## See the pillars directly

```bash
lsns                                   # all namespaces and the processes in them
unshare --user --map-root-user --pid --fork --mount-proc bash   # a tiny container by hand
nsenter -t <pid> -n ss -tulpn          # run ss inside another process's net namespace
cat /proc/<pid>/cgroup                 # which cgroup (→ limits) a process is in
grep CapEff /proc/<pid>/status         # effective capabilities of a process
```

## Rootless Podman

```bash
podman run --rm -it --read-only --cap-drop=ALL --user 1000:1000 alpine sh
podman run -d --name web -p 8080:80 docker.io/library/nginx:1.27
podman ps; podman logs web; podman inspect web | jq '.[0].State'
podman build -t myapp:1.0 .            # or: buildah bud -t myapp:1.0 .
podman image scan myapp:1.0            # (or trivy) — check for known CVEs
```

## Quadlet (containers as systemd units — the compose replacement)

```ini
# /etc/containers/systemd/web.container   (or ~/.config/containers/systemd/ for rootless)
[Container]
Image=docker.io/library/nginx:1.27
PublishPort=8080:80
ReadOnly=true
DropCapability=ALL
NoNewPrivileges=true

[Service]
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload                # Quadlet generates a real .service from the .container
systemctl enable --now web.service
journalctl -u web -f
```

This unifies containers with every other service on the box: same `systemctl`,
same journal, same cgroup resource control (`linux-process-cgroups-sota`), same
sandboxing vocabulary (`linux-systemd-sota`). For debugging what a containerized
process is *actually doing* at the syscall/kernel level, use
`linux-observability-ebpf-sota`.
