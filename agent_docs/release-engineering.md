# Release Engineering

Stability: mostly-stable (changes with CI pipeline evolution)

## Pipeline Overview

The Maqui Linux release pipeline has three stages: build, ISO generation, and publish.

### Stage 1: Build (`build-rpms-v2.yml`)

Triggered by `push` to `main` (on `SPECS/*.spec` changes), `workflow_dispatch`, or
`pull_request`. The `build` job runs `build-chain.sh` with `--continue-on-failure`,
producing structured per-spec status. Each spec is built, installed, and verified
via acceptance tests. On success, RPMs are signed and synced to `repo.glats.org`.

### Stage 2: ISO (`iso.yml`)

Triggered by `workflow_call` from build-rpms-v2.yml (after clean build), `push: tags v*`,
or `workflow_dispatch`. The `build-iso` job:

1. Sets up chroot overlay (bind mounts workspace + RPM repo)
2. Verifies ISO deps: xorriso, mksquashfs, dracut
3. Runs `mql release rootfs` -- installs all RPMs into chroot via dnf
4. Runs `mql release iso` -- kernel + dracut initramfs + squashfs + grub-mkrescue
5. Generates SHA-256 and SHA-512 checksums
6. Uploads ISO as GitHub Actions artifact (90-day retention)
7. On tag push: attaches ISO and checksums to GitHub Release

If `publish: true`, calls `publish-iso.yml` which:

1. Downloads the `iso` artifact
2. Validates size (>500 MB), structure, and checksum
3. Rsyncs to `rog.local:/srv/glats/nginx/maquiroot/iso/latest/`
4. Archives to `iso/history/` with version name
5. Updates `index.json`
6. Verifies published file size

### Stage 3: Rootfs (`publish-rootfs.yml`)

Standalone workflow for promoting a backup rootfs to `maquiroot.glats.org/latest/`.
Validates backup integrity and critical files before syncing. See `agent_docs/backup-flow.md`.

## Publish URLs

| URL | Purpose | Source workflow |
|-----|---------|-----------------|
| `https://repo.glats.org` | Production RPM repository (DNF5) | `build-rpms-v2.yml` |
| `https://maquiroot.glats.org/latest/` | Latest rootfs tarball | `publish-rootfs.yml` |
| `https://maquiroot.glats.org/history/` | Rootfs archive | `publish-rootfs.yml` |
| `https://maquiroot.glats.org/iso/latest/` | Latest live ISO | `publish-iso.yml` |
| `https://maquiroot.glats.org/iso/history/` | ISO version archive | `publish-iso.yml` |

## Push vs Read Boundary

- **Push (internal)**: SSH + rsync to `rog.local` (thinkcentre.local only)
- **Read (public)**: HTTPS via `repo.glats.org` (RPMs), `maquiroot.glats.org` (rootfs, ISO)

## Trigger Summary

| Event | ISO build | Publish | GitHub Release |
|-------|-----------|---------|----------------|
| Push to main (spec change) | Yes | Yes | No |
| Tag push `v*` | Yes | Yes (if configured) | Yes |
| `workflow_dispatch` | Yes | Optional | No |
| Pull request | No | No | No |

## ISO Generation

The canonical builder is `lib/iso.sh` (`mql release iso`). It runs inside the chroot
overlay to produce a live-bootable ISO. The ISO filename omits the architecture suffix
(`-x86_64`) for Phase 1; multiarch ISOs would use `maquilinux-latest-x86_64.iso`.

## Related Docs

- `agent_docs/build-workflow.md` -- Spec to RPM pipeline
- `agent_docs/backup-flow.md` -- Rootfs backup lifecycle
- `.github/workflows/iso.yml` -- ISO workflow definition
- `.github/workflows/publish-iso.yml` -- ISO publish workflow
- `.github/workflows/build-rpms-v2.yml` -- Build pipeline
- `.github/workflows/publish-rootfs.yml` -- Rootfs publish
- `lib/iso.sh` -- Canonical ISO builder
