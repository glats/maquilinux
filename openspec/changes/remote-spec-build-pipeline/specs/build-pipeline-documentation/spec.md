# Build Pipeline Documentation Specification

## Purpose

Document the developer environment setup, push-vs-read artifact boundary, acceptance test verification flow, and backup lifecycle for AI agents working on the Maqui Linux build pipeline.

## Requirements

### Requirement: R.9 Developer Setup Documentation

The agent documentation MUST describe two environment setup paths for developers: Path A (Nix shell via `nix develop`, providing rpm, rpmbuild, createrepo_c, dnf5) and Path B (standalone via host package manager: apt, dnf, pacman). MUST include rootfs download from `maquiroot.glats.org` and MQL_ROOTFS configuration steps.

#### Scenario: New developer follows setup guide

- GIVEN a developer cloning maquilinux for the first time
- WHEN they read the developer setup documentation
- THEN they see Nix shell and standalone paths with exact commands
- AND they know how to download and extract the rootfs tarball
- AND they know how to set MQL_ROOTFS via `mql.local`

### Requirement: R.10 Push-vs-Read Boundary Documentation

The agent documentation MUST explicitly document the artifact boundary at `rog.local` nginx. Internal push: SSH + rsync from `thinkcentre.local` to `rog.local`. Public read: HTTPS via `repo.glats.org` (RPMs) and `maquiroot.glats.org` (rootfs tarballs).

#### Scenario: Agent reads boundary documentation

- GIVEN an agent needs to understand the artifact flow
- WHEN the agent reads the push-vs-read documentation
- THEN it identifies SSH/rsync as internal-only
- AND it identifies HTTPS endpoints as the public surface
- AND it does not attempt SSH to rog.local from outside thinkcentre

### Requirement: R.11 Acceptance Test Flow Documentation

The agent documentation MUST document the acceptance test verification flow: build completes, install RPM, verify install (rpm -q), verify integrity (rpm -V), verify execution (binary --version/--help), verify linkage (ldd). MUST state that any failure blocks the publish step.

#### Scenario: Agent reads acceptance test documentation

- GIVEN an agent monitoring a CI build
- WHEN the agent reads the acceptance test documentation
- THEN it knows the ordered verification steps
- AND it knows failure blocks publishing
- AND it can interpret test failure reports

### Requirement: R.12 Backup Flow Documentation

The agent documentation MUST document the backup lifecycle: pre-build backup via `mql backup create pre-build-<tag>`, post-build success backup via `mql backup create post-build-<tag>`, post-build failure restore via `mql backup restore pre-build-<tag>`. MUST reference `lib/backup.sh` and the museum-style storage model.

#### Scenario: Agent reads backup flow documentation

- GIVEN an agent needs to understand the backup system
- WHEN the agent reads the backup flow documentation
- THEN it knows pre-build and post-build backups are automatic in CI
- AND it knows the restore command for failure recovery
- AND it understands backup naming conventions
