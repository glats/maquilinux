# Maqui Linux Development System Plan

> **Status: IMPLEMENTED (2026-04-02)** — All phases complete. This document
> describes the architecture as built. Sections 15.1–15.4 have been achieved.

Comprehensive plan for the development tooling, build system, testing
infrastructure, and release pipeline of Maqui Linux.

**Date:** March 2026
**Status:** Active

---

## 1. Overview

### 1.1 What is Maqui Linux

| Property         | Value                                          |
| ---------------- | ---------------------------------------------- |
| Name             | Maqui Linux                                    |
| Version          | 26.4 (os-release and dnf releasever)           |
| Base             | Linux From Scratch (MLFS multilib book)        |
| Init system      | OpenRC 0.63                                    |
| Package manager  | DNF5 5.3.0.0 + RPM 6.0.1                      |
| Kernel           | 6.17.9 (near-monolithic, 8 loadable modules)  |
| Toolchain        | GCC 15.2.0, glibc 2.42, Python 3.14, Perl 5.42 |
| Multiarch        | Debian-style (`/usr/lib/x86_64-linux-gnu/`, `/usr/lib/i386-linux-gnu/`) |
| Architecture     | x86_64 with i686 multilib                      |
| Package tag      | `m264` (maquilinux 26.4)                       |
| Spec count       | 109+ RPM spec files (Gen3 template)            |
| Repo URL         | `https://repo.glats.org/linux/maquilinux/$releasever/$basearch/stable` |

### 1.2 Design Principles

1. **Nix is optional, not required.** The entire build system is pure bash.
   `flake.nix` is a convenience layer (~25 lines) that provides tools via
   `nix develop`. If Nix is removed, install the same tools with `dnf` or
   `apt` and everything works identically.

2. **Portable.** The `mql` CLI and all scripts work on any Linux distribution
   with bash >= 5 and the required tools installed.

3. **Overlay-first development.** The rootfs base is immutable. All changes
   happen on an overlayfs layer that can be reset, snapshotted, or persisted.

4. **Per-package repos in the future.** Each spec will eventually be its own
   git repository (dist-git model). The current flat `SPECS/` + `SOURCES/`
   layout is a stepping stone.

---

## 2. Architecture

```
                         +----------------------------------+
                         |          nix develop              |
                         |   (rpm, createrepo_c, xorriso,   |
                         |    qemu, squashfs, dracut-ng)     |
                         +----------------------------------+
                                        |
              +-------------------------+-------------------------+
              |                         |                         |
    +---------v----------+   +----------v--------+   +------------v-----------+
    |   mql chroot       |   |  mql build        |   |   mql test             |
    |                    |   |                    |   |                        |
    |  overlayfs layers: |   |  build-spec.sh     |   |  QEMU VM boot         |
    |   base (immutable) |   |  install-spec.sh   |   |  smoke tests          |
    |   upper (mutable)  |   |  auto-repo update  |   |  rc-status check      |
    |   snapshots        |   |  createrepo_c      |   |  package verification |
    +--------------------+   +----------+---------+   +------------+----------+
                                        |                          |
                             +----------v--------------------------v----------+
                             |                mql release                      |
                             |                                                |
                             |  rootfs (dnf5 --installroot)                   |
                             |  -> cleanup-lfs-remnants.sh                    |
                             |  -> dracut-ng (initramfs with dmsquash-live)   |
                             |  -> mksquashfs                                 |
                             |  -> xorriso + grub + kernel + initramfs        |
                             |  -> maquilinux-26.4-x86_64.iso                 |
                             +------------------------------------------------+
```

---

## 3. Repository Structure

