# Getting Started with Maqui Linux Development

This guide gets you from zero to a working development environment in under an
hour. It covers two paths — Nix (recommended) and standalone — and explains
the critical gotchas that trip up new developers.

---

## 1. Prerequisites

### 1.1 Hardware

- **Host:** x86_64 Linux (tested on NixOS; works on Fedora, Debian, Arch)
- **Disk:** a dedicated disk or partition — 120 GB minimum, formatted ext4,
  labeled `maquilinux`. The dev disk is `/dev/sdd1` on the primary machine.
- **RAM:** 16 GB recommended (builds are memory-intensive; 8 GB minimum)
- **KVM:** strongly recommended for `mql test vm` (QEMU is slow without it)

### 1.2 Software — Option A: Nix (recommended)

Install Nix with flakes enabled: <https://nixos.org/download>

Everything else (`xorriso`, `mksquashfs`, `qemu`, `createrepo_c`, `dracut`,
`rpm`, `rpmbuild`) is provided automatically by `nix develop`.

### 1.3 Software — Option B: Standalone

Install on your distribution:

**Fedora / RHEL:**
```bash
sudo dnf install bash coreutils util-linux tar rsync git \
  createrepo_c xorriso squashfs-tools mtools \
  qemu-system-x86
```

**Debian / Ubuntu:**
```bash
sudo apt install bash coreutils util-linux tar rsync git \
  createrepo-c xorriso squashfs-tools mtools \
  qemu-system-x86
```

**Arch:**
```bash
sudo pacman -S bash coreutils util-linux tar rsync git \
  libisoburn squashfs-tools mtools qemu-system-x86
yay -S createrepo_c
```

---

## 2. Clone and Configure

### 2.1 Clone the Repository

```bash
git clone https://github.com/glats/maquilinux.git
cd maquilinux
```

Or if you have access to the working directory directly:

```bash
ls ~/Work/maquilinux/
```

### 2.2 Understand the Config System

`mql` uses two config files:

| File | Purpose | In git? |
| ---- | ------- | ------- |
| `mql.conf` | Project defaults (MQL_LFS, MQL_DISK, MQL_RELEASEVER, …) | Yes |
| `mql.local` | Your machine overrides | No (gitignored) |

Environment variables override both files.

The most important variable is **`MQL_LFS`** — where your development disk is
mounted. The default is `/mnt/maquilinux`.

### 2.3 Set MQL_LFS If Your Disk Auto-Mounts Elsewhere

> **⚠️ Critical gotcha:** On NixOS and most desktop environments, `udisks2`
> auto-mounts labeled disks at `/run/media/<user>/<label>`, not at
> `/mnt/maquilinux`. If you don't set `MQL_LFS`, `mql` will look in the wrong
> place and silently fail.

Check where your disk is actually mounted:

```bash
mount | grep sdd
# or:
lsblk
```

If it shows `/run/media/glats/maquilinux` (or similar), create `mql.local`:

```bash
echo "MQL_LFS=/run/media/$USER/maquilinux" >> mql.local
```

Or set it per-session:

```bash
export MQL_LFS=/run/media/$USER/maquilinux
```

### 2.4 Verify the Configuration

```bash
# Nix path:
nix develop --command mql config

# Standalone / already in nix develop:
mql config
```

The output should show `MQL_LFS` pointing to your actual disk mount, `MQL_DISK`
pointing to `/dev/sdd1`, and `MQL_RELEASEVER=26.4`.

---

## 3. Enter the Development Environment

### 3.1 Path A — Nix

```bash
cd ~/Work/maquilinux
nix develop
```

You are now in a shell with all tools available and `mql` in your `PATH`.
Verify:

```bash
which xorriso mksquashfs mql
mql config
```

Now enter the Maqui Linux chroot:

```bash
mql chroot
```

You should see:

```
(maquilinux) root:/#
```

Type `exit` to leave the chroot. All mounts clean up automatically.

> **Note about sudo inside `nix develop`:** If you need to run `mql` with
> `sudo` from inside `nix develop`, use:
> ```bash
> sudo env "PATH=$PATH" mql release iso
> ```
> Plain `sudo mql` resets PATH and loses all Nix-provided tools (`xorriso`,
> `mksquashfs`, `qemu-system-x86_64`). This bites everyone at least once.

### 3.2 Path B — Standalone

Verify all required tools are on your PATH:

```bash
which xorriso mksquashfs qemu-system-x86_64 createrepo_c
```

Add `mql` to your PATH:

```bash
export PATH="$PWD:$PATH"
```

Enter the chroot:

```bash
mql chroot
```

---

## 4. Your First Build

This walks you through building a simple package (`mtools`) from scratch.

### 4.1 Build the RPM

```bash
mql build mtools
```

This runs `rpmbuild` inside the chroot using `SPECS/mtools.spec`. The output
RPM lands in `RPMS/x86_64/`.

### 4.2 Install the RPM (Two Ways)

**Option A — Developer with repo (you just built it):**

```bash
# Install directly from your build
mql chroot --exec "dnf5 install /workspace/RPMS/x86_64/mtools-*.rpm"
```

