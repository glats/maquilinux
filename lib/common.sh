#!/usr/bin/env bash
# lib/common.sh - Common functions for mql CLI
# Phase 1: Core library with logging, colors, and dependency validation

set -euo pipefail

# ============================================================================
# Guard against multiple sourcing
# ============================================================================

if [[ -n "${MQL_COMMON_SOURCED:-}" ]]; then
    return 0
fi
readonly MQL_COMMON_SOURCED=1

# ============================================================================
# Colors and Terminal Output
# ============================================================================

# Check if terminal supports colors
if [[ -t 1 ]]; then
    readonly COLOR_RED='\033[0;31m'
    readonly COLOR_GREEN='\033[0;32m'
    readonly COLOR_YELLOW='\033[1;33m'
    readonly COLOR_BLUE='\033[0;34m'
    readonly COLOR_CYAN='\033[0;36m'
    readonly COLOR_NC='\033[0m' # No Color
else
    readonly COLOR_RED=''
    readonly COLOR_GREEN=''
    readonly COLOR_YELLOW=''
    readonly COLOR_BLUE=''
    readonly COLOR_CYAN=''
    readonly COLOR_NC=''
fi

# Logging functions
log_info() {
    echo -e "${COLOR_BLUE}[INFO]${COLOR_NC} $*" >&2
}

log_ok() {
    echo -e "${COLOR_GREEN}[OK]${COLOR_NC} $*" >&2
}

log_warn() {
    echo -e "${COLOR_YELLOW}[WARN]${COLOR_NC} $*" >&2
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_NC} $*" >&2
}

log_step() {
    echo -e "${COLOR_CYAN}=>${COLOR_NC} $*" >&2
}

# ============================================================================
# Dependency Validation
# ============================================================================

# Check if a command exists
check_cmd() {
    local cmd="$1"
    if command -v "$cmd" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Validate required dependencies for a command
dep_error() {
    log_error "Missing required tool: $1"
    log_info "Install it with your distribution's package manager:"
    log_info "  Fedora: sudo dnf install $2"
    log_info "  Debian: sudo apt install $3"
    log_info "  Arch:   sudo pacman -S $4"
    exit 1
}

# Check core dependencies (always needed)
check_core_deps() {
    if ! check_cmd bash; then
        log_error "bash is required but not found"
        exit 1
    fi
    
    # Check bash version >= 5.0
    local bash_version
    bash_version=$(bash --version | head -1 | grep -oP '\d+\.\d+' | head -1)
    if [[ $(echo "$bash_version < 5.0" | bc -l 2>/dev/null || echo "1") -eq 1 ]]; then
        log_warn "bash version $bash_version detected, >= 5.0 recommended"
    fi
}

# Check dependencies for chroot operations
check_chroot_deps() {
    local missing=()
    
    if ! check_cmd mount; then missing+=("mount (util-linux)"); fi
    if ! check_cmd umount; then missing+=("umount (util-linux)"); fi
    if ! check_cmd chroot; then missing+=("chroot (util-linux)"); fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing chroot dependencies: ${missing[*]}"
        log_info "Install util-linux package"
        exit 1
    fi
    
    # Check for overlayfs support
    if ! grep -q overlay /proc/filesystems 2>/dev/null; then
        log_warn "overlayfs not available in kernel"
        log_info "Try: sudo modprobe overlay"
    fi
}

# Check dependencies for repo operations
check_repo_deps() {
    if ! check_cmd createrepo_c; then
        dep_error "createrepo_c" "createrepo_c" "createrepo-c" "createrepo_c"
    fi
}

# Check dependencies for ISO operations
check_iso_deps() {
    local missing=()
    
    if ! check_cmd xorriso && ! check_cmd mkisofs; then
        missing+=("xorriso/libisoburn")
    fi
    
    if ! check_cmd mksquashfs; then
        missing+=("squashfs-tools")
    fi
    
    if ! check_cmd dracut; then
        missing+=("dracut")
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing ISO dependencies: ${missing[*]}"
        log_info "Install: xorriso squashfs-tools dracut"
        exit 1
    fi
}

# Check dependencies for VM testing
check_vm_deps() {
    if ! check_cmd qemu-system-x86_64 && ! check_cmd qemu-system-x86; then
        dep_error "qemu" "qemu-system-x86" "qemu-system-x86" "qemu-full"
    fi
}

# ============================================================================
# Path Configuration
# ============================================================================

# Get the project root directory
get_project_root() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    echo "$script_dir"
}

