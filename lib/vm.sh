#!/usr/bin/env bash
# lib/vm.sh - Testing and verification for Maqui Linux

set -euo pipefail

# Guard against multiple sourcing
if [[ -n "${MQL_VM_SOURCED:-}" ]]; then
    return 0
fi
readonly MQL_VM_SOURCED=1

# Load common functions
source "$MQL_PROJECT_ROOT/lib/common.sh"

# ============================================================================
# Test Functions
# ============================================================================

# mql_test_vm [memory] [cpus]
# Boot the latest ISO in QEMU with KVM acceleration.
mql_test_vm() {
    local memory="${1:-2G}"
    local cpus="${2:-2}"

    check_vm_deps

    local qemu_cmd
    qemu_cmd="$(find_tool qemu-system-x86_64 /run/current-system/sw/bin/qemu-system-x86_64)" || {
        log_error "qemu-system-x86_64 not found"
        return 1
    }

    # Find latest ISO
    local iso
    iso="$(find "$MQL_PROJECT_ROOT" -maxdepth 1 -name "maquilinux-*.iso" | sort | tail -1)"

    if [[ -z "$iso" ]]; then
        log_error "No ISO found in $MQL_PROJECT_ROOT"
        log_info "Build one first: mql release iso"
        return 1
    fi

    log_step "Booting: $(basename "$iso") (memory=$memory, cpus=$cpus)"
    log_info "QEMU: $qemu_cmd"

    "$qemu_cmd" \
        -m "$memory" \
        -smp "$cpus" \
        -enable-kvm \
        -cdrom "$iso" \
        -boot d \
        -vga virtio \
        -serial stdio
}

# mql_test_smoke
# Run basic smoke tests inside the chroot.
mql_test_smoke() {
    source "$MQL_PROJECT_ROOT/lib/chroot.sh"

    local disk
    disk="$(get_rootfs_path)"

    log_step "Running smoke tests"

    local failed=0

    # Test 1: Package count
    log_info "Test 1: RPM package count"
    local pkg_count
    pkg_count="$(mql_chroot_exec "rpm -qa | wc -l" 2>/dev/null || echo 0)"
    if [[ "$pkg_count" -gt 0 ]]; then
        log_ok "Packages installed: $pkg_count"
    else
        log_error "No packages found in chroot"
        ((failed++))
    fi

    # Test 2: DNF version
    log_info "Test 2: DNF availability"
    if mql_chroot_exec "dnf --version" >/dev/null 2>&1; then
        log_ok "DNF works"
    else
        log_error "DNF not available"
        ((failed++))
    fi

    # Test 3: Basic shell
    log_info "Test 3: Basic shell echo"
    local result
    result="$(mql_chroot_exec "echo smoke_ok" 2>/dev/null || echo '')"
    if [[ "$result" == *"smoke_ok"* ]]; then
        log_ok "Shell echo: ok"
    else
        log_error "Shell echo failed"
        ((failed++))
    fi

    if [[ $failed -eq 0 ]]; then
        log_ok "All smoke tests passed"
    else
        log_error "$failed smoke test(s) failed"
        return 1
    fi
}

# mql_test_verify
# Verify the environment and project structure are healthy.
mql_test_verify() {
    log_step "Verifying Maqui Linux environment"

    local failed=0

    # Check no LFS references in spec files
    log_info "Check: no linuxfromscratch.org references in SPECS/"
    local lfs_refs
    lfs_refs="$(grep -rl "linuxfromscratch.org" "$MQL_PROJECT_ROOT/SPECS/" 2>/dev/null | wc -l)"
    if [[ "$lfs_refs" -eq 0 ]]; then
        log_ok "No LFS references in SPECS/"
    else
        log_warn "Found $lfs_refs spec(s) referencing linuxfromscratch.org"
    fi

    # Check MQL_ROOTFS or fallback set
    log_info "Check: rootfs path configured"
    local rootfs
    rootfs="$(get_rootfs_path)"
    log_ok "Rootfs path: $rootfs"

    # Check required lib files exist
    log_info "Check: lib files present"
    local libs=(common.sh chroot.sh repo.sh iso.sh vm.sh backup.sh build.sh)
    for lib in "${libs[@]}"; do
        if [[ -f "$MQL_PROJECT_ROOT/lib/$lib" ]]; then
            log_ok "lib/$lib"
        else
            log_error "Missing: lib/$lib"
            ((failed++))
        fi
    done

    # Check SPECS/ directory
    log_info "Check: SPECS/ directory"
    local spec_count
    spec_count="$(find "$MQL_PROJECT_ROOT/SPECS" -name "*.spec" 2>/dev/null | wc -l)"
    if [[ "$spec_count" -gt 0 ]]; then
        log_ok "Specs found: $spec_count"
    else
        log_error "No spec files found in SPECS/"
        ((failed++))
    fi

    if [[ $failed -eq 0 ]]; then
        log_ok "All verification checks passed"
    else
        log_error "$failed check(s) failed"
        return 1
    fi
}

# ============================================================================
# CLI Dispatcher
# ============================================================================

mql_test() {
    local subcmd="${1:-}"
    shift || true

    case "$subcmd" in
        vm)
            mql_test_vm "$@"
            ;;
        smoke)
            mql_test_smoke "$@"
            ;;
        verify)
            mql_test_verify "$@"
            ;;
        --help|-h|"")
            echo "Usage: mql test {vm|smoke|verify}"
            echo ""
            echo "  vm [MEM] [CPUS]  Boot latest ISO in QEMU (default: 2G, 2 CPUs)"
            echo "  smoke            Quick sanity checks inside chroot"
            echo "  verify           Check environment and project structure"
            return 1
            ;;
        *)
            log_error "Unknown test subcommand: $subcmd"
            return 1
            ;;
    esac
}

# EOF