```
Work/maquilinux/
|
+-- mql                          # CLI (bash, executable, zero Nix deps)
+-- flake.nix                    # Optional: devShell for Nix users
+-- AGENTS.md                    # OpenCode context for AI-assisted dev
+-- .gitignore
|
+-- SPECS/                       # 109+ RPM spec files (Gen3 template)
+-- SOURCES/                     # Source tarballs + patches
+-- BUILD/                       # (gitignored) rpmbuild workspace
+-- BUILDROOT/                   # (gitignored) rpmbuild staging
+-- RPMS/                        # (gitignored) built RPMs
+-- SRPMS/                       # (gitignored) source RPMs
|
+-- lib/                         # CLI library functions (bash)
|   +-- common.sh                # Colors, logging, dep validation
|   +-- chroot.sh                # Overlay mount, chroot, unmount
|   +-- repo.sh                  # createrepo_c, sync to /srv/
|   +-- build.sh                 # Build wrapper + auto-repo-update
|   +-- vm.sh                    # QEMU testing
|   +-- iso.sh                   # ISO generation pipeline
|
+-- scripts/                     # Existing build scripts (reorganized)
|   +-- build-spec.sh            # rpmbuild wrapper with multiarch
|   +-- install-spec.sh          # RPM installer with auto-build
|   +-- mlfs-runner.sh           # Full build orchestrator (890 lines)
|   +-- enter-chroot.sh          # Legacy chroot entry
|   +-- umount-chroot.sh         # Legacy chroot cleanup
|   +-- backup-rootfs.sh         # Rootfs backup
|   +-- sync-loop.sh             # Continuous rsync
|
+-- tools/                       # Maintenance tools (existing)
|   +-- cleanup-lfs-remnants.sh  # Remove LFS vestiges
|   +-- create-clean-rootfs.sh   # Generate rootfs from RPMs
|   +-- verify-independence.sh   # Verify no /tools deps
|   +-- download-sources.py      # Download sources from YAML
|   +-- migrate-to-packages.py   # Migrate to per-package layout
|
+-- release/                     # Release assets
|   +-- grub.cfg                 # GRUB config for ISO
|   +-- dracut/                  # dracut-ng modules and config
|   |   +-- maquilinux.conf      # dracut-ng config for live ISO
|   |   +-- 90maquilinux-live/   # Custom dracut-ng module (if needed)
|   +-- branding/
|       +-- os-release           # Template for releases
|       +-- issue                # Login prompt branding
|
+-- docs/                        # Documentation (existing + this file)
+-- .github/workflows/           # CI/CD (existing)
+-- .gitlab-ci.yml               # CI/CD (existing)
```

---

## 4. Overlay-Based Development Chroot

Instead of a mutable rootfs that must be re-extracted if broken, the
development environment uses overlayfs for fast, reversible iteration.

### 4.1 Partition Layout (`/dev/sdd1` mounted at `/mnt/maquilinux`)

```
/mnt/maquilinux/                  <- ext4, 119.2 GB
+-- base/                         <- Rootfs IMMUTABLE (extracted from tarball)
|   +-- bin -> usr/bin
|   +-- etc/
|   +-- usr/
|   +-- ...
+-- layers/
|   +-- upper/                    <- Current changes (overlay upperdir)
|   +-- work/                     <- Overlay workdir (required by overlayfs)
|   +-- snapshots/                <- Named snapshots
|       +-- 2026-03-24-initial/
|       +-- 2026-03-25-post-gcc/
+-- merged/                       <- Unified view (base + upper) -> chroot here
+-- repo/                         <- Local RPM repo (bind-mounted as /mnt/repo)
+-- sources/                      <- (optional) bind-mount of SOURCES/
```

### 4.2 How It Works

**Mount overlay:**

```bash
mount -t overlay overlay \
  -o lowerdir=/mnt/maquilinux/base,\
     upperdir=/mnt/maquilinux/layers/upper,\
     workdir=/mnt/maquilinux/layers/work \
  /mnt/maquilinux/merged
```

**Chroot sees:**

- `/` is the merged view (base + changes)
- `/sources` is a bind-mount of `SOURCES/` from the repo
- `/mnt/repo` is a bind-mount of the local RPM repo

**Reset (discard all changes):**

```bash
rm -rf /mnt/maquilinux/layers/upper/*
# Next chroot starts clean from base
```

**Snapshot (save current state):**

```bash
cp -a /mnt/maquilinux/layers/upper/ \
  /mnt/maquilinux/layers/snapshots/$(date +%F)-description/
```

**Promote (merge overlay into new base):**

```bash
mql chroot --promote
# Equivalent to:
#   rsync -a /mnt/maquilinux/layers/upper/ /mnt/maquilinux/base/
#   rm -rf /mnt/maquilinux/layers/upper/*
```

Use this when the overlay contains changes you want to keep
permanently (e.g., after installing a batch of updated packages).

**Regenerate base from RPMs (cleanest):**

```bash
mql release rootfs --target /mnt/maquilinux/base
```

Produces a fresh base from the published RPMs, without any manual
changes or artifacts. Preferred for formal releases.

### 4.3 Advantages

- **Never lose the base:** a broken `rpm -e glibc` is a 2-second reset,
  not an 800 MB re-extraction.
- **Visual diff:** `ls layers/upper/` shows exactly what changed.
- **Named snapshots:** checkpoint before risky operations.
- **Fast:** overlayfs is kernel-native, zero copy overhead.

---

## 5. The `mql` CLI

A single bash script that dispatches to library functions. No Nix dependency.

### 5.1 Commands

```
mql chroot                    Enter the overlay chroot
mql chroot --reset            Discard overlay, return to base
mql chroot --persist <name>   Save snapshot of current overlay
mql chroot --promote          Merge overlay into base (new base)
mql chroot --exec "<cmd>"     Run a command in chroot without entering

mql build <spec>              Build an RPM (wraps build-spec.sh)
mql build <spec> --both       Build 64+32 bit
mql build --all               Build all specs (wraps mlfs-runner.sh)
mql install <spec>            Install RPM into the chroot

mql repo update               Run createrepo_c on local RPMS/
mql repo list                 List packages in local repo
mql repo sync                 rsync to /srv/glats/nginx/repo/

mql test vm                   Boot Maqui Linux in QEMU (serial console)
mql test smoke                Run smoke tests inside chroot
mql test verify               Run verify-independence.sh

mql release rootfs             Generate clean rootfs from RPMs
mql release rootfs --target <path>  Generate rootfs into specific dir
mql release tarball           Package rootfs as .tar.xz
mql release iso               Generate bootable live ISO

mql status                    Show overview (modified specs, pending
                              RPMs, overlay size, repo status)
```