# Path helper functions - always read from env so overrides are picked up
get_repo_dest() {
    local releasever="${MQL_RELEASEVER:-26.4}"
    echo "${MQL_REPO_DEST:-/srv/glats/nginx/repo/maquilinux/${releasever}}"
}

get_repo_url() {
    echo "${MQL_REPO_URL:-https://repo.glats.org/linux/maquilinux}"
}

# ============================================================================
# Error Handling
# ============================================================================

# Error handler
die() {
    log_error "$*"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        die "This command must be run as root (use: sudo mql <command>)"
    fi
}

# Check if not running as root (for some commands)
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "Running as root when not required"
    fi
}

# ============================================================================
# Utility Functions
# ============================================================================

# Check if a directory is a mountpoint
is_mounted() {
    local path="$1"
    mountpoint -q "$path" 2>/dev/null
}

# Safely unmount (ignore if not mounted)
safe_umount() {
    local path="$1"
    if is_mounted "$path"; then
        umount "$path" 2>/dev/null || true
    fi
}

# Get disk usage in human readable format
get_disk_usage() {
    local path="$1"
    if [[ -e "$path" ]]; then
        du -sh "$path" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

# Count files matching pattern
count_files() {
    local pattern="$1"
    find . -name "$pattern" -type f 2>/dev/null | wc -l
}

# Confirm action with user
confirm() {
    local prompt="${1:-Are you sure?}"
    local response
    
    read -r -p "$prompt [y/N] " response
    [[ "$response" =~ ^[Yy]$ ]]
}

# ============================================================================
# Initialization
# ============================================================================

# ============================================================================
# Tool Discovery (NixOS-aware)
# ============================================================================

# find_tool <name> [extra_paths...]
# Search extra_paths first, then PATH. Returns path and rc=0, or rc=1.
find_tool() {
    local name="$1"; shift
    for p in "$@"; do [[ -x "$p" ]] && echo "$p" && return 0; done
    local f; f="$(command -v "$name" 2>/dev/null)" && echo "$f" && return 0
    return 1
}

find_sudo() {
    find_tool sudo /run/wrappers/bin/sudo /usr/bin/sudo /bin/sudo
}

find_chroot() {
    find_tool chroot /run/current-system/sw/bin/chroot /usr/sbin/chroot /sbin/chroot /bin/chroot
}

is_nixos() {
    [[ -f /etc/NIXOS ]]
}

# check_overlay [disk_path]
# Validates overlay directories and merged mountpoint.
check_overlay() {
    local disk="${1:-$(get_rootfs_path)}"
    local ok=0
    [[ -d "$disk/base" ]]         || { log_error "Missing: $disk/base";         ok=1; }
    [[ -d "$disk/layers/upper" ]] || { log_error "Missing: $disk/layers/upper"; ok=1; }
    [[ -d "$disk/layers/work" ]]  || { log_error "Missing: $disk/layers/work";  ok=1; }
    mountpoint -q "$disk/merged"  || { log_error "Not mounted: $disk/merged";   ok=1; }
    return $ok
}

# get_rootfs_path
# Priority: MQL_ROOTFS > MQL_DISK > MQL_LFS (deprecated, warns) > /mnt/maquilinux
get_rootfs_path() {
    if [[ -n "${MQL_ROOTFS:-}" ]]; then
        echo "$MQL_ROOTFS"
    elif [[ -n "${MQL_DISK:-}" ]]; then
        echo "$MQL_DISK"
    elif [[ -n "${MQL_LFS:-}" ]]; then
        log_warn "MQL_LFS is deprecated, use MQL_ROOTFS" >&2
        echo "$MQL_LFS"
    else
        echo "/mnt/maquilinux"
    fi
}

# Deprecated alias - use get_rootfs_path
get_lfs_path() {
    log_warn "get_lfs_path() is deprecated, use get_rootfs_path()" >&2
    get_rootfs_path
}

# ============================================================================
# Initialization
# ============================================================================

# Check core deps on load
check_core_deps
