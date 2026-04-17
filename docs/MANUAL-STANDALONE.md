# Maqui Linux Developer Manual -- Standalone (No Nix)

Guide for developing Maqui Linux on any Linux distribution without Nix.
This covers Fedora, Debian/Ubuntu, Arch, openSUSE, or Maqui Linux
itself (self-hosting).

---

## 1. Prerequisites

- Any Linux distribution (x86_64) with root access.
- A dedicated disk or partition for the chroot (recommended: >= 20 GB).
- Kernel with overlayfs support (standard on all modern kernels).
- bash >= 5.0.

---

## 2. Install Required Tools

### 2.1 What You Need

Install only the tools required for your workflow. Not everything is
needed at once.

**Always needed:**

| Tool        | Purpose                          |
| ----------- | -------------------------------- |
| `bash`      | Shell (>= 5.0)                   |
| `coreutils` | Standard utilities               |
| `util-linux`| mount, chroot, lsblk             |
| `tar`       | Extract rootfs tarball           |
| `rsync`     | Sync repos and snapshots         |

**For building packages (inside chroot):**

Building happens inside the Maqui Linux chroot using its native
`rpmbuild` and `gcc`. You do not need rpm or gcc on the host.

**For repo management:**

| Tool           | Purpose                          |
| -------------- | -------------------------------- |
| `createrepo_c` | Generate RPM repo metadata       |

**For ISO generation:**

| Tool           | Purpose                          |
| -------------- | -------------------------------- |
| `xorriso`      | Create bootable ISO images       |
| `mksquashfs`   | Compress rootfs into squashfs    |
| `mtools`       | Create EFI FAT images            |

**For testing:**

| Tool                  | Purpose                   |
| --------------------- | ------------------------- |
| `qemu-system-x86_64`  | Boot ISO/rootfs in VM     |

### 2.2 Installation by Distribution

**Fedora / RHEL / CentOS:**

```bash
# Core (always)
sudo dnf install bash coreutils util-linux tar rsync

# Repo management
sudo dnf install createrepo_c

# ISO generation
sudo dnf install xorriso squashfs-tools mtools

# Testing
sudo dnf install qemu-system-x86
```

**Debian / Ubuntu:**

```bash
# Core (always)
sudo apt install bash coreutils util-linux tar rsync

# Repo management
sudo apt install createrepo-c

# ISO generation
sudo apt install xorriso squashfs-tools mtools

# Testing
sudo apt install qemu-system-x86
```

**Arch Linux:**

```bash
# Core (always, most are pre-installed)
sudo pacman -S bash coreutils util-linux tar rsync

# Repo management (AUR)
yay -S createrepo_c

# ISO generation
sudo pacman -S libisoburn squashfs-tools mtools

# Testing
sudo pacman -S qemu-system-x86
```

**openSUSE:**

```bash
sudo zypper install bash coreutils util-linux tar rsync \
  createrepo_c xorriso squashfs mtools qemu-x86
```

**Maqui Linux (self-hosting):**

```bash
dnf install rpm-build createrepo_c libisoburn squashfs-tools \
  mtools dracut busybox dhcpcd qemu  # dracut = dracut-ng 110
```

When all 7 self-hosting specs are built, Maqui Linux can install
everything it needs from its own repository.

---

## 3. Getting Started

### 3.1 Obtain the Repository

```bash
# If hosted on git:
git clone https://github.com/glats/maquilinux.git
cd maquilinux

# Or copy/sync the working directory:
rsync -a user@host:~/Work/maquilinux/ ~/maquilinux/
cd ~/maquilinux
```

### 3.2 Add `mql` to PATH

```bash
export PATH="$PWD:$PATH"

# Or permanently (add to ~/.bashrc or ~/.zshrc):
echo 'export PATH="$HOME/maquilinux:$PATH"' >> ~/.bashrc
```

### 3.3 Configure the Mount Point

Edit `mql.local` (gitignored) to set where your disk is mounted.
This overrides the default in `mql.conf`:

```bash
# Check defaults
cat mql.conf

# Override for your setup (disk auto-mounted by your desktop, etc.)
echo "MQL_LFS=/run/media/$USER/maquilinux" >> mql.local

# Or override per-session:
export MQL_LFS=/run/media/$USER/maquilinux

# Verify
mql config
```