### 5.2 Dependency Validation

`mql` only checks for tools needed by the invoked subcommand:

| Tool                  | Required for        | Nix devShell    | Fedora/RHEL       | Debian/Ubuntu       |
| --------------------- | ------------------- | --------------- | ------------------ | ------------------- |
| bash >= 5             | everything          | included        | included           | included            |
| rpm, rpmbuild         | build, install      | `rpm`           | `rpm-build`        | `rpm`               |
| createrepo_c          | repo                | `createrepo_c`  | `createrepo_c`     | `createrepo-c`      |
| xorriso               | release iso         | `libisoburn`    | `xorriso`          | `xorriso`           |
| mksquashfs            | release iso         | `squashfsTools`  | `squashfs-tools`   | `squashfs-tools`    |
| dracut-ng             | release iso         | `dracut`        | `dracut`           | `dracut-core`       |
| qemu-system-x86_64    | test vm             | `qemu`          | `qemu-system-x86`  | `qemu-system-x86`   |
| mount (overlay)       | chroot              | included        | included           | included            |

---

## 6. Nix DevShell (Optional)

The `flake.nix` provides all tools in a single command:

```bash
cd ~/Work/maquilinux
nix develop
# All tools available, mql in PATH
```

The flake is minimal (~30 lines):

```nix
{
  description = "Maqui Linux development environment";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          rpm
          createrepo_c
          libisoburn
          cdrtools
          squashfsTools
          dracut  # dracut-ng in Nixpkgs
          qemu
          file
          tree
        ];
        shellHook = ''
          export PATH="$PWD:$PATH"
        '';
      };
    };
}
```

If Nix is removed in the future, install the same packages with the
distribution's package manager. The `mql` CLI works identically.

---

## 7. Build and Repo Pipeline

### 7.1 Build Flow

```
SPECS/*.spec
  |  mql build <spec>
  |  (rpmbuild inside chroot via build-spec.sh)
  v
RPMS/{x86_64,i686,noarch}/*.rpm
  |  mql repo update
  |  (createrepo_c generates metadata)
  v
Local repo with repodata/
  |  mql repo sync
  |  (rsync to /srv/glats/nginx/repo/)
  v
repo.glats.org
  |  nginx serves over HTTPS (wildcard cert via dns-cloudflare)
  v
dnf install / dnf update (from installed systems)
```

### 7.2 Local Repo

After each `mql build`, RPMs are placed in `RPMS/`. `mql repo update`
runs `createrepo_c` to generate metadata. Inside the chroot, a local
repo config points to this directory:

```ini
# /etc/yum.repos.d/local.repo (inside chroot)
[maquilinux-local]
name=Maquilinux Local Development
baseurl=file:///mnt/repo
enabled=1
gpgcheck=0
priority=1
```

### 7.3 Production Repo

`mql repo sync` copies RPMs and repodata to
`/srv/glats/nginx/repo/maquilinux/26.4/` which nginx serves at
`https://repo.glats.org/linux/maquilinux/26.4/$basearch/stable/`.

The NixOS nginx config for `repo.glats.org`:

```nix
"repo.glats.org" = {
  useACMEHost = "glats.org";
  forceSSL = true;
  locations."/linux/" = {
    alias = "/srv/glats/nginx/repo/";
    extraConfig = "autoindex on;";
  };
  locations."/" = {
    return = "301 /linux/";
  };
};
```

---

## 8. Testing

### 8.1 QEMU VM Boot Test

```bash
mql test vm
```

Boots the rootfs in QEMU using the distribution's own kernel:

```bash
qemu-system-x86_64 \
  -kernel /mnt/maquilinux/base/boot/vmlinuz-6.17.9 \
  -append "root=/dev/sda1 console=ttyS0 init=/sbin/openrc-init" \
  -drive file=maquilinux.qcow2,format=qcow2 \
  -nographic \
  -m 2G \
  -enable-kvm
```

### 8.2 Smoke Tests

```bash
mql test smoke
```

Automated checks inside the chroot or VM:

1. System boots to login prompt
2. `rc-status` shows running services
3. `rpm -qa` returns package list
4. `dnf repolist` shows configured repos
5. `gcc --version` returns 15.2.0
6. Compile and run a hello.c program
7. `openssl version` returns 3.6.0
8. `python3 --version` returns 3.14.0

### 8.3 Independence Verification

```bash
mql test verify
```

