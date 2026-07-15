# Exploration: Auto Release ISO Pipeline

## A. Current ISO Pipeline

### `mql release iso` — Step-by-Step (lib/iso.sh:72-125)

1. **`check_iso_deps`** (common.sh:126-146) — verifies host has: xorriso/mkisofs, mksquashfs, dracut. Fails if any missing.
2. **Copy kernel** — Finds latest `vmlinuz-*` from `$MQL_ROOTFS/base/boot/` (sorted by name), copies to staging `boot/vmlinuz`.
3. **Generate initramfs** — Runs `dracut --force --add livenet /boot/initramfs.img $kver` inside chroot via `mql_chroot_exec`. Copies result from merged or base to staging.
4. **Compress rootfs** — `mksquashfs "$disk/base" "$staging/LiveOS/rootfs.img" -comp zstd -noappend -quiet`
5. **Build ISO** — `grub-mkrescue -o "$iso_out" "$staging/"` 
6. **Output**: `maquilinux-{YYYYMMDD}.iso` in project root. Staging cleaned up.

The function does NOT regenerate the rootfs via `mql release rootfs` beforehand — it operates on the current `base/` as-is. The `mql release rootfs` subcommand (lines 21-39) installs ALL RPMs from `RPMS/x86_64/*.rpm` into the chroot via `dnf install` and is a SEPARATE, manual step.

### Dependencies (must be installed in chroot rootfs)

| Package | Spec | Role | Installed in base? |
|---------|------|------|-------------------|
| `dracut` | SPECS/dracut.spec v110 | Initramfs generator with dmsquash-live module | Unknown |
| `grub` | SPECS/grub.spec v2.12 | Bootloader, `grub-mkrescue` | Unknown |
| `libisoburn` | SPECS/libisoburn.spec v1.5.6 | xorriso ISO tool | Unknown |
| `squashfs-tools` | SPECS/squashfs-tools.spec v4.6.1 | `mksquashfs` rootfs compression | Unknown |
| `mtools` | SPECS/mtools.spec v4.0.43 | EFI boot image creation (used by grub-mkrescue) | Unknown |
| `busybox` | SPECS/busybox.spec v1.36.1 | Static binaries (mount, umount, switch_root, etc.) for initramfs | Unknown |
| `dhcpcd` | SPECS/dhcpcd.spec v10.0.6 | DHCP client for live network on boot | Unknown |
| `linux` | SPECS/linux.spec v6.17.9 | Kernel image `vmlinuz-6.17.9` | Unknown |

### ISO Capabilities (what is built today)

- **Bootable**: Yes — via GRUB (BIOS and/or UEFI, determined by grub-mkrescue)
- **Installable**: NO — no installer. GRUB entry uses `root=/dev/ram0` (live-only). No `calamares`, `anaconda`, or custom installer.
- **Live mode**: Yes — dmsquash-live via dracut mounts rootfs.img from ISO into RAM.
- **Network**: Yes (via dhcpcd in initramfs through `livenet` dracut module, also in base rootfs via dhcpcd default runlevel from capa-1).

### ISO Size

Unknown — no size data found in code or docs. Estimable from:
- Squashfs-compressed rootfs (zstd): base rootfs was ~1-2GB uncompressed, compressed ~500MB-1GB
- Kernel: ~12MB
- Initramfs: ~50-100MB
- Total estimate: **600MB - 1.2GB**

## B. Current CI Integration

### `.github/workflows/iso.yml` — Current Behavior

- **Triggers**: `git push tag v*` OR `workflow_dispatch`
- **Runner**: `[self-hosted, maquilinux]`
- **NOT using `mql release iso`** — reimplements ISO creation from scratch:
  - Gets version from tag or defaults to `26.4-YYYYMMDD`
  - Copies kernel directly from `${MQL_ROOTFS}/boot/vmlinuz-*`  
  - Runs dracut via `sudo run-in-chroot.sh` (not mql chroot --exec)
  - Uses `nix shell nixpkgs#squashfs-tools` and `nix shell nixpkgs#grub2 nixpkgs#xorriso` instead of chroot tools
  - Creates hardcoded GRUB config with `root=/dev/ram0`
  - Many steps have `|| true` masking failures
- **Output**: GitHub artifact (retention 90 days) + GitHub Release (if tag push)
- **No public publishing** — no maquiroot.glats.org URL

### `.github/workflows/build-rpms-v2.yml` — Main CI Pipeline