Key variables in `mql.conf` / `mql.local`:

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `MQL_LFS` | `/mnt/maquilinux` | Disk mount point |
| `MQL_DISK` | `/dev/sdd1` | Block device |
| `MQL_RELEASEVER` | `26.4` | DNF release version |
| `MQL_REPO_DEST` | `/srv/glats/nginx/repo/...` | Production repo path |
| `MQL_KERNEL_VERSION` | `6.17.9` | Kernel for ISO |

Verify:

```bash
mql help
```

### 3.3 Prepare the Disk

**Important:** The disk may auto-mount at `/run/media/$USER/maquilinux/`
due to desktop environment auto-mounting. Check and unmount if needed:

```bash
# Check current mounts
mount | grep sdd

# If mounted at /run/media/, unmount it
sudo umount /run/media/$USER/maquilinux 2>/dev/null || true
```

Identify your target disk (here `/dev/sdd`, adapt as needed):

```bash
lsblk
```

**Partition and format** (skip if already done):

```bash
sudo bash -c '
  echo -e "g\nn\n1\n\n\nw" | fdisk /dev/sdd
  mkfs.ext4 -L maquilinux /dev/sdd1
'
```

**Mount at the development location:**

```bash
sudo mkdir -p /mnt/maquilinux
sudo mount /dev/sdd1 /mnt/maquilinux
```

### 3.4 Extract and Restructure the Rootfs

**Initial setup** (first time only):

```bash
# Extract the rootfs tarball
sudo tar xJpf maquilinux.tar.xz -C /mnt/maquilinux
```

The `p` flag preserves ownership and permissions. The `J` flag
handles xz decompression.

### 3.5 Set Up the Overlay Structure

```bash
cd /mnt/maquilinux

sudo mkdir -p base
sudo mv bin boot dev etc home lib lib64 media mnt opt proc root \
  run sbin srv sys tmp usr var base/

sudo mkdir -p layers/{upper,work,snapshots}
sudo mkdir -p merged
sudo mkdir -p repo
sudo mkdir -p sources  # optional bind-mount
```

Result:

```
/mnt/maquilinux/                  <- ext4 partition (label: maquilinux)
├── base/                         <- immutable rootfs (~3.5GB)
├── layers/
│   ├── upper/                    <- current overlay changes
│   ├── work/                     <- overlayfs workdir (required)
│   └── snapshots/                <- saved checkpoints
├── merged/                       <- unified view (chroot target)
├── repo/                         <- local RPM repo (bind-mounted as /mnt/repo)
└── sources/                      <- optional bind-mount of project SOURCES/
```

**Verify:**
```bash
ls -la /mnt/maquilinux/
ls /mnt/maquilinux/base/
```

---

## 4. Daily Workflow

### 4.1 Enter the Chroot

```bash
mql chroot
```

This mounts the overlay, virtual kernel filesystems (`/dev`, `/proc`,
`/sys`, `/run`), bind-mounts the local repo, and enters an interactive
bash session. Exit with `exit` or `Ctrl-D`; everything unmounts
automatically.

### 4.2 Run a Command Without Entering

```bash
mql chroot --exec "rpm -qa"
mql chroot --exec "rc-status"
mql chroot --exec "cat /etc/os-release"
```

### 4.3 Reset (Discard All Changes)

```bash
mql chroot --reset
```

Wipes the overlay upper layer. The next `mql chroot` starts from the
pristine base rootfs.

### 4.4 Save a Snapshot

```bash
mql chroot --persist "before-gcc-rebuild"
```

Creates a copy of the current overlay in
`layers/snapshots/YYYY-MM-DD-before-gcc-rebuild/`.

### 4.5 Restore a Snapshot

```bash
# List available snapshots
ls /mnt/maquilinux/layers/snapshots/

# Restore one (replaces current upper)
sudo rm -rf /mnt/maquilinux/layers/upper
sudo cp -a /mnt/maquilinux/layers/snapshots/2026-03-24-before-gcc-rebuild \
  /mnt/maquilinux/layers/upper
```

### 4.6 Promote Overlay to New Base

When the overlay contains changes you want to keep permanently:

```bash
mql chroot --promote
```

Merges the overlay into the base and clears the overlay. The next
chroot session starts with the updated base.

### 4.7 Regenerate Base from RPMs

For a completely clean base derived from published RPMs:

```bash
mql release rootfs --target /mnt/maquilinux/base
```