Runs `tools/verify-independence.sh` to confirm the system has no
remaining dependencies on the LFS temporary toolchain.

---

## 9. Initramfs with dracut-ng

### 9.1 Why dracut-ng

dracut-ng is the actively maintained fork of the original dracut project
(which was last released as dracut 059 in December 2022). dracut-ng is
used by Fedora, RHEL, openSUSE, Arch, Void, Alpine, Gentoo, and Ubuntu.
It provides the `dmsquash-live` module which handles exactly what a live
ISO needs: mount squashfs, create overlay, switch_root.

Using dracut-ng instead of a custom init script means:
- Standard, well-tested live boot logic
- Hardware detection and module loading out of the box
- Future extensibility (network boot, installer hooks, encryption)
- An RPM spec for dracut becomes a real package in the distribution
- OpenRC is explicitly tested (Void, Alpine, Gentoo use it with OpenRC)

See `docs/DECISIONS.md` for the full evaluation of alternatives.

### 9.2 dracut-ng as an RPM

dracut-ng is built and installed as a package in Maqui Linux via
`SPECS/dracut.spec` (the RPM package name remains `dracut`):

- Version 110 (latest release, February 2026)
- `--disable-dracut-cpio`: skip the optional Rust-based cpio (deferred
  until Maqui Linux bootstraps its own Rust toolchain)
- `--disable-documentation`: no asciidoctor build dependency
- OpenRC compatibility: systemd modules omitted via config
- Requires GNU cpio (see `SPECS/cpio.spec`, patched for GCC 15 / glibc 2.4x)
- Requires libkmod >= 23

Configure:

```bash
./configure \
    --prefix=/usr \
    --sysconfdir=/etc \
    --libdir=/usr/lib \
    --disable-dracut-cpio \
    --disable-documentation
```

### 9.3 Generating the Initramfs

For a live ISO:

```bash
dracut --no-hostonly \
  --add "dmsquash-live livenet" \
  --omit "systemd systemd-initrd" \
  --kver 6.17.9 \
  --force \
  initramfs-6.17.9.img
```

Key flags:
- `--no-hostonly`: include all drivers, not just for the build host
- `--add "dmsquash-live"`: the squashfs + overlay live boot module
- `--omit "systemd"`: Maqui Linux uses OpenRC, not systemd
- `--kver`: target the Maqui Linux kernel version

The resulting initramfs handles:
1. Finding the boot media (USB/DVD)
2. Mounting the squashfs from `/live/filesystem.squashfs`
3. Creating a tmpfs overlay for writable layer
4. Merging via overlayfs
5. `switch_root` to the live system
6. OpenRC takes over

### 9.4 dracut-ng for Installed Systems

Once dracut is packaged, it also serves installed systems:

```bash
dracut --kver 6.17.9 /boot/initramfs-6.17.9.img
```

This generates an initramfs for a disk-installed Maqui Linux system,
handling hardware detection, filesystem mounting, etc.

---

## 10. ISO Live Release Pipeline

### 10.1 Overview

```bash
mql release iso
```

Produces a bootable ISO that works on both BIOS and UEFI systems.

### 10.2 Step-by-Step Pipeline

**Step 1: Generate clean rootfs from RPMs**

```bash
tools/create-clean-rootfs.sh /tmp/maquilinux-rootfs --full
```

Uses `dnf5 --installroot` to install packages from the local repo into
a fresh directory. No LFS vestiges, no build artifacts.

**Step 2: Clean up**

```bash
chroot /tmp/maquilinux-rootfs tools/cleanup-lfs-remnants.sh --production
```

Removes any remaining LFS artifacts, caches, temp files.

**Step 3: Configure the rootfs for live boot**

```
/etc/fstab           -> tmpfs entries (live mode, no disk references)
/etc/hostname        -> maquilinux
/etc/os-release      -> Maqui Linux 26.4 (from release/branding/)
/etc/resolv.conf     -> nameserver 8.8.8.8 (fallback)
/etc/yum.repos.d/    -> maquilinux.repo (repo.glats.org)
CA certificates      -> ca-certificates bundle installed
/etc/conf.d/hostname -> maquilinux
/etc/conf.d/network  -> DHCP or static config
```

**Step 4: Generate initramfs with dracut-ng**

```bash
chroot /tmp/maquilinux-rootfs \
  dracut --no-hostonly \
    --add "dmsquash-live" \
    --omit "systemd systemd-initrd" \
    --kver 6.17.9 \
    --force \
    /boot/initramfs-6.17.9.img
```

**Step 5: Compress rootfs into squashfs**

```bash
mksquashfs /tmp/maquilinux-rootfs filesystem.squashfs \
  -comp zstd -Xcompression-level 19 \
  -e boot    # Exclude /boot (kernel/initramfs go separately)
```

**Step 6: Assemble ISO structure**

