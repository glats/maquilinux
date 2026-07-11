# Dependency Resolution
<!-- stability: mostly-stable | last-reviewed: 2026-07-10 -->

Building a package requires its BuildRequires to be installed first. This
document covers how to determine the build order and resolve dependencies.

## BuildRequires Chain

Every spec declares what it needs to build:

```spec
BuildRequires: gcc
BuildRequires: zlib-devel
BuildRequires: pkgconfig(openssl)
```

When building a new package, all BuildRequires must already be installed in
the chroot or available as RPMs in the local repo.

## Determining Build Order

1. Identify the target spec's `BuildRequires:` lines.
2. For each BuildRequires, check if it's installed:
   ```bash
   mql chroot --exec "rpm -q <package>"
   ```
3. If not installed, check if an RPM exists:
   ```bash
   ls RPMS/<package>-*.rpm
   ```
4. If no RPM exists, recursively resolve that package's dependencies.

## Installing Dependencies

```bash
mql chroot --exec "dnf install /mnt/repo/<package>-*.rpm"
```

DNF5 resolves transitive dependencies automatically from the local repo at
`/mnt/repo`. The repo metadata must be current:

```bash
mql repo update
```

## Multiarch Considerations

When using `--both` to build x86_64 and i686:

- x86_64 packages are built first and installed
- i686 packages may need 32-bit library dependencies already installed
- Check that 32-bit `-devel` packages exist if the spec requires them

## Circular Dependencies

Some packages form dependency cycles (e.g., rpm needs zstd, zstd needs gcc,
gcc needs m4). The existing toolchain handles these. For new packages with
potential cycles, bootstrap with a minimal first build, install it, then
rebuild with full features.

## Related Docs

- [Build Workflow](build-workflow.md) -- the full pipeline
- [Spec Conventions](spec-conventions.md) -- how to declare BuildRequires
- [Multiarch Guide](multiarch-guide.md) -- 32-bit dependency patterns