This is the preferred method before formal releases. It produces
a rootfs without any manual changes or build artifacts.

---

## 5. Building Packages

All builds happen inside the Maqui Linux chroot, using its native GCC,
rpmbuild, and libraries. The host does not need any build tools.

### 5.1 Build a Single Package

```bash
mql build openrc
```

Options:

```bash
mql build openrc --both       # 64-bit and 32-bit
mql build openrc --arch i686  # 32-bit only
```

Output: `RPMS/x86_64/openrc-*.rpm` (and `RPMS/i686/` if `--both`).

### 5.2 Install a Package into the Chroot

```bash
mql install openrc
```

If the RPM has not been built yet, it is built automatically first.

### 5.3 Build All Packages

```bash
mql build --all
```

Builds all 109+ specs in dependency order. Supports:

```bash
mql build --all --resume        # Continue from last failure
mql build --all --fast          # Skip tests
mql build --all --only gcc      # Build only one package
mql build --all --keep-going    # Don't stop on failure
```

### 5.4 Writing a New Spec

Specs follow the Gen3 template documented in `SPECS/SPEC_TEMPLATE.md`.
Key conventions:

- Disable debug packages:
  ```
  %global debug_package %{nil}
  ```
- Use multiarch conditionals for 32/64-bit.
- Generate file lists dynamically with `find | sed | sort`.
- Run `ldconfig` in `%post` / `%postun` for shared libraries.
- Release tag: `1.m264` (m264 = maquilinux 26.4).

Place the new spec in `SPECS/` and sources in `SOURCES/` (or
`/sources/` inside the chroot).

---

## 6. Managing the RPM Repository

### 6.1 Update Local Repo

```bash
mql repo update
```

Runs `createrepo_c` on the `RPMS/` directory to generate metadata.
After this, `dnf install` inside the chroot can find the new packages
via the `maquilinux-local` repo.

### 6.2 List Packages

```bash
mql repo list
```

### 6.3 Sync to Production Server

```bash
mql repo sync
```

By default this rsyncs to `/srv/glats/nginx/repo/maquilinux/26.4/`.
If your production server is remote:

```bash
# Configure in lib/repo.sh or pass as env var:
MQL_REPO_DEST="user@server:/var/www/repo/maquilinux/26.4/" \
  mql repo sync
```

### 6.4 Serving the Repo

The repo is a directory of static files. Any web server works:

**nginx (manual config):**

```nginx
server {
    listen 443 ssl;
    server_name repo.example.com;
    ssl_certificate /etc/ssl/certs/repo.pem;
    ssl_certificate_key /etc/ssl/private/repo.key;

    location /linux/ {
        alias /path/to/repo/;
        autoindex on;
    }
}
```

**Python (quick test, no HTTPS):**

```bash
cd /path/to/repo
python3 -m http.server 8080
# Repo accessible at http://localhost:8080/maquilinux/26.4/...
```

**caddy:**

```
repo.example.com {
    root * /path/to/repo
    file_server browse
}
```

---

## 7. Testing

### 7.1 QEMU VM Boot

```bash
mql test vm
```

Boots Maqui Linux in QEMU with serial console. Press `Ctrl-A X` to
exit.

If QEMU is not available, test manually in the chroot:

```bash
mql chroot
# Inside:
rc-status           # Check OpenRC services
rpm -qa | wc -l     # Count installed packages
gcc -o /tmp/hello /tmp/hello.c && /tmp/hello   # Compile test
```

### 7.2 Smoke Tests

```bash
mql test smoke
```

Runs automated checks against the chroot.

### 7.3 Independence Verification

```bash
mql test verify
```

Confirms the system is free of LFS temporary toolchain dependencies.

---

## 8. Generating a Release

All release artifacts (rootfs, tarball, ISO) are derived from the RPM
repository. The RPMs are the source of truth. Artifacts are regenerated
for each formal release; they are not stored in git.

### 8.1 Generate a Clean Rootfs

```bash
mql release rootfs
```

Creates a rootfs directory from RPMs via `dnf5 --installroot`.
Configured with proper fstab, hostname, CA certificates, and repo
config. This rootfs is the base for both the tarball and the ISO.

### 8.2 Generate a Rootfs Tarball

```bash
mql release tarball
```

Packages the rootfs as `maquilinux-26.4-rootfs.tar.xz`. Published
for developers and for the disk installer.