```
iso/
+-- boot/
|   +-- vmlinuz-6.17.9          <- Kernel
|   +-- initramfs-6.17.9.img    <- dracut-ng initramfs
|   +-- grub/
|       +-- grub.cfg            <- Boot menu
|       +-- fonts/
|           +-- unicode.pf2
+-- LiveOS/
|   +-- squashfs.img            <- Compressed rootfs
+-- EFI/
    +-- BOOT/
        +-- BOOTX64.EFI         <- GRUB EFI binary
```

Note: dracut-ng `dmsquash-live` expects the squashfs at
`/LiveOS/squashfs.img` by default (matching Fedora convention).

**Step 7: Generate ISO with xorriso**

```bash
xorriso -as mkisofs \
  -iso-level 3 \
  -o maquilinux-26.4-x86_64.iso \
  -full-iso9660-filenames \
  -volid "MAQUILINUX_264" \
  --grub2-mbr /usr/lib/grub/i386-pc/boot_hybrid.img \
  -partition_offset 16 \
  --mbr-force-bootable \
  -append_partition 2 0xef efi.img \
  -appended_part_as_gpt \
  -eltorito-catalog boot/boot.cat \
  -eltorito-boot boot/grub/i386-pc/eltorito.img \
    -no-emul-boot -boot-load-size 4 -boot-info-table --grub2-boot-info \
  -eltorito-alt-boot \
  -e '--interval:appended_partition_2:all::' \
    -no-emul-boot \
  iso/
```

**Step 8: Verify**

```bash
# Test in QEMU
qemu-system-x86_64 -cdrom maquilinux-26.4-x86_64.iso -m 2G -enable-kvm

# Write to USB
dd if=maquilinux-26.4-x86_64.iso of=/dev/sdX bs=4M status=progress
```

### 10.3 ISO Boot Sequence

```
BIOS/UEFI
  -> GRUB (from ISO)
    -> vmlinuz-6.17.9 + initramfs-6.17.9.img
      -> dracut-ng dmsquash-live module:
        1. Find boot media (scan for MAQUILINUX_264 label)
        2. Mount /LiveOS/squashfs.img as /lower
        3. Create tmpfs as /upper (writable, in RAM)
        4. Mount overlayfs (lower + upper)
        5. switch_root to merged system
      -> OpenRC starts
        -> sysinit: cgroups, devfs, dmesg, sysfs
        -> boot: fsck, hostname, hwclock, keymaps, network, ...
        -> default: agetty.tty1-tty6, local, netmount
      -> Login prompt
```

---

## 11. RPM Repository

### 11.1 Repository Structure

```
repo.glats.org/linux/maquilinux/
+-- 26.4/                          <- $releasever
    +-- x86_64/
    |   +-- stable/                <- Production channel
    |   |   +-- Packages/          <- .rpm files
    |   |   +-- repodata/          <- createrepo_c metadata
    |   +-- testing/               <- Pre-release channel
    |       +-- Packages/
    |       +-- repodata/
    +-- i686/
    |   +-- stable/
    |   +-- testing/
    +-- SRPMS/
        +-- ...
```

### 11.2 Client Configuration

On installed Maqui Linux systems:

```ini
# /etc/yum.repos.d/maquilinux.repo
[maquilinux]
name=Maquilinux $releasever - $basearch
baseurl=https://repo.glats.org/linux/maquilinux/$releasever/$basearch/stable
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-maquilinux
sslverify=1
```

### 11.3 GPG Signing (Future)

```bash
# Generate key pair
gpg --gen-key

# Export public key
gpg --export --armor > RPM-GPG-KEY-maquilinux

# Sign RPMs
rpmsign --addsign *.rpm

# Import key in target system
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-maquilinux
```

### 11.4 Hosting (NixOS)

`repo.glats.org` is served by nginx on NixOS with a wildcard Let's
Encrypt certificate via DNS-01 challenge (Cloudflare). The config is in
`~/.nixos/modules/nginx.nix`.

---

## 12. Known Issues in the Rootfs

> **All items in this table have been resolved as of 2026-04-02.**

Issues detected in the current rootfs that must be resolved before a
release:

| #  | Issue                          | Severity | Resolution                                    |
| -- | ------------------------------ | -------- | --------------------------------------------- |
| 1  | CA certificates empty          | Critical | Install ca-certificates bundle                |
| 2  | /etc/fstab empty               | Critical | Configure for target (live: tmpfs, disk: UUID) |
| 3  | Hostname not configured        | Medium   | Set in /etc/hostname and /etc/conf.d/hostname |
| 4  | Version mismatch 25.4 vs 26.4  | Medium   | Align os-release with dnf releasever          |
| 5  | Broken udev rule (LFS path)    | Low      | Fix or remove /etc/udev/rules.d/55-maquilinux.rules |
| 6  | Missing /etc/profile           | Medium   | Create with standard PATH and umask           |
| 7  | Missing /etc/shells            | Medium   | Create listing /bin/bash, /bin/sh             |
| 8  | Missing /etc/inputrc           | Low      | Create with readline defaults                 |
| 9  | Missing /etc/shadow            | Medium   | Run pwconv to generate from passwd            |
| 10 | Binaries not stripped           | Low      | Strip in spec %install or post-build          |
| 11 | elfutils test artifacts         | Low      | Clean /var/tmp/                               |
| 12 | No DHCP client                  | Medium   | Package and install dhcpcd or dhclient        |
| 13 | No initramfs                    | Critical | Build dracut-ng as RPM, generate initramfs    |
| 14 | No dracut-ng package            | Critical | Update SPECS/dracut.spec to dracut-ng 110     |
| 15 | systemd timer units from dnf5   | Low      | Remove or ignore (inert without systemd)      |

