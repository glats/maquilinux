# Troubleshooting
<!-- stability: evolvable | last-reviewed: 2026-07-10 -->

Common failure modes when building packages for Maqui Linux, with diagnostic
and recovery commands. Append new failures as they are discovered.

## Overlay Not Mounted

**Diagnosis:** `mql chroot --exec "echo ok"` fails with "not mounted".

**Fix:**
```bash
mql chroot              # This mounts the overlay before entering
# Or manually: mount -t overlay overlay -o lowerdir=$MQL_LFS/base,upperdir=$MQL_LFS/layers/upper,workdir=$MQL_LFS/layers/work $MQL_LFS/merged
```

## Sources Not Found

**Diagnosis:** rpmbuild fails with "error: File ... not found".

**Fix:**
```bash
scripts/fetch-spec-sources.sh SPECS/<package>.spec
# Or download the tarball manually to SOURCES/
```

## BuildRequires Unresolved

**Diagnosis:** dnf install fails with "nothing provides ...".

**Fix:** Check dependency order. The dependency must be built and installed
first, and `mql repo update` must have been run. See `dependency-resolution.md`.

## Stale Mounts After Crash

**Diagnosis:** `mount | grep merged` shows leftover mounts.

**Fix:** Lazy unmount in exact order (see `chroot-lifecycle.md`).

## Promote Confirmation

**Diagnosis:** `mql chroot --promote` hangs or fails in CI.

**Fix:** Use the manual rsync alternative:
```bash
sudo rsync -a $MQL_LFS/layers/upper/ $MQL_LFS/base/ && sudo rm -rf $MQL_LFS/layers/upper/*
```

## GPG Signature Errors

**Diagnosis:** dnf install fails with "GPG check FAILED".

**Fix:** For local development builds (unsigned), add `--nogpgcheck`:
```bash
mql chroot --exec "dnf install --nogpgcheck /mnt/repo/<package>-*.rpm"
```

## Workspace Not Bind-Mounted

**Diagnosis:** `ls /mnt/workspace` inside chroot is empty.

**Fix:** Exit chroot and re-enter. `mql chroot` handles bind mounts
automatically. If persistent, check that `$MQL_LFS/merged/mnt/workspace`
exists.

## 32-bit Build Missing

**Diagnosis:** `mql build <spec> --both` only builds x86_64.

**Fix:** The spec may lack i686 conditionals. Check for
`%if "%{_target_cpu}" == "i686"` in the spec file. Alternatively, build
i686 explicitly:
```bash
mql build <spec> --arch i686
```

## Related Docs

- [Chroot Lifecycle](chroot-lifecycle.md) -- mount recovery details
- [Dependency Resolution](dependency-resolution.md) -- build order resolution
- [Build Workflow](build-workflow.md) -- the full pipeline
