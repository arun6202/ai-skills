---
name: linux-networking-sota
description: >-
  Modern Linux networking commands and configuration — use whenever the task
  involves interfaces, IP addresses, routes, listening ports, firewalls, DNS, or
  "what's connecting to/from this box". Steers hard off the deprecated net-tools
  the cheat-sheet still lists (`ifconfig`, `netstat`, `route`, `arp`) and the
  legacy `iptables`, toward the SOTA stack: the **`iproute2`** suite (`ip`, `ss`),
  **`nftables`**/`firewalld` for filtering, `resolvectl`/systemd-resolved and
  `dig +short`/`drill` for DNS, `nmcli` (NetworkManager) and systemd-networkd for
  declarative config, `mtr` over `traceroute`, and `curl`/`xh` for HTTP. Reach for
  it on "show my IP/interfaces", "check listening ports", "open/block a port",
  "why can't this host resolve", "set a static IP", or any connectivity-debugging
  task.
---

# Linux networking (SOTA)

The cheat-sheet's networking box is the most *outdated* page in it: `ifconfig`,
`netstat`, and `route` come from **net-tools, deprecated for over a decade** and
absent from minimal modern images. The replacements aren't just renames — `ip`
and `ss` expose things net-tools can't (namespaces, multiple addresses, socket
internals), and `nftables` replaces the four separate `*tables` binaries with one
coherent ruleset.

> **Prime directive: `iproute2` + `nftables`, not net-tools + iptables.** If a
> command starts with `ifconfig`, `netstat`, `route`, or `arp`, there is a better
> one-to-one replacement that's installed, scriptable, and namespace-aware.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)              | SOTA                                                          |
|-----------------------------------------|--------------------------------------------------------------|
| `ifconfig`                              | `ip addr` (`ip a`) / `ip -br a` for a brief table            |
| `ifconfig eth0 up/down`                 | `ip link set eth0 up` / `down`                               |
| `route -n` / `route add`                | `ip route` (`ip r`) / `ip route add`                         |
| `netstat -tulpn`                        | `ss -tulpn` (faster, same flags, more socket detail)         |
| `netstat -i` / interface stats          | `ip -s link`                                                 |
| `arp -a`                                | `ip neigh`                                                   |
| `iptables -A ...`                       | `nft add rule ...` / manage via `firewalld` or `ufw`         |
| `traceroute host`                       | `mtr host` (continuous, loss+latency per hop)                |
| `nslookup host`                         | `dig +short host` / `drill host` / `resolvectl query host`   |
| edit `/etc/resolv.conf` by hand         | `resolvectl` + systemd-resolved (the file is often a symlink) |
| static IP in `/etc/network/interfaces`  | `nmcli` (NetworkManager) or a `.network` file (systemd-networkd) |
| `wget`/`curl` text-scrape               | `curl`/`xh`/`httpie`; add `-w`/`-s` and pipe JSON to `jq`     |
| `ping` only                             | `ping` for reachability; `mtr`/`ss`/`ip` for *why* it fails  |

## The creed

1. **`iproute2` is the interface to the kernel's networking.** One tool family
   (`ip`, `ss`, `tc`, `bridge`) over the modern netlink API. It sees everything:
   multiple addresses per interface, policy routing, network namespaces, VRFs.
2. **`ss` over `netstat` for sockets.** It reads `/proc` and netlink directly,
   is faster on busy hosts, and shows socket state, timers, and owning process
   (`-p`) cleanly. Same `-tulpn` mnemonic you already know.
3. **One firewall ruleset with `nftables`.** `nft` replaces iptables/ip6tables/
   arptables/ebtables with a single grammar, atomic ruleset reloads, sets/maps,
   and dual IPv4/IPv6 rules. On servers, manage it through `firewalld`; on
   desktops/simple hosts, `ufw` is a friendly front-end. Default policy: drop.
4. **DNS goes through the resolver, not the file.** `/etc/resolv.conf` is usually
   a stub managed by `systemd-resolved` or NetworkManager. Use `resolvectl` to
   query, flush caches, and see per-link DNS; it also enables DNS-over-TLS.
5. **Configure declaratively.** A static IP belongs in an `nmcli` connection
   profile or a systemd `.network` file — surviving reboot and visible to the
   stack — not in an imperative `ip` command that vanishes on reboot.
6. **Diagnose in layers.** Link up? (`ip link`) Address? (`ip addr`) Route?
   (`ip route get <dst>`) Name resolves? (`resolvectl query`) Port open and
   listening? (`ss -ltnp`) Reachable + where it breaks? (`mtr`). Don't jump to
   "DNS is broken" before checking the link.

## Inspect (the daily commands)

```bash
ip -br a                       # brief: iface, state, addresses
ip -s link                     # interface counters (rx/tx, errors, drops)
ip route get 1.1.1.1           # which route+source IP the kernel would use
ip neigh                       # ARP/neighbour table
ss -tulpn                      # listening TCP/UDP sockets + owning process
ss -tnp state established      # active connections with PIDs
ss -s                          # socket summary by state
```

## Firewall with nftables

```bash
nft list ruleset                                   # current rules (the whole config)
# Minimal stateful host firewall (idempotent file: nft -f /etc/nftables.conf):
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add rule  inet filter input ct state established,related accept
nft add rule  inet filter input iif lo accept
nft add rule  inet filter input tcp dport {22,443} accept
```

Or, higher level:

```bash
firewall-cmd --add-service=https --permanent && firewall-cmd --reload   # firewalld
ufw allow 443/tcp && ufw enable                                          # ufw
```

## DNS

```bash
dig +short example.com               # just the answer
resolvectl query example.com         # via systemd-resolved (respects per-link DNS)
resolvectl status                    # per-link servers, DNSSEC/DoT state
resolvectl flush-caches              # clear the resolver cache
```

## Configure (declarative)

```bash
# NetworkManager (most desktops/servers):
nmcli con add type ethernet ifname eth0 con-name lan ip4 192.0.2.10/24 gw4 192.0.2.1
nmcli con mod lan ipv4.dns "1.1.1.1 9.9.9.9"
nmcli con up lan
```

```ini
# systemd-networkd: /etc/systemd/network/10-lan.network
[Match]
Name=eth0
[Network]
Address=192.0.2.10/24
Gateway=192.0.2.1
DNS=1.1.1.1
```

For modern VPN/overlay, prefer **WireGuard** (`wg`, `wg-quick`, or a `.netdev`)
over legacy IPsec for most cases. To watch traffic, `tcpdump`/`tshark` capture
packets; for *programmatic* socket/latency tracing use eBPF tooling in
`linux-observability-ebpf-sota`. Exposing a service safely (socket activation,
sandbox) is `linux-systemd-sota`.
