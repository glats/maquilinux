# Build Rust & rpm-sequoia Chain Specification

## Purpose

Specify the build execution, verification, and acceptance criteria for the full dependency chain enabling RPM GPG signing via rpm-sequoia in Maqui Linux. This spec covers the staged build pipeline from crypto libraries through rust toolchain to the final rpm-sequoia and rpm-with-sequoia rebuild.

**Proposal reference**: `sdd/maquilinux-build-rust/proposal`

## Requirements

### Requirement: Crypto Dependency Chain Build

The system MUST build the crypto library chain in dependency order: nettle → libgpg-error → libgcrypt → libassuan → gpgme. Each package MUST produce a valid RPM in RPMS/x86_64/ and install successfully into the chroot before the next package builds.

#### Scenario: Full crypto chain builds successfully

- GIVEN all source tarballs are fetched via fetch-spec-sources.sh
- WHEN build-chain.sh executes the five crypto specs in order
- THEN each spec produces an RPM and installs without unresolved BuildRequires

#### Scenario: Missing source tarball halts chain

- GIVEN a source URL is unreachable or tarball checksum fails
- WHEN fetch-spec-sources.sh runs for that spec
- THEN the build aborts with a clear error before invoking rpmbuild

### Requirement: Build Dependency Chain (libssh2, llvm)

The system MUST build libssh2 and llvm after the crypto chain completes. llvm MUST be available as a BuildRequires for subsequent rust compilation.

#### Scenario: llvm builds after crypto deps

- GIVEN nettle, libgcrypt, and gpgme RPMs are installed in chroot
- WHEN build-chain.sh builds libssh2 then llvm
- THEN llvm RPM is produced and `llvm-config --version` returns the expected version in chroot

### Requirement: Rust Toolchain Build

The system MUST build rustc, cargo, rust-std, and rust-toolchain RPMs from rust.spec. The build MUST run in a detached tmux session (--async flag) due to 4-6h compile time. A rootfs backup MUST be created before this stage.

#### Scenario: Rust builds in tmux with monitoring

- GIVEN a rootfs backup exists via `mql backup create pre-rust`
- AND disk free space exceeds 15GB
- WHEN `build-chain.sh rust --async` is executed
- THEN a tmux session is created, build runs detached, and logs are written to logs/rust.log
- AND upon completion, rust, rust-cargo, rust-std RPMs exist in RPMS/x86_64/

#### Scenario: Disk space check prevents rust build

- GIVEN disk free space is below 15GB
- WHEN `build-chain.sh rust --async` is attempted
- THEN the build is aborted with a disk space warning and no tmux session is created

#### Scenario: Rust build failure is recoverable

- GIVEN rust build fails mid-compilation in tmux
- WHEN the operator inspects logs/rust.log and fixes the spec
- THEN `build-chain.sh rust --resume` restarts from the failure point

### Requirement: rpm-sequoia Build

The system MUST build rpm-sequoia.spec after rust RPMs are installed. rpm-sequoia MUST depend on cargo from the rust RPM, not on any host-system rust.

#### Scenario: rpm-sequoia builds after rust installed

- GIVEN rust, rust-cargo, and rust-std RPMs are installed in chroot
- WHEN `mql build rpm-sequoia` is executed
- THEN rpm-sequoia RPM is produced in RPMS/x86_64/
- AND `rpm -q --requires rpm-sequoia` shows cargo as a build dependency

#### Scenario: rpm-sequoia fails without rust

- GIVEN rust RPMs are NOT installed in chroot
- WHEN `mql build rpm-sequoia` is attempted
- THEN build fails with unresolved BuildRequires: cargo

### Requirement: RPM Rebuild with Sequoia Support

The system MUST rebuild rpm.spec with `-DWITH_SEQUOIA=ON` cmake flag after rpm-sequoia-devel is installed. The resulting rpm MUST support `rpm --addsign` and `rpm --checksig`.

#### Scenario: RPM rebuilds with sequoia support

- GIVEN rpm-sequoia-devel is installed in chroot
- WHEN rpm.spec is built with `-DWITH_SEQUOIA=ON`
- THEN the resulting rpm RPM includes sequoia support
- AND `rpm --showrc | grep sequoia` confirms sequoia is enabled

#### Scenario: GPG signing test passes

- GIVEN rpm is rebuilt with sequoia support and a GPG key exists
- WHEN a test RPM is signed with `rpm --addsign`
- AND `rpm --checksig` is run on the signed RPM
- THEN verification passes with "digests signatures OK"

## Constraints

| Constraint | Value | Rationale |
|------------|-------|-----------|
| CI timeout | 360 min | Self-hosted runner limit; rust alone takes 4-6h |
| Disk space | >15GB free required | Rust compilation expands to >10GB |
| Runner RAM | >16GB | llvm and rust compilation are memory-intensive |
| Chroot isolation | All builds run inside chroot | No host-tool leakage; reproducible builds |
| Rust version | 1.75.0 (stage0 bootstrap) | Pinned by proposal; no version bump in scope |
| Architecture | x86_64 only | i686 rust deferred per proposal scope |
| Macro expansion | rpmspec -P for source URLs | Known bug: some specs fail macro expansion |

## Acceptance Criteria

| # | Criterion | Verification Command |
|---|-----------|---------------------|
| AC-01 | All 5 crypto RPMs exist | `ls RPMS/x86_64/{nettle,libgpg-error,libgcrypt,libassuan,gpgme}*.rpm` |
| AC-02 | llvm RPM exists | `ls RPMS/x86_64/llvm*.rpm` |
| AC-03 | rust RPMs exist | `ls RPMS/x86_64/{rust,rust-cargo,rust-std}*.rpm` |
| AC-04 | rust-toolchain installed in chroot | `mql chroot --exec "rustc --version && cargo --version"` |
| AC-05 | rpm-sequoia RPM exists | `ls RPMS/x86_64/rpm-sequoia*.rpm` |
| AC-06 | rpm rebuilt with sequoia | `mql chroot --exec "rpm --showrc" \| grep -i sequoia` |
| AC-07 | GPG signing works | `mql chroot --exec "rpm --addsign /mnt/repo/test.rpm && rpm --checksig /mnt/repo/test.rpm"` |
| AC-08 | Rootfs backup exists | `mql backup list \| grep pre-rust` |

## Dependencies

| Stage | Prerequisite |
|-------|-------------|
| Crypto chain | Sources fetched, chroot functional |
| libssh2 + llvm | Crypto chain RPMs installed |
| Rust toolchain | llvm installed, >15GB disk, backup created |
| rpm-sequoia | rust RPMs installed |
| rpm rebuild | rpm-sequoia-devel installed |
| GPG test | rpm rebuilt with sequoia, GPG key configured |
