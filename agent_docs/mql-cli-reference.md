# mql CLI Reference
<!-- stability: evolvable | last-reviewed: 2026-07-10 | regenerate: `mql --help` -->

Complete `mql` command reference. Regenerated from `mql --help` output when
the CLI changes.

## Chroot Management

```
mql chroot                       Enter overlay chroot as interactive shell
mql chroot --exec "<cmd>"        Run a single command inside the chroot
mql chroot --reset               Discard all overlay changes since last promote
mql chroot --persist <name>      Save current overlay state as named snapshot
mql chroot --promote             Merge overlay changes into immutable base
```

## Build and Install

```
mql build <spec>                 Build RPM from spec file (x86_64)
mql build <spec> --both          Build for x86_64 and i686
mql build <spec> --arch i686     Build for i686 only
mql install <spec>               Install built RPM into chroot via DNF5
```

## Repository

```
mql repo update                  Regenerate DNF repository metadata
mql repo sync                    Sync RPMs to production repo (repo.glats.org)
```

## Release

```
mql release rootfs               Generate rootfs from installed RPMs
mql release tarball              Package rootfs as .tar.xz
mql release iso                  Generate bootable live ISO
```

## Testing

```
mql test vm                      Boot the live ISO in QEMU
mql test smoke                   Run smoke tests against the chroot
```

## Backup

```
mql backup create [tag]          Create full rootfs backup
mql backup list                  List all backups with metadata
mql backup restore <name>        Restore rootfs from backup
```

## Configuration

```
mql config                       Show active configuration
```

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `MQL_ROOTFS` | `/mnt/maquilinux` | Override rootfs disk location |
| `MQL_RELEASEVER` | Set in `mql.conf` | Release version (e.g., 26.4) |

## Related Docs

- [Build Workflow](build-workflow.md) -- how these commands fit together
- [Chroot Lifecycle](chroot-lifecycle.md) -- the overlay model behind chroot
