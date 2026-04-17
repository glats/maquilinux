# Maquilinux CI/CD Pipeline Guide

> **⚠️ PLANNED — Not yet implemented.** Current builds use `mql` CLI locally.
> This document describes the target CI architecture. None of the GitHub
> Actions workflows, GitLab CI pipelines, or Docker builder images referenced
> here exist yet. For actual build instructions, see `docs/GETTING-STARTED.md`.

This guide explains how to use and customize the CI/CD pipelines for Maquilinux.

## Overview

All builds are executed through YAML-based pipeline definitions, not local scripts.
The builder container image provides a consistent, reproducible environment.

| Platform | Configuration Files |
|----------|---------------------|
| GitHub Actions | `.github/workflows/*.yml` |
| GitLab CI | `.gitlab-ci.yml` |

## Workflows

### 1. PR Validation (`pr-validate.yml`)

**Trigger:** `on: pull_request` (when SPECS/ or SOURCES/ change)

**Jobs:**
- `lint` - Validate spec syntax with `rpmspec -P`
- `codeowners` - Check if correct owner is assigned
- `build-test` - Build changed specs in container

**Purpose:** Catch errors before merge, ensure CODEOWNERS approval.

```yaml
# Key sections
on:
  pull_request:
    paths:
      - 'SPECS/**'
      - 'SOURCES/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: rpmspec -P "$spec"
```

### 2. Build & Publish (`build-publish.yml`)

**Trigger:** `on: push` to main branch

**Jobs:**
1. `detect-changes` - Find which specs changed
2. `build` - Matrix build of changed packages
3. `publish-testing` - Upload RPMs to testing/ repo
4. `generate-images` - Create tar.zst, qcow2
5. `update-builder` - Rebuild and push builder:latest

**Purpose:** Automated build and publish on every merge.

```yaml
# Matrix strategy for parallel builds
jobs:
  build:
    strategy:
      matrix:
        package: ${{ fromJson(needs.detect-changes.outputs.matrix) }}
```

### 3. Promote to Stable (`promote-stable.yml`)

**Trigger:** `workflow_dispatch` (manual)

**Required Input:** `confirm: "promote"`

**Jobs:**
- `confirm` - Validate user typed "promote"
- `promote` - Copy RPMs from testing/ to stable/

**Purpose:** Controlled promotion after QA approval.

```yaml
# Manual trigger with confirmation
on:
  workflow_dispatch:
    inputs:
      confirm:
        description: 'Type "promote" to confirm'
        required: true
```

## Builder Container Image

The builder image contains all tools needed to build packages:

```dockerfile
# Dockerfile.builder (example)
FROM fedora:latest

RUN dnf install -y \
    rpm-build \
    gcc gcc-c++ \
    make cmake meson ninja-build \
    git \
    && dnf clean all

# Or from Maquilinux rootfs
FROM scratch
ADD rootfs.tar.zst /
```

**Registry:** `ghcr.io/<owner>/maquilinux-builder:latest`

### Local Development with Builder

```bash
# Pull the builder image
podman pull ghcr.io/maquilinux/builder:latest

# Build a package locally
podman run --rm -v $PWD:/src -w /src \
    ghcr.io/maquilinux/builder:latest \
    rpmbuild -ba SPECS/mypackage.spec \
        --define "_topdir /src" \
        --define "_sourcedir /src/SOURCES"

# Interactive shell
podman run -it --rm -v $PWD:/src -w /src \
    ghcr.io/maquilinux/builder:latest \
    /bin/bash
```

## GitLab CI Alternative

If using GitLab instead of GitHub:

```yaml
# .gitlab-ci.yml stages
stages:
  - validate    # lint:specs
  - build       # build:packages
  - test        # test:smoke
  - publish     # publish:testing
  - images      # images:rootfs, images:builder
  - promote     # promote:stable (manual)
```

Key differences:
- Uses `rules:` instead of `on:`
- Uses `needs:` for job dependencies
- Uses `artifacts:` for passing files between jobs
- Manual jobs use `when: manual`

## Secrets Required

Configure these secrets in your repository settings:

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` | Auto-provided, for GHCR access |
| `REPO_SSH_KEY` | SSH key for repo.glats.org |

### Setting up REPO_SSH_KEY

```bash
# Generate deploy key
ssh-keygen -t ed25519 -f deploy_key -N ""

# Add public key to repo server
cat deploy_key.pub >> ~/.ssh/authorized_keys  # on repo server

# Add private key as secret
cat deploy_key  # paste into GitHub/GitLab secret
```

## Customizing Workflows

### Adding a new package smoke test

Edit the `build-publish.yml` smoke test step:

```yaml
- name: Run smoke tests
  run: |
    case "${{ matrix.package }}" in
      mypackage)
        mypackage --version
        ;;
      # ... other cases
    esac
```

### Building specific packages manually

Use `workflow_dispatch` with inputs:

```yaml
on:
  workflow_dispatch:
    inputs:
      packages:
        description: 'Packages to build (space-separated)'
        required: false
```

Then trigger from GitHub UI or CLI:

```bash
gh workflow run build-publish.yml -f packages="gcc glibc"
```

### Skipping CI for commits

Add `[skip ci]` to commit message:

```bash
git commit -m "docs: update README [skip ci]"
```

## Troubleshooting

### Build fails with missing dependency

1. Check if dependency is in builder image
2. Add to `Dockerfile.builder` BuildRequires
3. Rebuild and push builder image

### RPMs not appearing in repo

1. Check `publish-testing` job logs
2. Verify SSH key is correct
3. Check repo server disk space
4. Run `createrepo_c` manually if needed

### Container image not updating

1. Check `update-builder` job succeeded
2. Verify GHCR permissions
3. Pull latest: `podman pull --no-cache ghcr.io/.../builder:latest`

## File Structure

```
maquilinux/
├── .github/
│   └── workflows/
│       ├── pr-validate.yml      # PR checks
│       ├── build-publish.yml    # Main build pipeline
│       └── promote-stable.yml   # Manual promotion
├── .gitlab-ci.yml               # GitLab alternative
├── Dockerfile.builder           # Builder image definition
├── SPECS/
│   └── *.spec
├── SOURCES/
│   └── *.patch, *.tar.gz
└── docs/
    ├── PIPELINES.md             # This file
    ├── DEVELOPMENT.md           # Ownership model
    └── *.puml                   # Diagrams
```

## See Also

- `docs/DEVELOPMENT.md` - CODEOWNERS and workflow
- `docs/ci-cd-workflow.puml` - Visual diagram
- `docs/02-build-pipeline.puml` - Detailed build sequence