### 8.3 Build a Live ISO

```bash
mql release iso
```

This requires `xorriso`, `mksquashfs`, and `mtools` on the host (or
inside Maqui Linux itself if self-hosting).

The pipeline:
1. Creates a clean rootfs from RPMs.
2. Removes LFS vestiges.
3. Configures the rootfs for live boot (fstab, hostname, networking).
4. Generates initramfs with dracut-ng.
5. Compresses rootfs into squashfs.
6. Assembles ISO with GRUB (BIOS + UEFI).

Output: `maquilinux-26.4-x86_64.iso`

### 8.4 Test the ISO

```bash
# QEMU
qemu-system-x86_64 -cdrom maquilinux-26.4-x86_64.iso -m 2G -enable-kvm

# USB
sudo dd if=maquilinux-26.4-x86_64.iso of=/dev/sdX bs=4M status=progress
```

### 8.5 Publish Release Artifacts

Artifacts are published to the repo server and/or GitHub:

```bash
# Sync to repo.glats.org/linux/maquilinux/images/
mql repo sync

# Or GitHub Releases
gh release create v26.4 \
  maquilinux-26.4-rootfs.tar.xz \
  maquilinux-26.4-x86_64.iso
```

### 8.6 Complete Release Flow

```bash
mql build --all               # Build all RPMs
mql repo update               # Regenerate repo metadata
mql repo sync                 # Publish RPMs to production
mql release rootfs            # Generate rootfs from RPMs
mql release tarball           # Package as .tar.xz
mql release iso               # Package as bootable ISO
# Publish tarball + ISO
```

The same RPMs always produce the same rootfs, tarball, and ISO.
Updating a package and re-running the release commands produces
updated artifacts automatically.

---

## 9. Self-Hosting: Building Maqui Linux From Maqui Linux

As of 2026-04-02, Maqui Linux is **fully self-hosting**. The following 7
packages are built, installed, and available in the base rootfs:

| Package          | Purpose                 |
| ---------------- | ----------------------- |
| `dracut`         | Initramfs generation (dracut-ng 110) |
| `busybox`        | dracut-ng backend       |
| `dhcpcd`         | DHCP for live networking |
| `createrepo_c`   | Repo metadata           |
| `libisoburn`     | xorriso / ISO creation  |
| `squashfs-tools` | Rootfs compression      |
| `mtools`         | EFI image creation      |

Install them on a fresh Maqui Linux install:

```bash
dnf install dracut busybox dhcpcd createrepo_c \
  libisoburn squashfs-tools mtools  # dracut = dracut-ng 110
```

The full cycle runs natively on Maqui Linux without any external host:

```bash
mql build --all
mql repo update
mql release iso
# ISO built entirely by Maqui Linux
```

---

## 10. Manual Chroot (Without `mql`)

If `mql` is not available or you prefer manual control, this is the
equivalent procedure:

### 10.1 Mount the Overlay

```bash
export LFS=/mnt/maquilinux

# Mount the disk
sudo mount /dev/sdd1 "$LFS"

# Mount overlay
sudo mount -t overlay overlay \
  -o lowerdir="$LFS/base",upperdir="$LFS/layers/upper",workdir="$LFS/layers/work" \
  "$LFS/merged"
```

### 10.2 Mount Virtual Filesystems

```bash
sudo mkdir -pv "$LFS/merged"/{dev,proc,sys,run}

sudo mount -v --bind /dev "$LFS/merged/dev"
sudo mount -vt devpts devpts -o gid=5,mode=0620 "$LFS/merged/dev/pts"
sudo mount -vt proc   proc   "$LFS/merged/proc"
sudo mount -vt sysfs  sysfs  "$LFS/merged/sys"
sudo mount -vt tmpfs  tmpfs  "$LFS/merged/run"

if [ -h "$LFS/merged/dev/shm" ]; then
    sudo install -v -d -m 1777 "$LFS/merged$(realpath /dev/shm)"
else
    sudo mount -vt tmpfs -o nosuid,nodev tmpfs "$LFS/merged/dev/shm"
fi
```

### 10.3 Enter the Chroot

```bash
sudo chroot "$LFS/merged" /usr/bin/env -i \
    HOME=/root \
    TERM="$TERM" \
    PS1='(maquilinux) \u:\w\$ ' \
    PATH=/usr/bin:/usr/sbin \
    /bin/bash --login
```

