# Maqui Linux Developer Manual -- NixOS / Nix

Guide for developing Maqui Linux on a system with Nix installed.
This is the recommended setup when working on the ROG development
machine or any NixOS host.

---

## 1. Prerequisites

- NixOS or any Linux with Nix installed (flakes enabled).
- `/dev/sdd` available and formatted (or any disk for the chroot).
- Access to the maquilinux repository at `~/Work/maquilinux/`.

Verify Nix is working:

```bash
nix --version
```

---

## 2. Getting Started

### 2.1 Enter the Development Environment

```bash
cd ~/Work/maquilinux
nix develop
```

This drops you into a shell with every tool needed:

| Tool            | Version    | Purpose                    |
| --------------- | ---------- | -------------------------- |
| `rpm`           | 4.x        | RPM queries and inspection |
| `rpmbuild`      | 4.x        | Build RPMs (host-side)     |
| `createrepo_c`  | latest     | Generate repo metadata     |
| `xorriso`       | latest     | Create ISO images          |
| `mkisofs`       | latest     | Alternative ISO tool       |
| `mksquashfs`    | latest     | Compress rootfs            |
| `dracut`        | latest     | Generate initramfs (dracut-ng) |
| `qemu-system-x86_64` | latest | Test ISOs and VMs     |
| `file`          | latest     | Inspect binaries           |
| `tree`          | latest     | Visualize directories      |

The `mql` CLI is automatically added to your PATH via the shell hook.
The shell hook also auto-detects the disk mount point and sets `MQL_LFS`.

### 2.2 Configure the Mount Point

`mql` uses `mql.conf` for defaults and `mql.local` for user overrides.
The most important variable is `MQL_LFS` -- the path where the development
disk is mounted.

```bash
# Check what mql detected
mql config

# If the disk is auto-mounted at a different path (e.g. by udisks2):
echo "MQL_LFS=/run/media/$USER/maquilinux" >> mql.local

# Or set per-session:
export MQL_LFS=/run/media/$USER/maquilinux
```

`mql.local` is gitignored -- create it once and it persists across sessions.

### 2.3 First-Time Disk Setup

**Important:** The disk may auto-mount at `/run/media/$USER/maquilinux/`
due to udisks2. If so, unmount it first:

```bash
sudo umount /run/media/$USER/maquilinux
```

Then proceed with setup:

```bash
# Partition the disk (single ext4 partition) - SKIP if already done
sudo bash -c '
  echo -e "g\nn\n1\n\n\nw" | fdisk /dev/sdd
  mkfs.ext4 -L maquilinux /dev/sdd1
'

# Mount at the correct location
sudo mkdir -p /mnt/maquilinux
sudo mount /dev/sdd1 /mnt/maquilinux

# Extract the rootfs tarball (ONLY for initial setup)
sudo tar xJpf ~/maquilinux.tar.xz -C /mnt/maquilinux
```

### 2.3 Set Up the Overlay Structure

Once the rootfs is extracted, restructure it for overlay-based
development:

```bash
cd /mnt/maquilinux

# Move the rootfs into base/ (immutable layer)
sudo mkdir -p base
sudo mv bin boot dev etc home lib lib64 media mnt opt proc root \
  run sbin srv sys tmp usr var base/

# Create overlay directories
sudo mkdir -p layers/{upper,work,snapshots}
sudo mkdir -p merged
sudo mkdir -p repo
sudo mkdir -p sources  # Optional: bind-mount of SOURCES/
```

After this, the partition layout is:

```
/mnt/maquilinux/                  <- ext4 partition (label: maquilinux)
├── base/                         <- immutable rootfs (extracted tarball)
│   ├── bin -> usr/bin
│   ├── boot/
│   ├── etc/
│   └── ...
├── layers/
│   ├── upper/                    <- current overlay changes
│   ├── work/                     <- overlayfs workdir
│   └── snapshots/                <- named snapshots
├── merged/                       <- unified view (chroot target)
├── repo/                         <- local RPM repo (bind-mounted as /mnt/repo)
└── sources/                      <- optional bind-mount of project SOURCES/
```

