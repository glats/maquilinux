# Contributing to Maqui Linux

## Prerequisites

- NixOS or any Linux distribution with `sudo` access
- ~15GB free disk space
- SSH key configured with GitHub
- GitHub CLI (`gh`) installed
- `git`, `curl`, `bash` (basic tools)

## Quick Start

### 1. Clone the project

```bash
git clone https://github.com/glats/maquilinux.git
cd maquilinux
```

### 2. Initialize the build environment

If you have a rootfs tarball:
```bash
mql init --from-file /path/to/maquilinux-rootfs.tar.gz
```

Or download one from maquiroot.glats.org:
```bash
curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.gz
mql init --from-file maquilinux-rootfs-latest.tar.gz
```

### 3. Enter the build chroot

```bash
mql chroot
```

### 4. Build a package

```bash
mql build <spec-name>
```

Examples:
```bash
mql build tree
mql build which
mql build nano
```

### 5. Install and test

```bash
mql chroot --exec "dnf install -y tree"
mql chroot --exec "tree --version"
```

### 6. Sign the package (manual)

```bash
nix shell nixpkgs#rpm -c rpmsign --addsign RPMS/x86_64/<package>-*.rpm
```

### 7. Push and trigger CI

```bash
git add SPECS/<spec>.spec
git commit -m "feat: update <package> to new version"
git push origin main
```

### 8. Monitor the pipeline

```bash
gh run list --limit 5
gh run watch $(gh run list --limit 1 --json databaseId -q '.[0].databaseId')
```

## Directory Structure

```
maquilinux/
├── SPECS/          # RPM spec files (131+ specs)
├── SOURCES/        # Source tarballs
├── RPMS/           # Built RPM packages
│   ├── x86_64/     # 64-bit packages
│   └── i686/       # 32-bit packages
├── lib/            # mql CLI library
├── scripts/        # Build and utility scripts
├── docs/           # Documentation
├── mql.conf        # Default configuration (committed)
├── mql.local       # User overrides (gitignored)
└── flake.nix       # Nix development shell
```

## Key Files

- `mql.conf` — Default configuration (MQL_ROOTFS, MQL_RELEASEVER, etc.)
- `mql.local` — User overrides (gitignored, created by `mql init`)
- `flake.nix` — Nix development shell (provides all build tools)

## Spec Conventions

- Release tag: `1.m264` (m264 = maquilinux 26.4)
- Debug packages disabled: `%global debug_package %{nil}`
- Multiarch: `%if "%{_target_cpu}" == "i686"` conditionals
- Library dirs: `/usr/lib/x86_64-linux-gnu/` (64-bit), `/usr/lib/i386-linux-gnu/` (32-bit)

## Troubleshooting

### Overlay not mounted
```bash
mql chroot --mount
```

### Permission denied on RPM
```bash
sudo chown $(id -u):$(id -g) RPMS/x86_64/*.rpm
```

### Build fails inside chroot
Ensure the overlay is mounted:
```bash
mountpoint /mnt/maquilinux/merged
```

### Stale overlay mounts after crash
```bash
sudo umount -l /mnt/maquilinux/merged/{mnt/repo,dev/shm,dev/pts,dev,run,sys,proc}
sudo umount -l /mnt/maquilinux/merged
```

## CI/CD Pipeline

Every push to `main` that changes `SPECS/*.spec` or `SOURCES/*` triggers:

1. **Backup** — Pre-build snapshot of rootfs
2. **Build** — Build changed specs inside chroot
3. **Sign** — GPG sign RPMs with `rpmsign --addsign`
4. **Install** — Install built RPMs in chroot
5. **Repo Update** — Regenerate repodata with `createrepo_c`
6. **Sync** — Push to `repo.glats.org` via `rsync`
7. **Backup** — Post-build snapshot

### Monitoring the Pipeline

```bash
# List recent runs
gh run list --limit 5

# Watch a specific run
gh run watch <run-id>

# View run details
gh run view <run-id>

# View job logs
gh run view --job=<job-id> --log
```

## Contact

- Issues: https://github.com/glats/maquilinux/issues
- Email: security@maqui-linux.org
