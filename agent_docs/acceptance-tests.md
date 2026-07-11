# Acceptance Tests
<!-- stability: stable | last-reviewed: 2026-07-10 -->

Post-build verification checks that run after a package is built and installed
inside the chroot. Any failure blocks the publish step.

## Test 1: Package Installation (rpm -q)

Verify the package is registered in the RPM database.

```bash
mql chroot --exec "rpm -q <package>"
```

- **Success**: Exit code 0, package version printed.
- **Failure**: Exit code non-zero, "package is not installed" error.

## Test 2: File Integrity (rpm -V)

Verify all installed files match the RPM payload (no tampering, no missing
files, no modification).

```bash
mql chroot --exec "rpm -V <package>"
```

- **Success**: Empty output (zero discrepancies).
- **Failure**: Non-empty output listing modified/missing files.

## Test 3: Binary Execution (--version)

Verify at least one installed binary from the package executes. Uses `--version`
or `--help` flag. Skipped if the package installs no binaries.

```bash
mql chroot --exec "<binary> --version"
```

- **Success**: Exit code 0.
- **Failure**: Exit code non-zero (binary not found or crashed).
- **Skip**: Warning emitted if no binaries are installed.

## Test 4: Library Linkage (ldd)

Verify all shared libraries have resolved dependencies. Runs `ldd` on each `.so`
file installed by the package. Skipped if no shared libraries are installed.

```bash
mql chroot --exec "ldd /usr/lib/<path>/*.so"
```

- **Success**: No "not found" entries in ldd output.
- **Failure**: One or more "not found" entries (unresolved dependency).

## Test 5: Multiarch Check

For `--both` builds, verify libraries exist in both architecture paths. For
single-arch builds, the missing-arch check is skipped.

```bash
# Verify 64-bit libraries
ls /usr/lib/x86_64-linux-gnu/<lib>*.so
# Verify 32-bit libraries (if built with --both)
ls /usr/lib/i386-linux-gnu/<lib>*.so
```

- **Success**: Libraries present in the expected architecture directories.
- **Failure**: Missing libraries for the expected architecture.
- **Skip**: Single-arch builds skip the other arch check.

## CI Integration

In the CI pipeline, these tests run after step 5 (Install the RPM) and before
step 6 (Regenerate repo metadata). The `acceptance-test.sh` script (Phase 2)
collects all results into a structured JSON report:

```json
{
  "spec": "bash",
  "status": "pass",
  "checks": [
    {"name": "rpm_installed", "status": "pass"},
    {"name": "rpm_verify", "status": "pass"},
    {"name": "binary_exec", "status": "pass"},
    {"name": "library_linkage", "status": "skip", "detail": "no shared libs"},
    {"name": "multiarch", "status": "pass"}
  ]
}
```

## Related Docs

- [Build Workflow](build-workflow.md) -- pipeline step that includes acceptance tests
- [Troubleshooting](troubleshooting.md) -- common test failures and recovery