**Verify the structure:**
```bash
ls -la /mnt/maquilinux/
# Should show: base/, layers/, merged/, repo/, sources/

ls /mnt/maquilinux/base/
# Should show the rootfs directories: bin, boot, dev, etc, usr, var...
```

---

## 3. Daily Workflow

### 3.1 Enter the Chroot

```bash
mql chroot
```

This mounts the overlay, virtual kernel filesystems, bind-mounts the
local repo, and drops you into an interactive bash session inside Maqui
Linux. When you type `exit`, everything is unmounted automatically.

The prompt inside the chroot looks like:

```
(maquilinux) root:/# 
```

### 3.2 Run a Single Command in the Chroot

```bash
mql chroot --exec "rpm -qa | wc -l"
mql chroot --exec "rc-status"
mql chroot --exec "gcc --version"
```

### 3.3 Reset the Chroot (Discard Changes)

```bash
mql chroot --reset
```

This deletes the overlay upper layer, restoring the chroot to the
pristine base. Use this when you want to start fresh after
experimentation.

### 3.4 Save a Snapshot

```bash
mql chroot --persist "post-openrc-update"
```

Copies the current overlay upper layer to
`layers/snapshots/YYYY-MM-DD-post-openrc-update/`. You can manually
restore a snapshot by copying it back to `layers/upper/`.

### 3.5 Promote Overlay to New Base

When the overlay contains changes you want to keep permanently:

```bash
mql chroot --promote
```

This merges the overlay upper layer into the base and clears the
overlay. The next `mql chroot` starts with the updated base.

### 3.6 Regenerate Base from RPMs

For a clean base derived entirely from published RPMs (no manual
changes or artifacts):

```bash
mql release rootfs --target /mnt/maquilinux/base
```

This is preferred before formal releases.

---

## 4. Building Packages

### 4.1 Build a Single Spec

```bash
mql build openrc
```

This runs `rpmbuild -ba` inside the chroot for `SPECS/openrc.spec`.
The resulting RPMs land in `RPMS/x86_64/` and/or `RPMS/i686/`.

Options:

```bash
mql build openrc --both       # Build 64-bit and 32-bit
mql build openrc --arch i686  # Build 32-bit only
```

### 4.2 Install a Built Package

```bash
mql install openrc
```

Installs the RPM into the chroot. If the RPM has not been built yet,
it builds it automatically.

### 4.3 Build All Packages

```bash
mql build --all
```

Runs the full build orchestrator (`mlfs-runner.sh`) which builds all
109+ packages in dependency order with smoke tests.

Options:

```bash
mql build --all --resume        # Resume from last failure
mql build --all --fast          # Skip tests (--nocheck)
mql build --all --only gcc      # Build only gcc
```

---

## 5. Managing the RPM Repository

### 5.1 Update Local Repo Metadata

After building packages, regenerate the repo metadata:

```bash
mql repo update
```

This runs `createrepo_c` on the `RPMS/` directory. The chroot can
then install packages from it via `dnf install`.

### 5.2 List Packages in the Local Repo

```bash
mql repo list
```

### 5.3 Sync to Production

Push local RPMs and metadata to the production repo served at
`repo.glats.org`:

```bash
mql repo sync
```

This rsyncs to `/srv/glats/nginx/repo/maquilinux/26.4/`. Nginx picks
up the changes immediately (no restart needed).

### 5.4 Verify the Production Repo

```bash
curl -sI https://repo.glats.org/linux/maquilinux/26.4/x86_64/stable/repodata/repomd.xml
```

Should return HTTP 200.

---

## 6. Testing

### 6.1 Boot in QEMU

```bash
mql test vm
```

Boots the Maqui Linux rootfs in a QEMU virtual machine with serial
console output. Press `Ctrl-A X` to exit QEMU.

### 6.2 Run Smoke Tests

```bash
mql test smoke
```

Automated checks: kernel boots, OpenRC starts services, rpm/dnf work,
gcc compiles, python runs.

### 6.3 Verify System Independence

```bash
mql test verify
```

Confirms no dependencies on the LFS temporary toolchain remain.

