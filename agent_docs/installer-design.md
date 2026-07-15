# Installable ISO Design

Stability: design-only

## Phase 2 -- Design Only. Not Yet Implemented.

This document captures the design approach for building an installable ISO. No
code exists yet. The current ISO is live-bootable only (no installer).

## Current State

The ISO produced by `mql release iso` boots into a live environment. It contains:
- Kernel + initramfs (dracut with livenet)
- Squashfs rootfs (all RPMs installed)
- GRUB bootloader

It does NOT include an installer script, partitioning logic, or bootloader
installation for target disks.

## Design: Custom Shell-Script Installer (Recommended)

| Option | GUI deps | Effort | Maintenance | Phase fit |
|--------|----------|--------|-------------|-----------|
| A. Custom shell installer | None | Low | Low (Maqui-specific) | Phase 1 |
| B. Calamares | Qt6 + X/Wayland | High | High (upstream deltas) | Phase 2+ |
| C. Anaconda-lite | Python + rpm-native | High | High (Fedora coupling) | Phase 3+ |

**Recommendation: Option A (custom shell script).** Rationale:
- Zero GUI dependencies -- keeps ISO small (600 MB - 1.2 GB target)
- Maqui-specific -- no upstream coupling, full control
- Can be added to squashfs without changing ISO build pipeline

## Minimal Viable Installer Feature Set

1. **Partition target disk** -- prompt for disk device, create partitions with
   `parted` or `cfdisk`, format with `mkfs.ext4`, mount at `/mnt/target`
2. **Extract rootfs** -- mount ISO's `/LiveOS/rootfs.img`, copy via `tar` (or
   `unsquashfs`) to target partition
3. **Install bootloader** -- `grub-install` on target disk, generate `grub.cfg`
   with `os-prober` or manual config
4. **Configure fstab** -- write `/etc/fstab` with target disk UUIDs
5. **Set hostname** -- prompt or default to `maqui`

## RPM Spec Dependencies

| Package | Needed for | Phase |
|---------|-----------|-------|
| `parted` | Disk partitioning | Phase 1 |
| `grub` | Bootloader install | Phase 1 |
| `dosfstools` | EFI system partition | Phase 1 |
| `util-linux` | `lsblk`, `blkid`, `mount` | Phase 1 |
| `e2fsprogs` | ext4 formatting | Phase 1 |

No new build flags or ISO changes needed: all dependencies are standard Linux
utilities already in the repo or easily packaged.

## Future Phases

- Phase 2: `mql install` subcommand implementing the installer logic
- Phase 3: Optional Calamares integration for GUI installer (separate ISO profile)
- Phase 4: Multi-architecture installer support (x86_64 + i686)

## Related Docs

- `lib/iso.sh` -- Current ISO builder (no installer)
- `agent_docs/release-engineering.md` -- ISO build and publish flow