---

## 13. Implementation Phases

### Phase 0: Reorganize Repository

Move existing scripts into `scripts/` directory. Create `.gitignore`.

- Move `build-spec.sh`, `install-spec.sh`, `mlfs-runner.sh`,
  `enter-chroot.sh`, `umount-chroot.sh`, `backup-temp-system.sh`,
  `sync-maquilinux-loop.sh` into `scripts/`.
- Create `.gitignore` (BUILD/, BUILDROOT/, RPMS/, SRPMS/, *.rpm, logs/).

**Depends on:** nothing.
**Nix required:** no.

### Phase 1: `mql` CLI + Core Libraries

Create the unified CLI and the chroot/overlay library.

- `mql` dispatcher script (bash).
- `lib/common.sh` with colors, logging, dependency checks.
- `lib/chroot.sh` with overlay mount/unmount, chroot entry, reset,
  snapshot, persist, and exec.

**Depends on:** Phase 0.
**Nix required:** no.

### Phase 2: Nix DevShell + AGENTS.md

Create the optional Nix integration and OpenCode context.

- `flake.nix` with devShell providing all tools.
- `AGENTS.md` describing the project, rootfs location, conventions,
  and how to use `mql`.

**Depends on:** Phase 1.
**Nix required:** yes (but optional for the project).

### Phase 3: Restructure Partition

Migrate the rootfs on `/dev/sdd1` from flat layout to overlay structure.

- Move current rootfs content into `base/`.
- Create `layers/{upper,work,snapshots}/`, `merged/`, `repo/`.

**Depends on:** Phase 1.
**Nix required:** no.

### Phase 4: Local Repo Integration

Set up createrepo_c for the local RPM repository.

- `lib/repo.sh` with update (createrepo_c) and sync (rsync to /srv/).
- Create `local.repo` inside the chroot pointing to `/mnt/repo`.
- Bind-mount `repo/` into the chroot at `/mnt/repo`.

**Depends on:** Phase 3.
**Nix required:** no.

### Phase 5: Build Wrapper

Wrap existing build scripts with `mql build` interface.

- `lib/build.sh` dispatching to `scripts/build-spec.sh` and
  `scripts/install-spec.sh`.
- Auto-run `mql repo update` after successful builds.

**Depends on:** Phase 4.
**Nix required:** no.

### Phase 6: Rootfs Critical Fixes

Fix all critical issues listed in section 12.

- Install CA certificates.
- Configure fstab, hostname, os-release.
- Create missing files (profile, shells, inputrc, shadow).
- Fix udev rule.
- Clean test artifacts.

**Depends on:** Phase 1.
**Nix required:** no.

### Phase 7: dracut-ng Package

Build the dracut-ng RPM spec (replaces original dracut 059).

- `SPECS/dracut.spec` updated to dracut-ng 110 (active fork).
- `--disable-dracut-cpio` (no Rust), `--disable-documentation` (no asciidoctor).
- Requires GNU cpio 2.15 (`SPECS/cpio.spec`, patched for GCC 15 / glibc 2.4x).
- Include `dmsquash-live`, `squash`, and `overlay` modules.
- Build and install in the chroot.
- Test initramfs generation.

**Depends on:** Phase 6.
**Nix required:** no.

### Phase 8: GPG Signing

Set up RPM signing infrastructure.

- Generate GPG key pair.
- Configure `rpmsign` macros.
- Sign all existing RPMs.
- Update repo config to `gpgcheck=1`.

**Depends on:** Phase 4.
**Nix required:** no.

### Phase 9: QEMU VM Testing

Enable boot testing in QEMU.

- `lib/vm.sh` with VM boot, serial console, and automated smoke tests.
- Generate qcow2 image from rootfs.
- Smoke test suite.

**Depends on:** Phase 6.
**Nix required:** no.

### Phase 10: DHCP Client

Package a DHCP client for automatic networking.

- Write `SPECS/dhcpcd.spec` (lightweight DHCP client).
- Create OpenRC init script.
- Enable in default runlevel.

**Depends on:** Phase 6.
**Nix required:** no.

### Phase 11: ISO Pipeline

Implement the full ISO generation.

