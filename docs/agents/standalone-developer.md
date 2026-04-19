# Standalone Developer Setup (Without Runner)

Set up a complete Maqui Linux development environment using a pre-built rootfs from **maquiroot.glats.org**. No self-hosted runner required — download the rootfs, develop locally, push to GitHub when ready.

**Rootfs Source**: https://maquiroot.glats.org

This is a public mirror of the Maqui Linux rootfs backups. The CI/CD runner (thinkcentre) creates museum-style backups before every build, which are periodically synced to this public endpoint.

---

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/glats/maquilinux.git ~/Work/maquilinux
cd ~/Work/maquilinux

# 2. Download latest rootfs (~4GB compressed)
curl -o maquilinux-rootfs-latest.tar.xz \
  https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz

# 3. Verify checksum
curl -o maquilinux-rootfs-latest.tar.xz.sha256 \
  https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz.sha256
sha256sum -c maquilinux-rootfs-latest.tar.xz.sha256

# 4. Create partition and extract (see details below)
# ...

# 5. Configure and start building
./mql status
./mql chroot
```

---

## Download Rootfs

### Option A: Latest Stable (Recommended)

```bash
# Latest tagged release
curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz
curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz.sha256
curl -O https://maquiroot.glats.org/latest/metadata.json

# Verify
sha256sum -c *.sha256
```

### Option B: Specific Date/Version

```bash
# List available backups
curl https://maquiroot.glats.org/index.json | jq '.backups[] | {date, tag, size}'

# Download specific
curl -O https://maquiroot.glats.org/2026-04-18/maquilinux-20260418-120000-base.tar.xz
```

### Option C: Minimal Bootstrap (Advanced)

For those who want to build everything from scratch:

```bash
# Minimal bootstrap rootfs (~500MB)
curl -O https://maquiroot.glats.org/bootstrap/maquilinux-bootstrap.tar.xz
# Then bootstrap gcc, glibc, etc. (see docs/BOOTSTRAP.md)
```

---

## About the Backup System

Maqui Linux uses a **museum-style backup system** — backups are never deleted, only archived.

### Storage Tiers

| Tier | Location | Retention | Access |
|------|----------|-----------|--------|
| **Hot** | CI/CD runner (`~/maqui-backups/`) | Last 90 days | Fast (local disk) |
| **Cold** | CI/CD runner (`~/maqui-archive/`) | Forever | Slower (can be NFS/S3) |
| **Public** | `maquiroot.glats.org` | Selected snapshots | HTTP download |

### Automatic Backups & Sync

The CI/CD runner (thinkcentre) creates backups automatically:
- **Before every build**: `pre-build-<tag>.tar.xz` (local only)
- **After successful builds**: `post-build-<tag>-ok.tar.xz` → **auto-synced to maquiroot.glats.org**

### Sync to maquiroot.glats.org

Successful builds are automatically synchronized:
```
thinkcentre (runner)
   ~/maqui-backups/maquilinux-YYYYMMDD-HHMMSS-post-build-ok.tar.xz
            ↓ rsync
   rog:/srv/maquiroot/incoming/
   rog:/srv/maquiroot/latest/maquilinux-rootfs-latest.tar.xz (symlink)
            ↓
   https://maquiroot.glats.org/latest/
```

### Directory Listing

Browse all available rootfs backups:

**Web:** https://maquiroot.glats.org/  
*(Simple directory listing with all tarballs, organized by date)*

**JSON API (for scripts):**
```bash
curl https://maquiroot.glats.org/index.json | jq '.backups[] | {date, tag, size}'
```

### Server Configuration (rog)

The nginx server should have **autoindex on** for the maquiroot directory:

```nginx
server {
    listen 443 ssl;
    server_name maquiroot.glats.org;
    
    root /srv/maquiroot;
    autoindex on;              # ← Directory listing
    autoindex_exact_size off;  # ← Human-readable sizes
    autoindex_localtime on;    # ← Local timestamps
    
    # Also serve index.json for API access
    location = /index.json {
        alias /srv/maquiroot/index.json;
    }
}
```

This provides both:
- **Human browsing**: https://maquiroot.glats.org/ (directory listing)
- **Machine API**: https://maquiroot.glats.org/index.json (JSON)

### Metadata

Each backup includes a `.meta` file with:
```json
{
  "timestamp": "2026-04-18T12:00:00",
  "tag": "pre-rust-bootstrap",
  "git_commit": "abc1234",
  "packages_count": 136,
  "size": "3.8GB"
}
```

---

## Install Rootfs

### Prepare Disk/Partition

```bash
# Option 1: Dedicated USB/external disk
lsblk  # Find your device (e.g., /dev/sdb)
sudo parted /dev/sdb mklabel gpt
sudo parted /dev/sdb mkpart primary ext4 0% 100%
sudo mkfs.ext4 -L maquilinux /dev/sdb1

# Option 2: Loop file (for testing, no dedicated disk)
sudo mkdir -p /var/lib/maquilinux
cd /var/lib/maquilinux
sudo dd if=/dev/zero of=disk.img bs=1M count=61440  # 60GB
sudo mkfs.ext4 -F disk.img
sudo mount -o loop disk.img /mnt/maquilinux

# Option 3: Existing partition (any spare partition)
sudo mkfs.ext4 -L maquilinux /dev/sdXN
```

### Extract Rootfs

```bash
# Mount target
sudo mkdir -p /mnt/maquilinux
sudo mount /dev/sdb1 /mnt/maquilinux  # or /mnt from loop above