### 10.4 Exit and Cleanup

```bash
# Exit chroot
exit

# Unmount (reverse order)
sudo umount "$LFS/merged/dev/pts"
sudo umount "$LFS/merged/dev/shm" 2>/dev/null || true
sudo umount "$LFS/merged/dev"
sudo umount "$LFS/merged/sys"
sudo umount "$LFS/merged/proc"
sudo umount "$LFS/merged/run"
sudo umount "$LFS/merged"       # overlay
sudo umount "$LFS"              # disk
```

---

## 11. Project Structure Reference

```
~/maquilinux/
  mql                   <- run: ./mql <command>
  AGENTS.md             <- context for OpenCode

  SPECS/                <- 109+ RPM spec files
  SOURCES/              <- source tarballs + patches

  lib/                  <- mql library (bash)
  scripts/              <- build scripts
  tools/                <- maintenance tools
  release/              <- ISO configs, dracut-ng, branding

  RPMS/                 <- (gitignored) built RPMs
  SRPMS/                <- (gitignored) source RPMs
  BUILD/                <- (gitignored) rpmbuild workspace
  BUILDROOT/            <- (gitignored) rpmbuild staging

/mnt/maquilinux/        <- development disk (ext4, 119GB)
  base/                 <- immutable rootfs (~3.5GB)
  layers/
    upper/              <- overlay changes (mutable)
    work/               <- overlayfs workdir
    snapshots/          <- saved checkpoints
  merged/               <- unified view (chroot target)
  repo/                 <- local RPM repo
  sources/              <- bind-mount of project SOURCES/
```

---

## 12. Troubleshooting

### Disk auto-mounted at /run/media/

Desktop environments often auto-mount removable disks at
`/run/media/$USER/maquilinux/`. This interferes with the development
workflow which expects the disk at `/mnt/maquilinux`.

**Check:**
```bash
mount | grep sdd
```

**Fix:**
```bash
# Unmount from auto-location
sudo umount /run/media/$USER/maquilinux

# Mount at correct location
sudo mount /dev/sdd1 /mnt/maquilinux
```

**Prevent:** Add to `/etc/fstab` with `noauto` option or configure
your desktop's auto-mount settings.

### overlayfs mount fails with "wrong fs type"

Your kernel may not have overlayfs. Check:

```bash
cat /proc/filesystems | grep overlay
```

If missing, load the module:

```bash
sudo modprobe overlay
```

### "device or resource busy" when unmounting

A process is still running inside the chroot. Find and kill it:

```bash
sudo fuser -vm /mnt/maquilinux/merged
sudo fuser -k /mnt/maquilinux/merged
```

Then unmount.

### createrepo_c: command not found

Install it for your distribution (see section 2.2). On Fedora:

```bash
sudo dnf install createrepo_c
```

### rpmbuild fails: "Bad exit status"

This runs inside the chroot, not on the host. Enter the chroot and
check the build log:

```bash
mql chroot
cat /sources/maquilinux/logs/mlfs/<package>.log
```

### xorriso: command not found

Install it:

```bash
# Fedora
sudo dnf install xorriso

# Debian
sudo apt install xorriso

# Arch
sudo pacman -S libisoburn
```

### Snapshot restore fails with permission errors

Snapshots must be copied as root to preserve file ownership:

```bash
sudo cp -a /mnt/maquilinux/layers/snapshots/name/ \
  /mnt/maquilinux/layers/upper/
```

### The chroot has no network access

The chroot inherits `/etc/resolv.conf` from the base rootfs. If DNS
does not work:

```bash
# From the host, copy the current resolv.conf into the chroot
sudo cp /etc/resolv.conf /mnt/maquilinux/merged/etc/resolv.conf
```

### RPM install fails with missing dependencies (bootstrap)

LFS-era libraries (`librpm`, `libsqlite3`, etc.) are on the filesystem but not
in RPM's database. `rpm -i` without `--nodeps` will reject packages that list
those libraries as dependencies, even though the `.so` files are present.

**Fix:** Always use `--nodeps --nosignature` for direct RPM installs:

```bash
mql chroot --exec "rpm -ivh --nosignature --nodeps /mnt/repo/<package>-*.rpm"
```

Once `dnf` is managing the system, this is no longer needed.
