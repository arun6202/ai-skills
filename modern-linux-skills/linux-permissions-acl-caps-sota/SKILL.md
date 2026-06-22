---
name: linux-permissions-acl-caps-sota
description: >-
  Modern Linux access control beyond `chmod`/`chown` — use whenever the task
  involves file permissions, ownership, "permission denied", sharing a directory
  between users/services, or the reflex to `chmod 777`. Steers from the
  three-digit `rwx` octal model toward what production actually uses: POSIX ACLs
  (`setfacl`/`getfacl`) for multi-principal access, **file capabilities**
  (`setcap`/`getcap`) to replace the setuid bit, `umask` and default ACLs for
  correct-by-default creation, the special bits (setuid/setgid/sticky) explained,
  immutable attributes (`chattr +i`), and where MAC (SELinux/AppArmor) labels sit
  on top. Reach for it on any `chmod 777`, "group can't write the shared folder",
  "binary needs root just to bind port 80", or "lock this file" task.
---

# Linux permissions, ACLs & capabilities (SOTA)

The cheat-sheet's `rwx`/`755`/`chmod 777` model is correct but **coarse**: it
expresses only *owner / one group / everyone*. Real systems need "these three
users and that service can write, nobody else", and "this binary may bind a low
port but is otherwise unprivileged". Those are ACLs and capabilities — and they
are the reason `chmod 777` is almost always the wrong answer.

> **Prime directive: grant the narrowest right that works, to the smallest
> principal, by construction.** `777` and blanket setuid are blast-radius bugs
> waiting to happen. ACLs name principals; capabilities name powers.

## Break the muscle memory (reflex → SOTA)

| Reflex (cheat-sheet habit)                      | SOTA                                                                 |
|-------------------------------------------------|---------------------------------------------------------------------|
| `chmod 777 dir` so "everyone can use it"        | `setfacl -m u:svc:rwX,g:team:rwX dir` — name who, drop world access |
| `chmod 666 file` to let two users write         | `setfacl -m u:alice:rw,u:bob:rw file`                              |
| Shared upload dir, files keep wrong group       | `setgid` on dir + **default ACL**: `setfacl -d -m g:team:rwX dir`  |
| setuid-root the binary so it can bind :80       | `setcap 'cap_net_bind_service=+ep' ./binary` (or a systemd socket) |
| setuid-root for raw sockets / ping              | `cap_net_raw`; for `nice`/RT → `cap_sys_nice`; never blanket root  |
| `chmod -R 755` to "fix" a tree                  | `chmod -R u=rwX,go=rX` (capital `X` = dir-only execute)            |
| Files world-readable by default                 | set `umask 027` (or `077`) so creation is private by default       |
| "Make this file un-deletable" via permissions   | `chattr +i file` (immutable attr; even root must clear it first)   |
| `chown` then forget SELinux denies it           | also fix the label: `restorecon -v` / `chcon` (see MAC below)      |
| Read perms off `ls -l` and eyeball              | `getfacl file`, `getcap binary`, `stat -c '%A %U %G' file`         |

## The creed

1. **Default-deny on creation.** Permissions you never grant can't leak. Set a
   tight `umask` (027/077) and **default ACLs** on shared dirs so new files are
   born correct instead of fixed afterward.
2. **Name principals with ACLs, not mode bits.** The mode has room for one user +
   one group + world. The moment you need a *second* group or a service account,
   reach for `setfacl`, not a looser octal.
3. **Name powers with capabilities, not setuid.** A setuid-root binary holds
   *all* of root for the duration. A file capability grants exactly the one power
   needed (`cap_net_bind_service`, `cap_net_raw`, `cap_sys_time`, …) and nothing
   else. Prefer a systemd socket/`AmbientCapabilities=` over even file caps.
4. **The special bits are tools, know them cold.** setuid (run as owner), setgid
   on a dir (inherit group — the key to shared dirs), sticky on a world-writable
   dir like `/tmp` (only owner deletes their files).
5. **Immutability and MAC are layers above the mode.** `chattr +i` blocks change
   regardless of `rwx`; SELinux/AppArmor can deny what the mode allows. A 0644
   file can still be unwritable, and a 0777 file can still be denied — check all
   the layers when "permission denied" surprises you.

## ACL essentials

```bash
getfacl path                       # read full ACL (also shows the mode as ACL)
setfacl -m u:alice:rwX path        # grant alice; X = execute only if dir/already-x
setfacl -m g:deploy:rX path        # grant a group read+traverse
setfacl -R -m u:svc:rX dir/        # recursive grant on an existing tree
setfacl -d -m g:team:rwX dir/      # DEFAULT acl: applies to things created later
setfacl -x u:alice path            # remove one entry
setfacl -b path                    # strip all ACLs back to the plain mode
```

A `+` after the mode in `ls -l` (`-rw-rwx---+`) means an ACL is present — always
`getfacl` it rather than trusting the displayed mode, which shows the *mask*.

## Capabilities essentials

```bash
getcap -r /usr/bin 2>/dev/null            # audit which binaries hold caps
setcap 'cap_net_bind_service=+ep' ./app   # may bind <1024 without being root
setcap -r ./app                           # remove file caps
capsh --print                             # caps of the current shell/process
grep Cap /proc/$$/status                  # raw cap bitmasks for a process
```

Common swaps for setuid-root: bind low ports → `cap_net_bind_service`; raw/ICMP
sockets → `cap_net_raw`; set system time → `cap_sys_time`; high priority →
`cap_sys_nice`. In a service, prefer dropping everything and granting back the
minimum: `CapabilityBoundingSet=` + `AmbientCapabilities=` in the unit (see
`linux-systemd-sota`).

## Special bits, umask, immutability

```bash
chmod u+s bin            # setuid; chmod 4755. Audit these — they are attack surface
chmod g+s shared/        # setgid on dir: new files inherit the dir's group
chmod +t /shared/tmp     # sticky: only the owner may delete their own files
umask 027                # new files 640 / dirs 750; put in /etc/profile.d for global
chattr +i /etc/resolv.conf   # immutable; lsattr to view; +a = append-only (logs)
```

## Where MAC fits (SELinux / AppArmor)

The mode and ACLs are **DAC** (discretionary). On RHEL/Fedora (SELinux) and
Ubuntu/SUSE (AppArmor) a **MAC** layer can still deny access the DAC allows —
this is the classic "0644 file, correct owner, still denied" footgun, usually a
wrong label after a move/copy.

```bash
ls -Z file                 # show SELinux context (user:role:type:level)
restorecon -Rv /srv/www    # reset labels to policy default (fixes most denials)
chcon -t httpd_sys_content_t file   # set a type label explicitly
ausearch -m AVC -ts recent # find what SELinux denied and why
aa-status                  # AppArmor: which profiles are enforcing
```

Rule of thumb: if DAC looks correct but access is denied, suspect the label
before loosening the mode. Never disable SELinux/AppArmor to "fix" one file —
relabel instead. Hardening of *who can become root* lives in
`linux-users-auth-hardening-sota`; sandboxing a service's filesystem view lives
in `linux-systemd-sota`.