# Extract (takes 5-10 minutes)
sudo tar -xJf maquilinux-rootfs-latest.tar.xz -C /mnt/maquilinux

# Create overlay structure
sudo mkdir -p /mnt/maquilinux/layers/upper /mnt/maquilinux/layers/work
sudo mkdir -p /mnt/maquilinux/merged
```

### Mount Overlay

```bash
# Mount overlay filesystem
sudo mount -t overlay overlay \
  -o lowerdir=/mnt/maquilinux,upperdir=/mnt/maquilinux/layers/upper,\
workdir=/mnt/maquilinux/layers/work \
  /mnt/maquilinux/merged

# Verify
mount | grep maquilinux
ls /mnt/maquilinux/merged/bin  # Should show bash, rpm, etc.
```

---

## Configure mql

```bash
cd ~/Work/maquilinux

# Create local config
cat > mql.local << 'EOF'
# Path to your Maqui Linux installation
MQL_LFS=/mnt/maquilinux
EOF

# Verify
./mql status
# Should show: MQL_LFS=/mnt/maquilinux
```

---

## Start Working

### Enter Chroot

```bash
./mql chroot
# Now you're inside Maqui Linux rootfs

# Test
cat /etc/maquilinux-release
rpm --version
dnf --version
```

### Build a Package

```bash
# Outside chroot (from repo directory)
./mql build bash

# Or manually enter chroot and use rpmbuild
./mql chroot --exec "cd /workspace && rpmbuild -ba SPECS/bash.spec"
```

### Test in Chroot

```bash
./mql chroot

# Install your built RPM
dnf install /workspace/RPMS/x86_64/bash-*.rpm

# Test it
bash --version
```

---

## Two Work Modes

### Mode 1: Local Development (No Push)

For testing, experimenting, learning:

```bash
# Edit specs locally
vim SPECS/my-new-package.spec

# Build locally
./mql build my-new-package --both

# Test in chroot
./mql chroot --exec "rpm -ivh /workspace/RPMS/x86_64/my-new-package-*.rpm"

# Iterate until it works
# No GitHub interaction needed
```

### Mode 2: CI/CD (With Push)

When ready to contribute or use runner:

```bash
# Stage your changes
git add SPECS/my-new-package.spec SOURCES/my-source.tar.gz
git commit -m "feat: add my-new-package for XYZ purpose"

# Push to GitHub
git push origin main

# Runner (if configured) automatically:
# 1. Detects changed spec
# 2. Builds package
# 3. Updates repo.glats.org
# 4. Installs in rootfs
```

---

## Staying Updated

### Update Your Rootfs

When new packages are built (by you or CI/CD):

```bash
# Option A: Sync with repo (if repo.glats.org has newer packages)
./mql chroot --exec "dnf upgrade"

# Option B: Download fresh rootfs backup
# (Useful if your local rootfs got corrupted or too old)
curl -O https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz
# Re-extract to fresh partition
```

### Backup Your Changes

Before risky operations:

```bash
./mql backup create before-big-change
# Creates: ~/maqui-backups/maquilinux-YYYYMMDD-HHMMSS-before-big-change.tar.xz
```

---

## Server Structure

The rootfs server provides:

```
maquiroot.glats.org/
├── latest/
│   ├── maquilinux-rootfs-latest.tar.xz      → symlink to latest
│   ├── maquilinux-rootfs-latest.tar.xz.sha256
│   └── metadata.json                        (date, packages, git commit)
│
├── 2026-04-18/                              (daily archives)
│   ├── maquilinux-20260418-120000-base.tar.xz
│   ├── maquilinux-20260418-180000-post-rust.tar.xz
│   └── ...
│
├── bootstrap/                               (minimal for scratch builds)
│   └── maquilinux-bootstrap.tar.xz
│
└── index.json                               (list all available)
```

---

## Troubleshooting

### "Overlay already mounted"

```bash
# Unmount and remount
sudo umount -l /mnt/maquilinux/merged
sudo mount -t overlay ...  # (see above)
```

### "No space left on device"

```bash
# Check
df -h /mnt/maquilinux

# Expand loop file (if using loop)
sudo umount /mnt/maquilinux
cd /var/lib/maquilinux
truncate -s +20G disk.img
sudo e2fsck -f disk.img
sudo resize2fs disk.img
sudo mount -o loop disk.img /mnt/maquilinux
# Recreate overlay structure
```

### "Cannot find MQL_LFS"

```bash
# Check mql.local exists and is readable
cat mql.local
# Should show: MQL_LFS=/mnt/maquilinux

# Check path exists
ls $MQL_LFS/merged/bin/bash
```

### Download Slow/Fails

```bash
# Use wget with resume
wget -c https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz

# Or use aria2 for faster download
aria2c -x4 https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz
```

---

## Next Steps

- **Build your first package:** See `docs/GETTING-STARTED.md`
- **Set up your own runner:** See `docs/agents/runner-setup.md`
- **Understand the overlay system:** See `docs/DEVELOPMENT-SYSTEM-PLAN.md`
- **Backup system:** See `docs/agents/backup-system.md`

---

## Comparison: Local vs CI/CD

| Aspect | Local Development | CI/CD with Runner |
|--------|-------------------|-------------------|
| **Setup** | Download rootfs, mount | Same + runner setup |
| **Build** | `./mql build <spec>` | Push, runner builds |
| **Speed** | Immediate | Queue + build time |
| **Repo update** | Manual (`./mql repo update`) | Automatic |
| **Best for** | Learning, testing, iterating | Production, sharing |
| **Push required** | No | Yes |

**Recommendation:** Use **Local** for development and testing, **CI/CD** for final integration.
