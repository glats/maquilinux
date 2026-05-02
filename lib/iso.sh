#!/usr/bin/env bash
# lib/iso.sh - Release artifact generation for Maqui Linux

set -euo pipefail

# Guard against multiple sourcing
if [[ -n "${MQL_ISO_SOURCED:-}" ]]; then
    return 0
fi
readonly MQL_ISO_SOURCED=1

# Load common functions
source "$MQL_PROJECT_ROOT/lib/common.sh"

# ============================================================================
# Release Functions
# ============================================================================

# mql_release_rootfs [target_dir]
# Generate rootfs from RPMs via dnf install inside chroot.
mql_release_rootfs() {
    local disk
    disk="$(get_rootfs_path)"

    source "$MQL_PROJECT_ROOT/lib/chroot.sh"
    source "$MQL_PROJECT_ROOT/lib/repo.sh"

    log_step "Generating rootfs from RPMs"

    # Update repo metadata first
    mql_repo_update

    # Install all packages from local repo into chroot
    mql_chroot_exec "dnf install -y --allowerasing /mnt/workspace/RPMS/x86_64/*.rpm" || {
        log_error "dnf install failed"
        return 1
    }

    log_ok "Rootfs generation complete"
}

# mql_release_tarball
# Package base rootfs as a compressed tarball.
mql_release_tarball() {
    local disk
    disk="$(get_rootfs_path)"

    if [[ ! -d "$disk/base" ]]; then
        log_error "Base rootfs not found: $disk/base"
        return 1
    fi

    local timestamp
    timestamp="$(date +%Y%m%d)"
    local output="$MQL_PROJECT_ROOT/maquilinux-rootfs-${timestamp}.tar.xz"

    log_step "Creating rootfs tarball: $output"
    tar -cJf "$output" -C "$disk/base" .

    local size
    size="$(du -sh "$output" | cut -f1)"
    log_ok "Tarball created: $output ($size)"
}

# mql_release_iso
# Build a bootable live ISO from the base rootfs.
# Steps:
#   1. Copy kernel from base/boot/
#   2. Generate initramfs via dracut inside chroot
#   3. Compress rootfs with mksquashfs (zstd)
#   4. Build ISO with grub-mkrescue
mql_release_iso() {
    check_iso_deps

    local disk
    disk="$(get_rootfs_path)"

    if [[ ! -d "$disk/base" ]]; then
        log_error "Base rootfs not found: $disk/base"
        return 1
    fi

    source "$MQL_PROJECT_ROOT/lib/chroot.sh"

    local timestamp
    timestamp="$(date +%Y%m%d)"
    local staging="$MQL_PROJECT_ROOT/staging-iso"
    local iso_out="$MQL_PROJECT_ROOT/maquilinux-${timestamp}.iso"

    log_step "Preparing ISO staging directory: $staging"
    rm -rf "$staging"
    mkdir -p "$staging/boot" "$staging/LiveOS"

    # Step 1: Copy kernel
    log_step "Copying kernel"
    local vmlinuz
    vmlinuz="$(find "$disk/base/boot" -name "vmlinuz-*" | sort | tail -1)"
    if [[ -z "$vmlinuz" ]]; then
        log_error "No vmlinuz found in $disk/base/boot/"
        return 1
    fi
    cp "$vmlinuz" "$staging/boot/vmlinuz"
    log_info "Kernel: $(basename "$vmlinuz")"

    # Step 2: Generate initramfs inside chroot
    log_step "Generating initramfs with dracut"
    local kver
    kver="$(basename "$vmlinuz" | sed 's/vmlinuz-//')"
    mql_chroot_exec "dracut --force --add livenet /boot/initramfs.img $kver"
    cp "$disk/merged/boot/initramfs.img" "$staging/boot/initramfs.img" 2>/dev/null || \
    cp "$disk/base/boot/initramfs.img"   "$staging/boot/initramfs.img"

    # Step 3: Compress rootfs
    log_step "Compressing rootfs with mksquashfs (zstd)"
    mksquashfs "$disk/base" "$staging/LiveOS/rootfs.img" -comp zstd -noappend -quiet

    # Step 4: Build ISO
    log_step "Building ISO with grub-mkrescue"
    grub-mkrescue -o "$iso_out" "$staging/"

    local size
    size="$(du -sh "$iso_out" | cut -f1)"
    log_ok "ISO created: $iso_out ($size)"
    rm -rf "$staging"
}

# ============================================================================
# CLI Dispatcher
# ============================================================================

mql_release() {
    local subcmd="${1:-}"
    shift || true

    case "$subcmd" in
        rootfs)
            mql_release_rootfs "$@"
            ;;
        tarball)
            mql_release_tarball "$@"
            ;;
        iso)
            mql_release_iso "$@"
            ;;
        --help|-h|"")
            echo "Usage: mql release {rootfs|tarball|iso}"
            echo ""
            echo "  rootfs   Generate rootfs from RPMs (dnf install in chroot)"
            echo "  tarball  Package base/ as maquilinux-rootfs-DATE.tar.xz"
            echo "  iso      Build bootable live ISO (kernel+dracut+squashfs+grub)"
            return 1
            ;;
        *)
            log_error "Unknown release subcommand: $subcmd"
            return 1
            ;;
    esac
}

# EOF
