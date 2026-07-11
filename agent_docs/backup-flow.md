# Backup Flow
<!-- stability: mostly-stable | last-reviewed: 2026-07-10 -->

## Philosophy

Museum-style storage: never delete, never overwrite. Backups accumulate in hot
storage (recent) and cold storage (archive). Old backups are never removed.

## Lifecycle

```
pre-build backup -> build packages -> post-build (success) backup
                               |
                               +-> restore pre-build if failure
```

### Pre-build

Create a snapshot of the current rootfs before any changes:

```bash
mql backup create pre-build-<tag>
```

Runs automatically in CI before the build loop. The tag identifies the build
session (e.g., date or PR number).

### Post-build (success)

Snapshot the rootfs after a successful build, capturing the new state:

```bash
mql backup create post-build-<tag>
```

### Post-build (failure restore)

If the build fails, restore the pre-build state to leave the chroot clean:

```bash
mql backup restore pre-build-<tag>
```

In CI, this runs via `if: failure()` GitHub Actions conditional.

## Commands

```bash
mql backup create <tag>       # Create backup of current base rootfs
mql backup list               # List all backups
mql backup restore <name>     # Restore from backup
mql backup museum             # View hot + cold storage
```

## Storage

| Location | Path | Purpose |
|----------|------|---------|
| Hot | `$HOME/maqui-backups/` | Recent backups |
| Cold | `$HOME/maqui-archive/` | Archived (old) backups |

## Rootfs Publishing

After CI validates a build, rootfs tarballs are promoted to:

| URL | Description |
|-----|-------------|
| `https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz` | Latest rootfs |
| `https://maquiroot.glats.org/history/<name>.tar.xz` | Historical versions |

## Push vs Read Boundary

| Direction | Mechanism | From | To | Who |
|-----------|-----------|------|----|-----|
| Push (internal) | SSH + rsync | thinkcentre.local | rog.local | CI runner |
| Push (internal) | SSH + rsync | thinkcentre.local | rog.local (maquiroot) | CI runner |
| Push (internal) | bind-mount | Host workspace | Chroot /mnt/repo | CI runner |
| Read (public) | HTTPS (nginx) | rog.local | Internet | Developers, DNF5 clients |

The boundary is `rog.local`'s nginx. Everything behind it is internal push.
Everything in front is public HTTPS read. Agents must never propose pushing
directly to a public URL.

## Related Docs

- [Build Workflow](build-workflow.md) -- pipeline that calls backup steps
- [Chroot Lifecycle](chroot-lifecycle.md) -- overlay state management
- [Troubleshooting](troubleshooting.md) -- backup recovery and failure modes
