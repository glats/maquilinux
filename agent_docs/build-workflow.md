# Build Workflow
<!-- stability: mostly-stable | last-reviewed: 2026-07-10 -->

The pipeline from spec file to installed RPM in the chroot. All builds happen
inside the overlay chroot, never on the host.

## Pipeline Steps

### 1. Write or update the spec

Create or edit a `.spec` file in `SPECS/`. Follow conventions in
`spec-conventions.md`.

### 2. Fetch sources

```bash
scripts/fetch-spec-sources.sh <package>
```

Downloads tarballs to `SOURCES/`. Alternatively, place sources manually.

### 3. Enter the overlay chroot

```bash
mql chroot
```

Mounts overlay and drops into shell. Workspace: `/mnt/workspace`, repo: `/mnt/repo`.

### 4. Pre-build backup

```bash
mql backup create pre-build-<package>
```

Creates a rootfs snapshot before building. Restore with
`mql backup restore pre-build-<package>` if the build fails.
See [backup-flow.md](backup-flow.md).

### 5. Build the RPM

```bash
mql build <package>
```

For multiarch:

```bash
mql build <package> --both
```

Output lands in `RPMS/`. See [spec-conventions.md](spec-conventions.md).

### 6. Install the RPM

```bash
mql install <package>
```

Runs `dnf install` inside the chroot from `/mnt/repo`.

### 7. Verify the installation

Run acceptance tests to confirm the package is functional:

```bash
mql chroot --exec "rpm -q <package>"       # Package registered in RPM DB
mql chroot --exec "rpm -V <package>"       # Files intact, no tampering
mql chroot --exec "<binary> --version"     # Binary executes (exit 0)
mql chroot --exec "ldd /usr/lib/<lib>.so"  # Shared libs linked (if any)
```

See [acceptance-tests.md](acceptance-tests.md) for full test specification.

### 8. Regenerate repo metadata

```bash
mql repo update
```

Rebuilds repo index so new packages are available as dependencies.

### 9. Post-build backup

```bash
mql backup create post-build-<package>
```

Snapshot after a successful build. On failure, restore pre-build instead:
```bash
mql backup restore pre-build-<package>
```
See [backup-flow.md](backup-flow.md).

## Related Docs

- [Acceptance Tests](acceptance-tests.md) -- verification checks in detail
- [Backup Flow](backup-flow.md) -- backup lifecycle and restore
- [Spec Conventions](spec-conventions.md) -- how to write specs
- [Dependency Resolution](dependency-resolution.md) -- build order and deps
- [Chroot Lifecycle](chroot-lifecycle.md) -- overlay and mount management
- [Troubleshooting](troubleshooting.md) -- what to do when builds fail