---

## 7. Generating a Release

All release artifacts are derived from the RPM repository. The RPMs
are the source of truth; the rootfs, tarball, and ISO are generated
from them.

### 7.1 Generate a Clean Rootfs

```bash
mql release rootfs
```

Creates a rootfs directory from RPMs via `dnf --installroot`.
This is the base for both the tarball and the ISO. The rootfs is
configured with proper fstab, hostname, CA certificates, and repo
config.

### 7.2 Generate a Rootfs Tarball

```bash
mql release tarball
```

Packages the rootfs as `maquilinux-26.4-rootfs.tar.xz`. This is
published for developers and for the disk installer.

### 7.3 Build a Live ISO

```bash
mql release iso
```

Pipeline:
1. Generates a clean rootfs from RPMs (`dnf --installroot`).
2. Cleans LFS vestiges.
3. Configures the rootfs for live boot.
4. Generates initramfs with dracut-ng.
5. Compresses rootfs with squashfs.
6. Assembles ISO with xorriso (BIOS + UEFI).

Output: `maquilinux-26.4-x86_64.iso` in the project root.

### 7.4 Test the ISO

```bash
# In QEMU
qemu-system-x86_64 -cdrom maquilinux-26.4-x86_64.iso -m 2G -enable-kvm

# Write to USB
sudo dd if=maquilinux-26.4-x86_64.iso of=/dev/sdX bs=4M status=progress
```

### 7.5 Publish Release Artifacts

```bash
# Sync tarball and ISO to repo.glats.org
mql repo sync

# Or publish to GitHub Releases
gh release create v26.4 \
  maquilinux-26.4-rootfs.tar.xz \
  maquilinux-26.4-x86_64.iso
```

Release artifacts are not stored in git. They are generated by
`mql release` and published to `repo.glats.org/linux/maquilinux/images/`
and/or GitHub Releases.

### 7.6 Complete Release Flow

```bash
mql build --all               # Build all RPMs
mql repo update               # Regenerate repo metadata
mql repo sync                 # Publish RPMs to repo.glats.org
mql release rootfs            # Generate rootfs from RPMs
mql release tarball           # Package as .tar.xz
mql release iso               # Package as bootable ISO
# Publish tarball + ISO
```

---

## 8. NixOS Host Configuration

### 8.1 RPM Repository Hosting

The repo is served by nginx on NixOS. The relevant config is in
`~/.nixos/modules/nginx.nix`:

```nix
"repo.glats.org" = {
  useACMEHost = "glats.org";
  forceSSL = true;
  locations."/linux/" = {
    alias = "/srv/glats/nginx/repo/";
    extraConfig = "autoindex on;";
  };
};
```

The wildcard certificate for `*.glats.org` is obtained via DNS-01
challenge with Cloudflare. Config is in the same file under
`security.acme.certs."glats.org"`.

### 8.2 Rebuilding NixOS After Config Changes

```bash
cd ~/.nixos
nixos-build          # or: sudo nixos-rebuild switch --flake '/etc/nixos#rog'
```

### 8.3 Disk Mount at Boot (Optional)

To auto-mount the development disk, add to `hardware-configuration.nix`
or a custom module:

```nix
fileSystems."/mnt/maquilinux" = {
  device = "/dev/disk/by-label/maquilinux";
  fsType = "ext4";
  options = [ "noauto" "user" ];
};
```

Use `noauto` to prevent mounting at boot; mount manually with
`sudo mount /mnt/maquilinux` when needed.

---

## 9. Project Structure Reference

