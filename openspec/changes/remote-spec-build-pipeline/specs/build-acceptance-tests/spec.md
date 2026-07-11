# Build Acceptance Tests Specification

## Purpose

Verify that a built RPM is functional before publishing. Acceptance tests run after build and install inside the chroot. Any failure MUST block publish.

## Requirements

### Requirement: R.1 Package Installation Verification

The system MUST verify the package is registered in the RPM database via `rpm -q <pkg>`. Exit code 0 confirms installation. Exit non-zero fails the build.

#### Scenario: Package verified after build

- GIVEN a spec has been built and installed in the chroot
- WHEN `mql chroot --exec "rpm -q <pkg>"` is executed
- THEN exit code is 0

#### Scenario: Uninstalled package fails verification

- GIVEN a package not present in the RPM database
- WHEN `rpm -q <pkg>` is run
- THEN exit code is non-zero and the acceptance test fails

### Requirement: R.2 File Integrity Verification

The system MUST verify file integrity via `rpm -V <pkg>`. Empty output confirms no tampered, modified, or missing files from the RPM payload.

#### Scenario: Clean package passes integrity check

- GIVEN a correctly installed package with no file modifications
- WHEN `rpm -V <pkg>` is executed
- THEN output is empty (zero discrepancies)

#### Scenario: Modified file fails integrity check

- GIVEN a package whose installed files have been altered
- WHEN `rpm -V <pkg>` is executed
- THEN non-empty output lists the modified files and the test fails

### Requirement: R.3 Binary Execution Test

The system SHALL verify that at least one installed binary from the package executes successfully. The test MUST run `<binary> --version` or `<binary> --help` and expect exit code 0. If the package installs no binaries, the test SHALL be skipped with a warning.

#### Scenario: Binary runs successfully

- GIVEN a package that installs a binary in PATH
- WHEN `<binary> --version` is executed in the chroot
- THEN exit code is 0

#### Scenario: No-binary package skips execution test

- GIVEN a package with no executables (e.g., a library package)
- WHEN execution test is run
- THEN test is skipped and a warning is emitted

### Requirement: R.4 Library Linkage Check

The system MUST verify shared library linkage by running `ldd` on each `.so` file installed by the package. Any "not found" line indicates an unresolved dependency and SHALL fail the test.

#### Scenario: All libraries correctly linked

- GIVEN a package that installs shared libraries
- WHEN `ldd` is run on each `.so` file
- THEN no "not found" entries appear in output

#### Scenario: Missing library dependency detected

- GIVEN a package with an unresolved library dependency
- WHEN `ldd` is run on its `.so` files
- THEN "not found" entries appear and the test fails

### Requirement: R.5 Multiarch Verification

For packages built with `--both`, the system MUST verify 64-bit libraries exist in `/usr/lib/x86_64-linux-gnu/` and 32-bit libraries in `/usr/lib/i386-linux-gnu/`. For single-arch builds, the missing-arch check SHALL be skipped.

#### Scenario: Multiarch build passes verification

- GIVEN a package built with `--both`
- WHEN multiarch verification runs
- THEN 64-bit `.so` files exist in `/usr/lib/x86_64-linux-gnu/`
- AND 32-bit `.so` files exist in `/usr/lib/i386-linux-gnu/`

#### Scenario: Single-arch build skips other arch

- GIVEN a package built for x86_64 only
- WHEN multiarch verification runs
- THEN the 32-bit check is skipped without error

## Global Scenarios

### Scenario: Acceptance test failure blocks publish

- GIVEN a build with acceptance tests enabled
- WHEN any acceptance test (R.1 through R.5) fails
- THEN the publish step is blocked
- AND the failure report identifies which test(s) failed and why
