# Chroot Lifecycle
<!-- stability: mostly-stable | last-reviewed: 2026-07-10 -->

Maqui uses an overlayfs-based chroot. The base rootfs is immutable; all
changes happen in a writable overlay layer. This gives reproducible builds
and safe experimentation.

## Overlay Model

```
$MQL_LFS/
  base/          Immutable rootfs (lower layer)
  layers/
    upper/       Writable changes
    work/        Overlay work directory
  merged/        Active overlay mount
  repo/          Local RPM repository
```

`$MQL_LFS` defaults to `/mnt/maquilinux` (set via `MQL_ROOTFS` in `mql.conf`
or `mql.local`).

## Bind Mounts

Inside the chroot, the workspace and RPM repo are bind-mounted:

| Host path | Chroot path |
|-----------|-------------|
| Project root | `/mnt/workspace` |
| `$MQL_LFS/repo/` | `/mnt/repo` |

Virtual filesystems are automatically mounted: `proc`, `dev`, `dev/pts`,
`dev/shm`, `sys`, `run`.

## Common Operations

```bash
mql chroot                     # Enter overlay chroot shell
mql chroot --exec "<cmd>"      # Run single command in chroot
mql chroot --reset             # Discard all overlay changes
mql chroot --persist <name>    # Save overlay snapshot
mql chroot --promote           # Merge overlay into base (interactive)
```

## Promote Gotcha

`mql chroot --promote` requires interactive confirmation. It cannot be
scripted silently. Manual alternative:

```bash
sudo rsync -a $MQL_LFS/layers/upper/ $MQL_LFS/base/ &&
sudo rm -rf $MQL_LFS/layers/upper/*
```

## Stale Mount Recovery

After a crash, overlay mounts may remain. Lazy unmount in this exact order:

```bash
sudo umount -l $MQL_LFS/merged/mnt/repo
sudo umount -l $MQL_LFS/merged/dev/shm
sudo umount -l $MQL_LFS/merged/dev/pts
sudo umount -l $MQL_LFS/merged/dev
sudo umount -l $MQL_LFS/merged/run
sudo umount -l $MQL_LFS/merged/sys
sudo umount -l $MQL_LFS/merged/proc
sudo umount -l $MQL_LFS/merged
```

Then re-enter with `mql chroot` to remount cleanly.

## Related Docs

- [Build Workflow](build-workflow.md) -- what happens inside the chroot
- [Troubleshooting](troubleshooting.md) -- recovery from mount failures