- **Triggers**: `push` to main (SPECS/*.spec changes), `workflow_dispatch`, `pull_request`
- **Modes**: `build-only` (default) or `publish` (build + sign + sync)
- **Flow**:
  1. Verify environment → 2. Cleanup → 3. Checkout → 4. Load config → 5. Setup chroot/overlay
  6. Determine build list (from input or git diff) → 7. Pre-build backup → 8. Disk check
  9. Validate specs (PR only) → 10. Build via `build-chain.sh` (JSON output, continue-on-failure)
  11. Acceptance tests → 12. Upload logs → 13. Collect RPMs → 14. Sign → 15. Update repo
  16. Sync to rog.local → 17. Post-build backup / restore on failure
- **No ISO step at all** — ISO generation is NOT part of the main build pipeline

### `.github/workflows/publish-rootfs.yml` — Rootfs Publishing Pattern

- **Trigger**: `workflow_dispatch` with backup_tag input
- **Flow**: Validate (integrity, DNF functionality) → rsync to rog.local → archive to history → update index.json
- **Publishes to**: `https://maquiroot.glats.org/latest/maquilinux-rootfs-latest.tar.xz`
- **Pattern**: validate-then-publish, additive sync (no --delete), history retention
- **ISO could follow same pattern**: validate → publish to maquiroot.glats.org/iso/

## C. Target Architecture

### Where ISO fits in CI pipeline

There are three viable insertion points:

1. **Within `build-rpms-v2.yml`** (after Build + Acceptance Tests, before Sync):
   - Pro: Single workflow, everything sequential, can conditionally generate ISO
   - Con: Workflow already runs 360min timeout; ISO generation adds time; ISO requires rootfs regeneration step

2. **Separate workflow triggered by `workflow_call` from `build-rpms-v2.yml`**:
   - Pro: Cleaner separation of concerns, reusable, can be tested independently
   - Con: Needs to pass state (built specs, rootfs path) between workflows

3. **Separate workflow with independent trigger** (e.g., nightly cron or tag):
   - Pro: Decoupled from build failures, predictable schedule
   - Con: No guarantee latest packages are current; requires copy of rootfs

### Recommended trigger

**Option 2 (workflow_call) combined with auto-trigger on main push when publish mode**:
- `build-rpms-v2.yml` triggers `iso.yml` via `workflow_call` after successful build + sync
- Requires all ISO dependencies to already be installed in base rootfs (achieved via `mql release rootfs`)
- ISO generation uses existing `mql release iso` command (fix iso.yml to use it)
- Conditional: only on `push` to main OR `workflow_dispatch` with `mode=publish`

### Publishing target

Follow `publish-rootfs.yml` pattern:
- **URL**: `https://maquiroot.glats.org/iso/latest/maquilinux-latest-x86_64.iso`
- **History**: `https://maquiroot.glats.org/iso/history/maquilinux-{date}-x86_64.iso`
- **Checksums**: `.iso.sha256` and `.iso.sha512` alongside
- **Also**: GitHub Release attachment (for tagged releases, like current `iso.yml`)

### Verification

- Boot test with QEMU (`qemu-system-x86_64 -cdrom maquilinux.iso -m 2048 -boot d`)
- Checksum generation (sha256 + sha512)
- Size sanity check (>500MB)
- Mount ISO and verify critical files exist (vmlinuz, initramfs.img, rootfs.img)

## D. Dependencies: What Must Be in the Rootfs for ISO

### Core ISO tools (must be installed via RPM in base rootfs)
- `dracut` (and its dmsquash-live module)
- `grub` (grub-mkrescue specifically)
- `libisoburn` (xorriso)
- `squashfs-tools` (mksquashfs)
- `mtools` (EFI image support for grub-mkrescue)

### Initramfs components (must be in rootfs for dracut to include)
- `busybox` (static /bin/busybox with all applet symlinks — provides mount, umount, switch_root, mdev, etc.)
- `dhcpcd` (network on live boot)

### Kernel requirements (must be in SPECS/linux.spec config)
- `SQUASHFS` + compression (ZSTD, XZ, ZLIB, LZO, LZ4) — ALL ENABLED in current kernel spec
- `ISO9660_FS` — ENABLED
- `CDROM` — ENABLED
- `OVERLAY_FS` — ENABLED
- `LOOP` — ENABLED

### Build-time tools (for ISO workflow host, not chroot)
- `xorriso` — for ISO creation (if not using chroot; current iso.yml uses nix shell)
- `createrepo_c` — for repo metadata regeneration (if needed)

## E. Key Decisions for Proposal

These questions need user answers before proceeding to `sdd-propose`:

### 1. Trigger Mechanism
When should ISO be auto-generated?
- [ ] **A. Every push to main** — Continuous ISO, always current, generates on every accepted spec change.
- [ ] **B. Tagged releases only** — Only when `git tag v*` is pushed (current behavior).
- [ ] **C. Scheduled nightly** — Like Fedora compose; nightly snapshot regardless of pushes.
- [ ] **D. Hybrid: push triggers ISO build, but only publish on tag** — Build ISO on every main push for testing, publish to public only on tags.

### 2. Release Rootfs Step
`mql release rootfs` installs ALL RPMs from `RPMS/x86_64/` into the chroot. This is needed BEFORE `mql release iso` can create a complete ISO.
- [ ] **A. Run on every ISO build** — Reinstall all packages (ensures consistency, but slow, ~30-60 min?)
- [ ] **B. Assume base rootfs is current** — ISO generation depends on `mql chroot --promote` having been run recently.
- [ ] **C. Create ISO from RPM repo directly** — Build ISO without depending on chroot state (more complex, but more reproducible).

### 3. Publishing Target
- [ ] **A. GitHub Releases only** — Simpler, no infrastructure changes needed.
- [ ] **B. maquiroot.glats.org** — Public ISO download alongside rootfs (needs SSH to rog.local, nginx config). Follow `publish-rootfs.yml` pattern.
- [ ] **C. Both** — GitHub Release for archival + public URL for downloads.

### 4. ISO Scope
- [ ] **A. Live ISO only** — Bootable, no installer. For testing/exploring, not installing.
- [ ] **B. Installable ISO** — Includes installer (e.g., custom script, calamares). Enables bare-metal deployment. Requires designing an installer (significant additional scope).
- [ ] **C. Both live + install** — Boot live, option to install from desktop. Largest scope.

### 5. Partial Failure Handling
If some specs fail but others succeed (build-chain uses `--continue-on-failure`):
- [ ] **A. Skip ISO if any spec failed** — Only generate ISO on clean full-build success. Safest, but may delay ISOs significantly.
- [ ] **B. Generate ISO anyway** — Use whatever packages built successfully. ISO may be incomplete but shows progress.
- [ ] **C. Generate ISO if core deps succeeded** — Define a minimum package set (kernel, dracut, grub, busybox) and generate ISO if those succeeded.

### 6. Integration Depth
- [ ] **A. New reusable workflow (`iso-build.yml`)** — Called by `build-rpms-v2.yml` via `workflow_call`. Clean separation, reusable by other workflows.
- [ ] **B. Additional job in `build-rpms-v2.yml`** — Simpler, everything in one file. Less reusable.
- [ ] **C. Refactor `iso.yml` to use `mql release iso`** — Fix the existing workflow to use the mql CLI properly, then add workflow_call trigger.

## F. Industry Patterns

### Fedora (Pungi + Koji)
- **System**: Pungi compose tool orchestrates phases: pkgset → gather → createrepo → buildinstall → createiso → checksums
- **Trigger**: Nightly cron for Rawhide, manual for milestone releases
- **ISO types**: netinstall (boot.iso via lorax), DVD (full repo), live images
- **Publishing**: Synced to mirrors after compose completes
- **Verification**: Image checksum, bootable media properties check
- **Key insight**: ISO is post-build, separate phase. Build and compose are decoupled.

### Arch Linux (archiso + releng)
- **System**: `mkarchiso` tool, GitLab CI for builds
- **Trigger**: Monthly release cycle, manual promotion
- **Artifacts**: bootstrap tarball + ISO + netboot per release
- **Publishing**: GitHub Releases with detached PGP signatures, torrents
- **Key insight**: Build is CI-automated; publishing (signing, promoting) is manual developer gate.

### openSUSE (OBS)
- **System**: Open Build Service — builds packages → publishes repos → KIWI builds images from repos
- **Decoupling**: Package build and image build are separate events. Image build consumes the published repo.

### Maqui Linux's Position
- Maqui is closer to Arch's model: single build machine, self-hosted runner, git-triggered builds
- Fedora's Pungi model (nightly compose) is aspirational but requires significant infrastructure
- Recommended: **Arch-inspired pattern** — CI builds packages → promotes rootfs → CI builds ISO from promoted rootfs → manual gate for public release (sign/promote)

## G. Affected Areas

| File | Why affected |
|------|-------------|
| `lib/iso.sh` | Must be verified that `mql release iso` works end-to-end; may need fixes |
| `lib/common.sh` | `check_iso_deps` needs updating if deps change |
| `.github/workflows/iso.yml` | Refactor to use `mql release iso` instead of inline reimplementation |
| `.github/workflows/build-rpms-v2.yml` | Add ISO trigger step (or workflow_call invocation) after successful build |
| `SPECS/dracut.spec` | May need live ISO config adjustments (dmsquash-live module confirmed present) |
| `SPECS/linux.spec` | Kernel config for ISO boot (SQUASHFS, ISO9660, CDROM — all already enabled) |
| `scripts/run-in-chroot.sh` | Used by iso.yml; may not be needed if switched to `mql release iso` |
| `.github/workflows/publish-rootfs.yml` | Pattern to follow for ISO publishing |

## H. Summary

**Current state**: ISO generation exists (`mql release iso`) but is completely decoupled from the build pipeline. The `iso.yml` workflow reimplements ISO creation differently from `mql release iso`, and neither is triggered automatically by successful builds. ISO is not published to a public URL.

**Core gap**: No automation — no trigger from build → ISO, no publishing to maquiroot.glats.org.

**Recommended direction**: 
1. Fix `iso.yml` to use `mql release iso` 
2. Add workflow_call trigger
3. Have `build-rpms-v2.yml` invoke ISO build on successful main push publish
4. Publish ISO to maquiroot.glats.org/iso/ following publish-rootfs.yml pattern
5. ISO scope: live ISO initially (what `mql release iso` already builds), installable ISO deferred
