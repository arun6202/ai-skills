---
name: linux-users-auth-hardening-sota
description: >-
  Modern user, group, privilege-escalation, and login hardening — use whenever
  the task involves users/groups, `sudo`/`su`/root, SSH access, `/etc/passwd` and
  `/etc/shadow`, PAM, or "secure this server day one". Steers from raw `sudo`/`su`
  toward the SOTA path: `run0` (systemd's setuid-free sudo replacement) and
  polkit, key-only/hardened SSH with certificates, `sudoers.d` drop-ins done
  safely with `visudo`, PAM-based controls, `systemd-homed`/userdb, service
  accounts with `nologin`, and brute-force defense (fail2ban/sshguard). Reach for
  it on "give this user sudo", "lock down SSH", "create a service account",
  "harden a fresh VM", or any privilege-escalation question.
---

# Linux users, auth & hardening (SOTA)

The cheat-sheet's UID/GID model and "su = switch user, sudo = superuser do" are
correct foundations. What it misses is that **privilege escalation and login are
now the hardened surface of a box** — and that the modern tools (`run0`, polkit,
key-only SSH, PAM, homed) give you escalation that *drops* privilege and login
that can't be brute-forced.

> **Prime directive: identities are cheap, root is expensive.** Give each human a
> named account and each daemon its own service account; reach root through an
> audited, narrowly-scoped path; and make password login over the network simply
> not exist.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)                   | SOTA                                                                |
|----------------------------------------------|--------------------------------------------------------------------|
| `sudo -i` / `su -` to "become root"          | `run0` (systemd ≥256): transient root unit via PID 1 + polkit, no setuid |
| Edit `/etc/sudoers` directly                 | `visudo -f /etc/sudoers.d/90-deploy` — validated drop-in, never the main file |
| `usermod -aG sudo bob` and move on           | grant the *specific* commands in a `sudoers.d` rule, not blanket root |
| Password SSH login                           | key-only: `PasswordAuthentication no`, ideally **SSH certificates** |
| Root SSH login enabled                       | `PermitRootLogin no`; log in as a user, escalate locally           |
| Shared admin account everyone logs into      | one named account per human; `run0`/sudo for escalation = audit trail |
| Service runs as `root` because "it's easier" | dedicated `--system` user with `nologin`, or `DynamicUser=` in the unit |
| `adduser svc` for a daemon                   | `useradd --system --no-create-home --shell /usr/sbin/nologin svc`  |
| Hope nobody brute-forces SSH                 | `fail2ban`/`sshguard` + key-only + non-default exposure            |
| `passwd` policy in your head                 | enforce via PAM (`pam_pwquality`, `pam_faillock`)                  |

## The creed

1. **Named identities, always.** Every human gets their own account; every daemon
   gets its own system account. Shared logins destroy accountability and the
   audit trail. The whole point of `run0`/`sudo` is *who did what as root, when*.
2. **Escalate by dropping, not gaining.** `run0` runs your command as a transient
   unit started by PID 1 — privileges are dropped into the session under polkit
   policy, not handed up through a setuid binary. It tints the terminal red and
   flags the prompt so you *know* you're elevated. Prefer it on systemd ≥256.
3. **Scope the grant.** "Has sudo" should mean "may run *these* commands", encoded
   in a `sudoers.d` drop-in and validated with `visudo`. Blanket `ALL=(ALL) ALL`
   is a last resort, not a default.
4. **Network login is key-only.** Passwords over SSH are a brute-force target and
   a phishing target. Public keys — better, **short-lived SSH certificates** from
   a CA — plus `PermitRootLogin no` and `PasswordAuthentication no`.
5. **PAM is the policy engine.** Lockout after failures (`pam_faillock`), password
   quality (`pam_pwquality`), MFA, and session limits all live in PAM. Reach for
   it instead of ad-hoc scripts.
6. **Service accounts can't log in.** `nologin` shell, no home where possible, or
   go further with systemd `DynamicUser=` so the account exists only while the
   service runs.

## `run0` — the modern `sudo`

```bash
run0 systemctl restart nginx      # run one command as root via a transient unit
run0                              # interactive root shell (red-tinted, 🦸 prompt)
run0 --user=postgres psql         # become another user, not just root
```

`run0` needs no setuid binary and no sudoers entry — authorization is polkit. On
systems without systemd ≥256, keep using `sudo`, but configure it well:

```bash
visudo -f /etc/sudoers.d/90-deploy   # ALWAYS via visudo (syntax-checks before save)
# deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart app.service
```

Grant the narrowest command set; avoid `NOPASSWD` except for tightly-scoped,
non-shell commands; never allow a command that can spawn a shell.

## SSH hardening (the real "day one")

```sshconfig
# /etc/ssh/sshd_config.d/10-hardening.conf  (drop-in; then: systemctl reload ssh)
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
X11Forwarding no
```

Use modern keys (`ssh-keygen -t ed25519`). At scale, prefer an **SSH CA** issuing
short-lived certificates (`ssh-keygen -s ca -I id -n user host`) over distributing
`authorized_keys` — revocation and rotation become trivial. Add `fail2ban` or
`sshguard` for brute-force defense, and don't rely on a non-standard port as
security (it's noise reduction, not a control).

## Users, groups & service accounts

```bash
useradd --system --no-create-home --shell /usr/sbin/nologin appsvc  # daemon acct
usermod -aG docker alice           # add to a group (re-login to take effect)
getent passwd alice                # resolve via nsswitch (not just /etc/passwd)
id alice; groups alice             # effective UID/GIDs
chage -l alice                     # password aging/expiry policy for a human acct
```

`/etc/passwd` (account info) and `/etc/shadow` (hashed passwords) are still the
files behind the cheat-sheet — but resolution goes through NSS, so always query
with `getent`, which also covers LDAP/SSSD/`systemd-userdb`. On modern systems,
**`systemd-homed`** can manage portable, self-contained, encrypted human accounts
(records carry their own auth), and **userdb** unifies account sources — useful
for immutable and provisioned systems.

## PAM controls (lockout, quality)

PAM stacks in `/etc/pam.d/` enforce policy at auth time:

- `pam_faillock` — lock an account after N failed attempts.
- `pam_pwquality` — minimum length/complexity on password change.
- `pam_google_authenticator` / `pam_u2f` — TOTP/FIDO2 MFA.

Edit with care and keep a root session open while testing — a broken PAM stack
can lock everyone out. Filesystem-level least privilege (caps, ACLs) lives in
`linux-permissions-acl-caps-sota`; per-service sandboxing lives in
`linux-systemd-sota`.
