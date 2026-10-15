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

## Lint

```
mql lint fhs [rpm...]            Check built RPMs against Debian filesystem rules
                                 (default: every RPM under RPMS/); exit 1 on violations
```

Rules (Debian Policy 9.1.1 over FHS 3.0): `FHS-USR-LIB64` no files under
`/usr/lib64`; `FHS-LIB64` only the dynamic linker under `/lib64`;
`FHS-TRIPLET` a package installs only into its own architecture triplet;
`FHS-LIB32` no files under `/lib32` or `/usr/lib32`. `/usr/libexec` is allowed.
Needs `rpm` on PATH (on NixOS: `nix shell nixpkgs#rpm -c ./mql lint fhs`).
Tests: `nix shell nixpkgs#bats -c bats tests/`.

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