- `lib/iso.sh` orchestrating all steps (rootfs, dracut-ng, squashfs, xorriso).
- `release/grub.cfg` with boot menu.
- `release/dracut/maquilinux.conf` with dracut-ng options.
- `release/branding/` with os-release and issue files.

**Depends on:** Phases 6, 7, 10.
**Nix required:** no.

### Phase 12: CI/CD Integration

Connect the existing CI/CD pipelines to the new tooling.

- Update `.github/workflows/` to use `mql` commands.
- Builder container image with all tools.
- Automated ISO builds on release tags.

**Depends on:** Phase 11.
**Nix required:** no.

### Dependency Graph

```
Phase 0
  +-> Phase 1
  |     +-> Phase 2 (flake + AGENTS.md)
  |     +-> Phase 3 (overlay partition)
  |     |     +-> Phase 4 (local repo)
  |     |           +-> Phase 5 (build wrapper)
  |     |           +-> Phase 8 (GPG signing)
  |     +-> Phase 6 (rootfs fixes)
  |           +-> Phase 7 (dracut)
  |           +-> Phase 9 (QEMU testing)
  |           +-> Phase 10 (DHCP client)
  |           +-> Phase 11 (ISO pipeline) <- also needs 7 and 10
  |                 +-> Phase 12 (CI/CD)
```

### Critical Path to First ISO

```
Phase 0 -> 1 -> 3 -> 4 -> 6 -> 7 -> 10 -> 11
```

---

## 14. Rootfs and Tarball Lifecycle

The rootfs tarball is a release artifact, not a source of truth. The
RPM repository is the source of truth. The tarball is derived from it.

### 14.1 How the Rootfs is Generated

**Current phase (bootstrapping):** The initial tarball was created
manually from the LFS build. It serves as the starting `base/` for
the overlay development environment.

**Target phase (self-hosting):** The rootfs is generated entirely
from RPMs:

```bash
mql release rootfs
# Internally:
#   1. dnf5 --installroot=/tmp/rootfs --repo=maquilinux install @base
#   2. cleanup-lfs-remnants.sh --production
#   3. Configure (fstab, hostname, CA certs, repo config)
#   4. tar cJf maquilinux-26.4-rootfs.tar.xz -C /tmp/rootfs .
```

Same RPMs always produce the same rootfs. The tarball is reproducible.

### 14.2 When to Regenerate

The tarball and overlay base do **not** need to be regenerated with
every change. The workflow is:

| Event                        | Action                                    |
| ---------------------------- | ----------------------------------------- |
| Spec edited/built            | `mql build` + `mql install` in chroot     |
| Multiple packages updated    | `dnf update` inside chroot                |
| Formal release               | `mql release rootfs` + `mql release iso`  |
| New developer onboarding     | Download tarball or `mql release rootfs`   |
| Overlay base refresh         | `mql chroot --promote` or regenerate from RPMs |

Day-to-day development does not regenerate the tarball. Packages are
installed directly in the chroot via `mql install` or `dnf install`.
The tarball is regenerated for formal releases and for publishing.

### 14.3 Updating the Overlay Base

Two methods to refresh the base layer on the development partition:

**Method 1: Promote the current overlay**

```bash
mql chroot --persist "pre-promote"   # Safety snapshot
mql chroot --promote                  # Merge upper -> base, clear upper
```

This makes the current state (base + changes) the new base.

**Method 2: Regenerate from RPMs (cleaner)**

```bash
mql release rootfs --target /mnt/maquilinux/base
```

This produces a clean base from the published RPMs, without any
manual changes or artifacts.

### 14.4 Publishing the Tarball

The tarball is published as a release artifact alongside the ISO:

| Destination                               | Audience    | Method                                   |
| ----------------------------------------- | ----------- | ---------------------------------------- |
| `repo.glats.org/linux/maquilinux/images/` | Developers  | `mql repo sync` (rsync alongside RPMs)   |
| GitHub Releases                           | Public      | `gh release create v26.4 *.tar.xz *.iso` |
| Inside the ISO                            | Installer   | Included for disk installation            |

The tarball is **not** stored in git (788 MB+). It is generated as
a CI/CD artifact or manually with `mql release tarball`.

### 14.5 Complete Release Artifact Flow

```
Specs (source of truth, in git)
  -> mql build            (RPMs)
  -> mql repo update      (metadata)
  -> mql repo sync        (publish to repo.glats.org)
  -> mql release rootfs   (generate rootfs from RPMs)
  -> mql release tarball  (package rootfs as .tar.xz)
  -> mql release iso      (package rootfs as bootable ISO)
  -> publish tarball + ISO to repo.glats.org/images/ and GitHub Releases
```

All three release artifacts (rootfs dir, tarball, ISO) are derived
from the same set of RPMs. They are not independent -- changing a
package and rebuilding produces updated versions of all three.

---

## 15. Self-Hosting: Maqui Linux Builds Maqui Linux

The long-term objective was that Maqui Linux is fully **self-hosting**:
it can rebuild itself and produce its own ISO without any external
distribution (NixOS, Fedora, Arch, or otherwise).