**Option B — Standalone developer (using pre-built packages):**

```bash
# Enter chroot and install from repo.glats.org
mql chroot
dnf5 install mtools
```

> **DNF5 for package installs.** The Maqui Linux rootfs now uses DNF5 for
> package management with proper dependency resolution. The `--nodeps` workaround
> was only needed during early LFS bootstrap when libraries weren't registered
> in RPM's database. All specs now have proper `Provides:` for dependencies.

**Two development modes:**

| Mode | What you have | Build packages? | Install from |
|------|---------------|-----------------|--------------|
| **Developer** | Repo cloned + disk | `mql build <spec>` | `/workspace/RPMS/` (your builds) |
| **Standalone** | Just rootfs disk | ❌ No (download pre-built) | `repo.glats.org` (dnf5 install) |

### 4.3 Verify the Install

```bash
mql chroot --exec "rpm -qi mtools"
```

You should see the package metadata. That's your first successful build-and-install.

### 4.4 Update the Local Repo

```bash
mql repo update
```

This regenerates the `repodata/` metadata so `dnf` inside the chroot can find
your newly built RPM.

---

## 5. Daily Development Workflow

### 5.1 The Core Loop

```
Edit SPECS/<package>.spec
  → mql build <package>
  → mql chroot --exec "dnf5 install /mnt/repo/<package>-*.rpm"
  → mql chroot --exec "<test command>"
  → mql repo update
  → mql repo sync          (when ready to publish)
```

### 5.2 The Overlay: What Changes, What Persists

Every `mql chroot` mounts an overlay on top of the immutable `base/` layer.
Your changes land in `$MQL_LFS/layers/upper/`. The `base/` layer is never
modified during normal development.

| Command | What it does |
| ------- | ------------ |
| `mql chroot` | Mount overlay, enter chroot; `exit` unmounts everything |
| `mql chroot --exec "<cmd>"` | Run one command and unmount |
| `mql chroot --reset` | Wipe `layers/upper/` — back to pristine base |
| `mql chroot --persist "name"` | Copy `upper/` to `layers/snapshots/YYYY-MM-DD-name/` |
| `mql chroot --promote` | Merge `upper/` into `base/` (see note below) |

> **`mql chroot --promote` requires interactive confirmation** and cannot
> be scripted silently. If you need to promote programmatically, the manual
> equivalent is:
> ```bash
> sudo rsync -a $MQL_LFS/layers/upper/ $MQL_LFS/base/
> sudo rm -rf $MQL_LFS/layers/upper/*
> ```

### 5.3 Useful One-Liners

```bash
# Check what changed in the overlay
ls $MQL_LFS/layers/upper/

# See all installed packages in the chroot
mql chroot --exec "rpm -qa | sort"

# Check service status
mql chroot --exec "rc-status"

# Run a full build of all packages
mql build --all --fast
```

---

## 6. Build and Test the ISO

The live ISO requires tools on PATH (`xorriso`, `mksquashfs`, `qemu`). These
are available automatically inside `nix develop`.

### 6.1 Build the ISO

**Nix path (inside `nix develop`):**

```bash
sudo env "PATH=$PATH" mql release iso
```

**Standalone:**

```bash
mql release iso
```

Output: `maquilinux-26.4-x86_64.iso` in the project root.

The full pipeline:
1. Generates a clean rootfs from RPMs (`dnf5 --installroot`)
2. Removes LFS vestiges
3. Configures for live boot (fstab, hostname, networking, CA certs)
4. Generates initramfs with dracut-ng
5. Compresses rootfs with squashfs (`zstd -19`)
6. Assembles BIOS + UEFI bootable ISO with xorriso

### 6.2 Test the ISO in QEMU

**Nix path:**

```bash
sudo env "PATH=$PATH" mql test vm
```

**Standalone:**

```bash
mql test vm
```

This boots `maquilinux-26.4-x86_64.iso` in QEMU with a serial console.

Inside the VM:
```bash
# Verify networking works
ping -c 3 8.8.8.8

# Verify DNF can reach the production repo
dnf update

# Check installed packages
rpm -qa | wc -l
```

Exit QEMU: press **Ctrl-A X** in the serial console, or close the window.

### 6.3 Run Smoke Tests

```bash
mql test smoke
```

Automated checks: kernel boot, OpenRC services, rpm/dnf, GCC 15.2 compile,
Python 3.14, openssl.

---

## 7. Key Paths Reference