```
~/Work/maquilinux/
  mql                   <- run: ./mql <command>
  flake.nix             <- run: nix develop
  AGENTS.md             <- context for OpenCode

  SPECS/                <- 109+ RPM spec files
  SOURCES/              <- source tarballs + patches

  lib/                  <- mql library (bash)
  scripts/              <- build scripts (existing)
  tools/                <- maintenance tools (existing)
  release/              <- ISO configs, dracut-ng, branding

  RPMS/                 <- (gitignored) built RPMs
  SRPMS/                <- (gitignored) source RPMs
  BUILD/                <- (gitignored) rpmbuild workspace
  BUILDROOT/            <- (gitignored) rpmbuild staging

/mnt/maquilinux/        <- development disk (ext4, 119GB)
                          (or /run/media/glats/maquilinux if auto-mounted
                           by udisks2 — set MQL_LFS in mql.local to match)
  base/                 <- immutable rootfs (3.5GB used)
  layers/
    upper/              <- overlay changes (mutable)
    work/               <- overlayfs workdir
    snapshots/          <- saved checkpoints
  merged/               <- unified view (chroot target)
  repo/                 <- local RPM repo
  sources/              <- bind-mount of project SOURCES/

/srv/glats/nginx/repo/  <- production repo (served by nginx)
```

---

## 10. Troubleshooting

### Disk auto-mounted at /run/media/

If udisks2 auto-mounts the disk at `/run/media/$USER/maquilinux/`:

```bash
# Check where it's mounted
mount | grep sdd

# Unmount from auto-location
sudo umount /run/media/$USER/maquilinux

# Mount at the correct development location
sudo mount /dev/sdd1 /mnt/maquilinux
```

To prevent auto-mounting, add to `/etc/udev/rules.d/` or use the
`noauto` mount option in NixOS configuration.

### Disk not mounted

```bash
sudo mount /dev/sdd1 /mnt/maquilinux
# or by label:
sudo mount /dev/disk/by-label/maquilinux /mnt/maquilinux
```

### Overlay mount fails

```bash
# Check if the kernel module is loaded
lsmod | grep overlay
# If not:
sudo modprobe overlay
```

### ACME certificate issues

```bash
# Check wildcard cert status
sudo systemctl status acme-glats.org
sudo journalctl -u acme-glats.org -n 20

# Force renewal
sudo rm -rf /var/lib/acme/glats.org/
sudo systemctl restart acme-glats.org
```

### Chroot virtual filesystems stuck

If a chroot session was interrupted (crash, kill), unmount manually:

```bash
sudo umount /mnt/maquilinux/merged/dev/pts 2>/dev/null
sudo umount /mnt/maquilinux/merged/dev/shm 2>/dev/null
sudo umount /mnt/maquilinux/merged/dev 2>/dev/null
sudo umount /mnt/maquilinux/merged/sys 2>/dev/null
sudo umount /mnt/maquilinux/merged/proc 2>/dev/null
sudo umount /mnt/maquilinux/merged/run 2>/dev/null
sudo umount /mnt/maquilinux/merged/mnt/repo 2>/dev/null
sudo umount /mnt/maquilinux/merged 2>/dev/null
```

### nix develop fails

```bash
# Ensure flakes are enabled
nix --extra-experimental-features 'nix-command flakes' develop
```

### RPM build fails inside chroot

Check the build log:

```bash
mql chroot --exec "cat /sources/maquilinux/logs/mlfs/<package>.log"
```

Common causes:
- Missing build dependency (install it first).
- Source tarball not in `/sources/` (check `SOURCES/` bind-mount).
- Spec macro error (validate with `rpmspec -P SPECS/<name>.spec`).

### `sudo` loses PATH inside `nix develop`

Running `sudo mql release iso` or `sudo mql test vm` from inside `nix develop`
fails with `xorriso: command not found` because `sudo` resets PATH and drops
Nix store paths.

**Fix:** Use `sudo -E` to preserve environment, or run `mql` directly (it uses `sudo` internally when needed):

```bash
# For chroot operations (preferred):
./scripts/run-in-chroot.sh <command>

# For release operations that need root:
sudo -E mql release iso
```

### RPM install and dependency resolution

Maqui Linux uses DNF5 for package management with proper dependency resolution.
All specs should declare proper `Provides:` for libraries they install.

**Install packages:**

```bash
mql chroot --exec "dnf install /mnt/repo/<package>-*.rpm"
```

**Build packages with proper dependencies:**

Ensure your specs have correct `BuildRequires:` and `Requires:` for proper
resolution. For libraries, add explicit `Provides:`:

```spec
Provides: libexample.so.1()(64bit)
```