**✅ ACHIEVED 2026-04-02** — All 7+2 self-hosting packages are built
and installed in the base rootfs.

### 15.1 Previous State ✅ RESOLVED

Previously, the build pipeline relied on a NixOS host for the tools that the
chroot did not yet have:

```
NixOS host (nix develop)
  provided: createrepo_c, xorriso, mksquashfs, dracut, qemu, mtools
                          |
                          v
Maqui Linux chroot (/mnt/maquilinux)
  had: rpmbuild, gcc 15.2, glibc 2.42, python 3.14, grub 2.12
```

RPM builds already happened inside the chroot with the native toolchain.
Nix only provided the release and repo management tools.

### 15.2 Current State ✅ ACHIEVED

```
Maqui Linux (installed or in VM)
  has: everything
                          |
  mql build --all         |
  mql release iso         |
                          v
RPMs -> Repo -> ISO (built entirely by Maqui Linux)
```

### 15.3 Self-Hosting Packages ✅ ALL BUILT AND INSTALLED

The following RPM specs close the self-hosting gap. All are built and
installed in the base rootfs as of 2026-04-02:

| Spec                    | Version    | Needed for                         |
| ----------------------- | ---------- | ---------------------------------- |
| `dracut.spec`           | 110-1      | Initramfs (dracut-ng 110)          |
| `busybox.spec`          | 1.36.1-1   | dracut-ng backend                  |
| `dhcpcd.spec`           | 10.0.6-2   | Live networking                    |
| `createrepo_c.spec`     | 1.2.3-1    | Repo metadata                      |
| `libisoburn.spec`       | 1.5.6-1    | ISO generation (xorriso)           |
| `squashfs-tools.spec`   | 4.6.1-1    | Rootfs compression                 |
| `mtools.spec`           | 4.0.43-2   | EFI image for ISO                  |
| `libburn.spec`          | 1.5.6-1    | libisoburn dependency              |
| `libisofs.spec`         | 1.5.6-1    | libisoburn dependency              |

### 15.4 The Bootstrap Milestone ✅ COMPLETED

```
First ISO  (NixOS assisted)  ->  Boot Maqui Linux
                                   |
                                    dnf install createrepo_c dracut
                                   dnf install libisoburn squashfs-tools
                                   dnf install mtools busybox dhcpcd
                                   |
                                   mql build --all
                                   mql release iso
                                   |
                                   v
                                 Second ISO (self-hosted, zero external deps)
                                 ✅ Achieved 2026-04-02
```

### 15.5 The `flake.nix` Becomes Optional

Once self-hosting is achieved, the `flake.nix` is a convenience for
developers who happen to use NixOS. It is not required for building,
testing, or releasing Maqui Linux. The `mql` CLI is pure bash and works
on any system where the required tools are installed, including Maqui
Linux itself.

### 15.6 Integration with Implementation Phases

The 7 new specs are distributed across existing phases:

| Phase | New specs                                             |
| ----- | ----------------------------------------------------- |
| 7     | `dracut.spec`, `busybox.spec`                         |
| 10    | `dhcpcd.spec`                                         |
| 11    | `createrepo_c.spec`, `libisoburn.spec`, `squashfs-tools.spec`, `mtools.spec` |

No new phases are needed. Self-hosting is a natural consequence of
completing the existing plan through Phase 11.

### 15.7 Updated Critical Path

```
Phase 0 -> 1 -> 3 -> 4 -> 6 -> 7 (dracut-ng, cpio, busybox)
                                |
                                +-> 10 (dhcpcd)
                                |
                                +-> 11 (createrepo_c, libisoburn,
                                |       squashfs-tools, mtools)
                                |
                                +-> First ISO
                                      |
                                      +-> Self-hosting milestone
```

---

## 16. Future Work

### 16.1 Per-Package Git Repositories

Each spec will eventually be its own git repository (dist-git model):

```
github.com/maquilinux/
  +-- rpm-glibc/      (glibc.spec + sources.yaml)
  +-- rpm-gcc/        (gcc.spec + sources.yaml)
  +-- rpm-openrc/     (openrc.spec + sources.yaml)
  +-- ...
```

The `tools/migrate-to-packages.py` script assists with this migration.
The `mql` CLI will be updated to resolve specs from per-package repos
when the migration happens.

### 16.2 Installer

A script or TUI application for installing Maqui Linux to disk from the
live ISO. This would handle partitioning, filesystem creation, rootfs
extraction, GRUB installation, fstab generation, and initial configuration.

### 16.3 Desktop Environment

The current system is a minimal CLI environment. Future releases may
include a desktop environment (Xfce, MATE, or similar) as an optional
package group.

### 16.4 Secure Boot

UEFI Secure Boot support requires signing the kernel, GRUB, and shim
with a trusted key. This is a significant undertaking that depends on
having a stable signing infrastructure.