| Path | What |
| ---- | ---- |
| `SPECS/` | 109+ RPM spec files |
| `SOURCES/` | Source tarballs and patches |
| `RPMS/x86_64/` | Built 64-bit RPMs (gitignored) |
| `RPMS/i686/` | Built 32-bit RPMs (gitignored) |
| `lib/` | `mql` CLI library functions (bash) |
| `release/` | ISO configs, dracut config, branding |
| `mql.conf` | Project-wide config defaults |
| `mql.local` | Your machine overrides (gitignored) |
| `flake.nix` | Nix dev shell (optional) |
| `$MQL_LFS/` | Dev disk root (default: `/mnt/maquilinux`) |
| `$MQL_LFS/base/` | Immutable rootfs (overlay lower layer) |
| `$MQL_LFS/layers/upper/` | Current overlay changes |
| `$MQL_LFS/layers/work/` | Overlayfs workdir (required) |
| `$MQL_LFS/layers/snapshots/` | Named snapshots |
| `$MQL_LFS/merged/` | Unified view — the chroot target |
| `$MQL_LFS/repo/` | Local RPM repo (bind-mounted as `/mnt/repo` inside chroot) |
| `/srv/glats/nginx/repo/maquilinux/26.4/x86_64/` | Production repo on the host |
| `https://repo.glats.org/linux/maquilinux/26.4/` | Production repo URL |
| `maquilinux-26.4-x86_64.iso` | Live ISO output (project root) |

**Library paths** (important — NOT `/usr/lib64/` like Fedora/RHEL):
- 64-bit: `/usr/lib/x86_64-linux-gnu/`
- 32-bit: `/usr/lib/i386-linux-gnu/`

---

## 8. Troubleshooting

### Disk mounted at the wrong path

**Symptom:** `mql chroot` says disk not found, or `mql config` shows wrong LFS path.

**Fix:** Set `MQL_LFS` in `mql.local`:

```bash
mount | grep sdd          # Find where it's actually mounted
echo "MQL_LFS=/run/media/$USER/maquilinux" >> mql.local
mql config                # Verify
```

### Overlay stuck / mounts not cleaning up

**Symptom:** "device or resource busy" when unmounting, or `mql chroot` fails
to mount overlay because previous session crashed.

**Fix:** Force-unmount with the lazy flag (safe, waits for last user to exit):

```bash
MQL_LFS=/run/media/$USER/maquilinux    # adjust to your path
sudo umount -l $MQL_LFS/merged/mnt/repo
sudo umount -l $MQL_LFS/merged/dev/shm
sudo umount -l $MQL_LFS/merged/dev/pts
sudo umount -l $MQL_LFS/merged/dev
sudo umount -l $MQL_LFS/merged/run
sudo umount -l $MQL_LFS/merged/sys
sudo umount -l $MQL_LFS/merged/proc
sudo umount -l $MQL_LFS/merged
```

### `sudo` loses PATH inside `nix develop`

**Symptom:** `sudo mql release iso` fails with `xorriso: command not found`
even though `which xorriso` works.

**Cause:** `sudo` resets PATH by default, dropping Nix store paths.

**Fix:** Always use `sudo env "PATH=$PATH"` from inside `nix develop`:

```bash
sudo env "PATH=$PATH" mql release iso
sudo env "PATH=$PATH" mql test vm
```

### RPM install fails with missing dependencies

**Symptom:** `error: Failed dependencies: libXYZ.so.N is needed by ...`

**Cause:** Missing `Provides:` in spec files. All library specs should declare
`Provides: libXYZ.so.N()(64bit)` for proper dependency resolution.

**Fix:** Use DNF5 for proper dependency resolution:

```bash
mql chroot --exec "dnf5 install /mnt/repo/<package>-*.rpm"
```

If building from source, add the missing `Provides:` to the library spec.

### `mql install` not finding the RPM

**Symptom:** `mql install <package>` fails or looks in the wrong directory.

**Fix:** Use DNF5 directly:

```bash
# First, find the file
ls RPMS/x86_64/<package>-*.rpm

# Then install with DNF5
mql chroot --exec "dnf5 install /mnt/repo/<package>-*.rpm"
```

The local repo (`$MQL_LFS/repo/`) is bind-mounted inside the chroot as
`/mnt/repo`. Copy RPMs there if needed:

```bash
cp RPMS/x86_64/<package>-*.rpm $MQL_LFS/repo/
mql repo update
```

### `nix develop` fails

```bash
# Ensure flakes are enabled
nix --extra-experimental-features 'nix-command flakes' develop
```

Or add to `~/.config/nix/nix.conf`:

```
experimental-features = nix-command flakes
```

### Overlay kernel module missing

```bash
cat /proc/filesystems | grep overlay
# If missing:
sudo modprobe overlay
```

---

## 9. What's Next

Now that you have a working environment:

- **Write a new spec:** See `SPECS/SPEC_TEMPLATE.md` for the Gen3 template and
  all conventions. Release tag is `1.m264`; debug packages are disabled;
  multiarch conditionals use `%if "%{_target_cpu}" == "i686"`.

- **Full Nix workflow:** `docs/MANUAL-NIX.md` — disk setup, NixOS host
  configuration, nginx repo hosting, ACME certificates, complete release flow.

- **Standalone workflow:** `docs/MANUAL-STANDALONE.md` — tool installation per
  distribution, manual chroot procedure, self-hosting details.

- **Architecture deep-dive:** `docs/DEVELOPMENT-SYSTEM-PLAN.md` — overlay
  system design, CLI architecture, build pipeline, dracut-ng/initramfs, ISO
  pipeline, repo structure, self-hosting milestone.

- **Decision history:** `docs/DECISIONS.md` — why dracut-ng over others, why
  xorriso, why GNU cpio, and all other tool choices with rationale.
