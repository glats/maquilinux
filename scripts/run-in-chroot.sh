#!/usr/bin/env bash
# scripts/run-in-chroot.sh - Run commands inside Maqui Linux chroot
#
# Usage: ./run-in-chroot.sh [options] <command>
#
# Prerequisites:
#   - Overlay must be mounted at $MQL_DISK/merged
#   - Workspace must be bind-mounted at $MQL_DISK/merged/workspace
#   - /proc, /dev, /etc/resolv.conf must be set up in chroot
#
# Setup (run once before using this script):
#   sudo mkdir -p "$MQL_DISK/merged/workspace"
#   sudo mount --bind "$PWD" "$MQL_DISK/merged/workspace"
#   sudo cp /etc/resolv.conf "$MQL_DISK/merged/etc/"
#   sudo mount -t proc proc "$MQL_DISK/merged/proc"
#   sudo mount --bind /dev "$MQL_DISK/merged/dev"
#
# Examples:
#   ./run-in-chroot.sh ./mql backup create pre-rust
#   ./run-in-chroot.sh rpmbuild -ba SPECS/bash.spec
#   ./run-in-chroot.sh ls -la /workspace

set -euo pipefail

# Find sudo (NixOS fix: /run/wrappers/bin/sudo has setuid bit)
find_sudo() {
    for path in /run/wrappers/bin/sudo /usr/bin/sudo /bin/sudo; do
        if [[ -x "$path" ]]; then
            echo "$path"
            return
        fi
    done
    # Fallback to PATH
    if command -v sudo &> /dev/null; then
        echo "sudo"
    else
        echo ""
    fi
}
SUDO_CMD="$(find_sudo)"
if [[ -z "$SUDO_CMD" ]]; then
    echo "[chroot] ERROR: sudo not found" >&2
    exit 1
fi

# Find workspace root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"

# Load configuration
MQL_DISK="${MQL_DISK:-${MQL_ROOT:-/run/media/glats/maquilinux}}"
if [[ -f "$WORKSPACE/mql.local" ]]; then
    source "$WORKSPACE/mql.local" 2>/dev/null || true
fi
if [[ -f "$WORKSPACE/mql.conf" ]]; then
    source "$WORKSPACE/mql.conf" 2>/dev/null || true
fi

# Support MQL_ROOT, MQL_DISK, and legacy MQL_LFS
CHROOT_TARGET="${MQL_ROOT:-${MQL_DISK:-$MQL_LFS}}/merged"
WORKSPACE_IN_CHROOT="/workspace"

# Verify chroot is ready (mounts must be done externally)
verify_chroot() {
    if ! mountpoint -q "$CHROOT_TARGET" 2>/dev/null; then
        echo "[chroot] ERROR: Overlay not mounted at $CHROOT_TARGET" >&2
        echo "[chroot] Run setup first:" >&2
        echo "[chroot]   sudo ./mql chroot --mount" >&2
        echo "[chroot] Or manually:" >&2
        echo "[chroot]   sudo mount -t overlay overlay -o lowerdir=...,upperdir=...,workdir=... $CHROOT_TARGET" >&2
        exit 1
    fi

    if ! mountpoint -q "$CHROOT_TARGET$WORKSPACE_IN_CHROOT" 2>/dev/null; then
        echo "[chroot] ERROR: Workspace not bind-mounted at $CHROOT_TARGET$WORKSPACE_IN_CHROOT" >&2
        echo "[chroot] Run setup first:" >&2
        echo "[chroot]   sudo mkdir -p $CHROOT_TARGET$WORKSPACE_IN_CHROOT" >&2
        echo "[chroot]   sudo mount --bind $WORKSPACE $CHROOT_TARGET$WORKSPACE_IN_CHROOT" >&2
        exit 1
    fi
}

# Parse arguments
preserve_env=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --preserve-env)
            preserve_env=true
            shift
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "[chroot] Unknown option: $1" >&2
            echo "[chroot] Usage: $0 [--preserve-env] <command>" >&2
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -eq 0 ]]; then
    echo "[chroot] ERROR: No command specified" >&2
    echo "[chroot] Usage: $0 [--preserve-env] <command>" >&2
    exit 1
fi

# Verify setup
verify_chroot

# Find chroot command
CHROOT_CMD=$(command -v chroot || echo "")
if [[ -z "$CHROOT_CMD" ]]; then
    # Try common locations
    for path in /run/current-system/sw/bin/chroot /usr/sbin/chroot /sbin/chroot; do
        if [[ -x "$path" ]]; then
            CHROOT_CMD="$path"
            break
        fi
    done
fi

if [[ -z "$CHROOT_CMD" ]]; then
    echo "[chroot] ERROR: chroot command not found in PATH" >&2
    echo "[chroot] PATH=$PATH" >&2
    echo "[chroot] Install util-linux or coreutils package" >&2
    exit 1
fi

# Set environment
export HOME="/root"
export TERM="${TERM:-xterm}"
export LANG="${LANG:-en_US.UTF-8}"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Execute in chroot
# chroot requires root privileges
if [[ $EUID -eq 0 ]]; then
    exec "$CHROOT_CMD" "$CHROOT_TARGET" "$@"
else
    exec "$SUDO_CMD" "$CHROOT_CMD" "$CHROOT_TARGET" "$@"
fi
