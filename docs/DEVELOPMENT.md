# Maquilinux Development Model

> **⚠️ NOTE:** The CI/CD infrastructure described in this document (Docker
> builder images, GitHub Actions workflows, GitLab CI pipelines) is **PLANNED
> but not yet implemented**. Current development uses the `mql` CLI locally.
> This document describes the target contribution and automation architecture.
> Use `mql build`, `mql install`, and `mql test` for all local work.

This document describes the development workflow, ownership model, and CI/CD
process for Maquilinux spec maintainers.

## Terminology

Different CI/CD platforms use different names for build executors:

| Platform | Term | Description |
|----------|------|-------------|
| GitHub Actions | **runner** | Self-hosted or GitHub-hosted executor |
| GitLab CI | **runner** | Registered executor for jobs |
| Jenkins | **agent** / **node** | Build executor |
| Azure DevOps | **agent** | Build and release executor |

In this document we use "runner" generically.

## Ownership Model (CODEOWNERS)

To prevent conflicts and ensure quality, each spec has an assigned maintainer.
Only the maintainer (or with their approval) can merge changes to their specs.

### Why ownership matters

Without clear ownership:
- Multiple developers may modify the same spec simultaneously
- Builds may use inconsistent dependency versions
- Breaking changes can slip through without expert review

### How it works

1. **Each spec has one owner** - responsible for that package
2. **Related specs are grouped** - the Cinnamon maintainer owns all Cinnamon-related specs
3. **PRs require owner approval** - enforced via CODEOWNERS file
4. **No direct push to main** - all changes go through PR review

### CODEOWNERS file

Create `.github/CODEOWNERS` (GitHub) or `CODEOWNERS` (GitLab):

```
# Maquilinux CODEOWNERS
# Format: <pattern> <@owner>

# Core system packages
SPECS/glibc.spec        @core-team
SPECS/gcc.spec          @core-team
SPECS/binutils.spec     @core-team
SPECS/coreutils.spec    @core-team
SPECS/linux.spec        @kernel-team

# Package management stack
SPECS/rpm.spec          @pkg-team
SPECS/dnf5.spec         @pkg-team
SPECS/libsolv.spec      @pkg-team
SPECS/librepo.spec      @pkg-team
SPECS/libdnf5.spec      @pkg-team

# Desktop environment (example: Cinnamon)
SPECS/cinnamon*.spec    @desktop-team
SPECS/muffin.spec       @desktop-team
SPECS/nemo*.spec        @desktop-team
SPECS/gtk*.spec         @desktop-team

# Build infrastructure
mql                     @core-team
lib/*.sh                @core-team
scripts/mlfs-runner.sh  @core-team

# Catch-all: new specs need core team approval
SPECS/*.spec            @core-team
```

### Branch protection rules

Configure in your Git platform:

1. **Require pull request before merging**
   - No direct push to `main` or `stable`

2. **Require CODEOWNERS review**
   - At least one approval from the file owner

3. **Require status checks to pass**
   - CI build must succeed before merge

4. **Require linear history** (optional)
   - Keeps commit history clean

## Development Workflow

### For spec maintainers

```
1. Create feature branch
   git checkout -b feature/update-glib2

2. Make changes to your spec(s)
   vim SPECS/glib2.spec

3. Test locally (optional but recommended)
   mql build glib2
   mql chroot --exec "dnf5 install /mnt/repo/glib2-*.rpm"

4. Push and create PR
   git push origin feature/update-glib2

5. CI runs automatically
   - Builds the changed spec(s)
   - Runs smoke tests
   - Reports pass/fail

6. Get approval from CODEOWNERS
   - If you own the spec, another team member reviews
   - If you don't own it, the owner must approve

7. Merge triggers:
   - RPM published to testing/
   - New system image generated
   - Available for other developers
```

### For contributors (non-owners)

```
1. Fork the repository (if external) or create branch

2. Make your changes

3. Create PR targeting main

4. Request review from the spec owner
   - They will be auto-assigned via CODEOWNERS

5. Address feedback

6. Owner merges when satisfied
```

## Avoiding Build Collisions

### The problem

```
Timeline:
  T1: Dev A pushes glib2 update → build starts with base image v1.0
  T2: Dev B pushes gtk4 update  → build starts with base image v1.0
  T3: Dev A's build completes   → new image v1.1 (has new glib2)
  T4: Dev B's build completes   → image v1.2 built on v1.0 (missing new glib2!)
```

### The solution

1. **Serial merges to main**
   - Only one PR can merge at a time
   - Each merge triggers sequential image rebuild

2. **PRs build against stable base**
   - PR builds use the last known-good image
   - Catches obvious breaks early

3. **Dependency-aware rebuilds**
   - When glib2 changes, rebuild gtk4, cinnamon, etc.
   - Handled by CI pipeline (rebuild graph)

4. **Ownership prevents conflicts**
   - Related specs have same owner
   - Owner coordinates changes across their stack

## CI/CD Pipeline Overview

```
┌─────────────────┐
│  Git Push/PR    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CI Triggered   │
│  (webhook)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Runner pulls Docker image      │
│  ghcr.io/maquilinux/builder     │
│  (contains toolchain + rpm)     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│  rpmbuild       │
│  (changed specs)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Smoke tests    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌────────────┐
│  RPM  │ │ System     │
│ Repo  │ │ Image      │
│testing│ │ (tar/qcow2)│
└───────┘ └────────────┘
```

## Distribution Formats

After successful builds, the following artifacts are generated:

| Format | Size | Use Case |
|--------|------|----------|
| `rootfs.tar.zst` | ~200-400 MB | Chroot, container base |
| `maquilinux.qcow2` | ~400-800 MB | QEMU/KVM VMs |
| Docker image | layers (~200 MB) | CI runners, dev testing |

### Docker image for runners

The builder image is published to a container registry:

```bash
# Pull the builder image
docker pull ghcr.io/maquilinux/builder:latest

# Or build locally
docker build -t maquilinux-builder -f Dockerfile.builder .
```

This image contains:
- Complete Maquilinux toolchain (gcc, binutils, etc.)
- rpm/rpmbuild
- Build dependencies
- dnf5 for package installation

## Quick Reference

### As a maintainer

```bash
# Update your spec
vim SPECS/mypackage.spec

# Test locally
mql build mypackage
mql chroot --exec "dnf5 install /mnt/repo/mypackage-*.rpm"

# Push for CI
git add SPECS/mypackage.spec
git commit -m "mypackage: update to version X.Y"
git push origin feature/mypackage-update

# Create PR, wait for CI, merge
```

### As a reviewer

1. Check that changes are within the contributor's ownership
2. Review the spec changes for correctness
3. Verify CI passed
4. Approve and merge (or request changes)

## See Also

- `README.md` - General project documentation
- `docs/GETTING-STARTED.md` - New developer onboarding
- `docs/ci-cd-workflow.puml` - Visual CI/CD diagram
- `scripts/mlfs-runner.sh` - Build orchestration script
