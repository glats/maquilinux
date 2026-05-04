# Maqui Linux Distro Health Specification

## Domain 1: repo-metadata (Phase 1)

### REQ-01: `mql repo update` MUST generate repodata via createrepo_c for each arch present in RPMS/
**Happy Path**: Given RPMS/x86_64/ and RPMS/i686/ directories contain built RPMs, when `mql repo update` is executed, then createrepo_c is run for both architectures and repodata is generated in RPMS/*/repodata/ directories.
**Edge Case**: Given RPMS/ directory exists but contains no architecture subdirectories, when `mql repo update` is executed, then no createrepo_c command is run and no repodata directories are created.

### REQ-02: `mql repo update` MUST be called automatically after `mql build` completes
**Happy Path**: Given a spec is built with `mql build <spec>`, when the build completes successfully, then `mql repo update` is automatically invoked and repodata is refreshed.
**Edge Case**: Given `mql build <spec>` fails due to compilation errors, when the build fails, then `mql repo update` is NOT called (to avoid creating repodata from broken/incomplete builds).

### REQ-03: DNF5 commands in mql CLI MUST include `--nogpgcheck` when installing from local repo (until PGP signing available)
**Happy Path**: Given a package is available in the local RPM repo, when `mql install <spec>` is executed, then the underlying dnf command includes `--nogpgcheck` flag and installation proceeds without GPG verification errors.
**Edge Case**: Given a package requires GPG signature verification and `--nogpgcheck` is not used, when `mql install <spec>` is attempted, then installation fails with GPG verification errors (until PGP signing is implemented in Phase 3).

### REQ-04: The repo config in chroot MUST point to the bind-mounted local repo at /mnt/repo
**Happy Path**: Given the chroot environment is active, when `dnf repolist` is executed, then a repository named "local" is listed with baseurl pointing to file:///mnt/repo.
**Edge Case**: Given the bind mount is missing or misconfigured, when `dnf repolist` is executed, then either no "local" repository is found or it points to an incorrect path, causing dependency resolution to fail.

## Domain 2: dep-naming (Phase 2)

### REQ-05: curl.spec MUST provide `libcurl-devel` as an alias (via %package devel or Provides:) OR rust.spec MUST use `curl-devel` instead of `libcurl-devel`
**Happy Path**: Given either curl.spec provides libcurl-devel via Provides: or rust.spec BuildRequires curl-devel instead of libcurl-devel, when `dnf install rust` is executed in chroot, then dependency resolution succeeds and rust package installs without unresolved dependencies.
**Edge Case**: Given curl.spec does not provide libcurl-devel AND rust.spec requires libcurl-devel, when `dnf install rust` is attempted, then dependency resolution fails with "No package libcurl-devel available" error.

### REQ-06: libburn.spec MUST be created with Source from upstream (libburnia project)
**Happy Path**: Given libburn.spec exists with Source pointing to official libburnia releases, when `mql build libburn` is executed, then the build succeeds using upstream source and produces libburn RPM with correct version.
**Edge Case**: Given libburn.spec uses a non-upstream source or invalid URL, when `mql build libburn` is executed, then the build fails during source download or patch application.

### REQ-07: libisoburn.spec MUST require libburn via its RPM name (not rely on LFS rootfs binary)
**Happy Path**: Given libisoburn.spec has Requires: libburn and libburn RPM is installed from local repo, when `rpm -q libisoburn` is executed, then libisoburn package is installed and `rpm -q --requires libisoburn` shows libburn dependency.
**Edge Case**: Given libisoburn.spec lacks Requires: libburn or points to a non-RPM dependency, when installed in a clean chroot without LFS rootfs libburn binary, then libisoburn may install but fails at runtime when libburn functions are called.

### REQ-08: busybox RPM provenance MUST be documented (either create busybox.spec with m264 tag, or document external build in SPECS/README or similar)
**Happy Path**: Given busybox.spec exists with Release tag containing m264, when `rpm -q busybox --qf '%{RELEASE}'` is executed, then output ends with .m264 indicating Maqui Linux build.
**Edge Case**: Given no busybox.spec exists and provenance is undocumented, when investigating busybox package origin, then no clear build instructions or spec file can be found in the repository, making reproduction difficult.

## Domain 3: rpm-sequoia-bootstrap (Phase 3)

### REQ-09: rust.spec MUST build successfully as RPM (x86_64) producing rustc, cargo, rust-std subpackages
**Happy Path**: Given rust.spec is ready and build dependencies are satisfied, when `mql build rust` is executed, then build completes successfully and produces rust, rust-cargo, rust-std, rust-debuginfo RPMs in RPMS/x86_64/.
**Edge Case**: Given rust.spec has unresolved BuildRequires or encounters compilation errors, when `mql build rust` is executed, then build fails with specific error indicating missing dependency or compilation issue.

### REQ-10: rpm-sequoia.spec MUST build successfully against the rust RPM's cargo
**Happy Path**: Given rust RPM provides cargo and rpm-sequoia.spec BuildRequires: cargo, when `mql build rpm-sequoia` is executed after rust is installed, then build succeeds and produces rpm-sequoia RPM.
**Edge Case**: Given rust is not installed or cargo is unavailable, when `mql build rpm-sequoia` is attempted, then build fails with unresolved dependency on cargo.

### REQ-11: rpm.spec MUST rebuild with rpm-sequoia-devel available, producing rpm with PGP signing support
**Happy Path**: Given rpm.spec is modified to build WITH_SEQUOIA=ON and rpm-sequoia-devel is installed, when `mql build rpm` is executed, then build succeeds and produces rpm RPM with sequoia support enabled (verified via `rpm --showrc`).
**Edge Case**: Given rpm-sequoia-devel is missing or rpm.spec lacks sequoia support, when `mql build rpm` is executed, then either build fails due to missing dependency or resulting rpm lacks PGP signing capability.

### REQ-12: After rebuild, `rpm --verify` MUST validate signed packages when a key is present
**Happy Path**: Given rpm has been rebuilt with sequoia support, a test package is signed with a trusted GPG key, when `rpm --verify <signed-package>` is executed, then verification passes with no output.
**Edge Case**: Given rpm lacks sequoia support or package signature is invalid/missing, when `rpm --verify <package>` is executed, then verification fails with appropriate error message.

## Domain 4: dep-graph-audit (Phase 4)

### REQ-13: All 122 specs MUST have their BuildRequires satisfiable by existing specs or base rootfs packages
**Happy Path**: Given the dependency graph is complete, when `rpmbuild --nobuild` is run on all specs and `dnf repoquery` checks BuildRequires, then all BuildRequires resolve to available packages.
**Edge Case**: Given a spec has BuildRequires: unsatisfiable-package, when dependency check is performed, then unresolved BuildRequires is detected and recorded as a gap.

### REQ-14: All 122 specs MUST have their Requires satisfiable by existing specs or base rootfs packages
**Happy Path**: Given the dependency graph is complete, when spec Requires are checked against available packages, then all Requires resolve to available packages from specs or base rootfs.
**Edge Case**: Given a spec has Requires: missing-package, when dependency check is performed, then unresolved Requires is detected and recorded as a gap.

### REQ-15: A `build-order.md` document MUST be produced listing specs in build-dependency order
**Happy Path**: Given all dependencies are satisfied and no circular deps exist, when dep graph audit is executed, then build-order.md is generated containing all 122 specs in topological build order.
**Edge Case**: Given circular dependencies exist in the spec set, when dep graph audit is executed, then build-order.md is NOT generated until circular deps are resolved, and gaps are documented instead.

### REQ-16: Any unsatisfied Requires/BuildRequires MUST be recorded as a known gap with severity
**Happy Path**: Given dependency gaps are identified during audit, when gaps are recorded, then each includes package name, dependent spec, severity (high/medium/low), and suggested resolution.
**Edge Case**: Given no gaps exist in the dependency graph, when audit is performed, then no gaps are recorded and build-order.md can be generated successfully.