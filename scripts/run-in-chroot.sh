#!/usr/bin/env bash
# scripts/run-in-chroot.sh - Run commands inside Maqui Linux chroot with proper environment
#
# Usage: ./run-in-chroot.sh [options] <command>
#
# Options:
#   --preserve-env    Preserve caller's environment variables
#   --root            Run as root inside chroot (default)
#   --user <user>     Run as specific user inside chroot
#
# Examples:
#   ./run-in-chroot.sh ./mql backup create pre-rust
#   ./run-in-chroot.sh --user builder rpmbuild -ba SPECS/bash.spec
#   ./run-in-chroot.sh ls -la /workspace

set -euo pipefail

# Find workspace root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"

# Load configuration
MQL_LFS="${MQL_LFS:-/run/media/glats/maquilinux}"
if [[ -f "$WORKSPACE/mql.local" ]]; then
    source "$WORKSPACE/mql.local" 2>/dev/null || true
fi
if [[ -f "$WORKSPACE/mql.conf" ]]; then
    source "$WORKSPACE/mql.conf" 2>/dev/null || true
fi

# Paths
CHROOT_TARGET="${MQL_LFS}/merged"
WORKSPACE_IN_CHROOT="/workspace"

# Ensure chroot is ready
ensure_chroot() {
    # Check if overlay is mounted
    if ! mountpoint -q "$CHROOT_TARGET" 2>/dev/null; then
        echo "[chroot] ERROR: Overlay not mounted at $CHROOT_TARGET" >&2
        echo "[chroot] Run: mql chroot --mount" >&2
        exit 1
    fi

    # Bind mount workspace into chroot
    if [[ ! -d "$CHROOT_TARGET$WORKSPACE_IN_CHROOT" ]]; then
        mkdir -p "$CHROOT_TARGET$WORKSPACE_IN_CHROOT"
    fi

    if ! mountpoint -q "$CHROOT_TARGET$WORKSPACE_IN_CHROOT" 2>/dev/null; then
        mount --bind "$WORKSPACE" "$CHROOT_TARGET$WORKSPACE_IN_CHROOT" 2>/dev/null || {
            echo "[chroot] ERROR: Cannot bind-mount workspace" >&2
            exit 1
        }
    fi

    # Setup network for chroot (copies host DNS config)
    if [[ -f /etc/resolv.conf ]] && [[ ! -f "$CHROOT_TARGET/etc/resolv.conf" ]]; then
        cp /etc/resolv.conf "$CHROOT_TARGET/etc/resolv.conf"
        echo "[chroot] Network configured (resolv.conf copied)"
    fi

    # Ensure proc is mounted (needed by some build tools)
    if ! mountpoint -q "$CHROOT_TARGET/proc" 2>/dev/null; then
        mount -t proc proc "$CHROOT_TARGET/proc" 2>/dev/null || true
    fi

    # Ensure dev is mounted
    if ! mountpoint -q "$CHROOT_TARGET/dev" 2>/dev/null; then
        mount --bind /dev "$CHROOT_TARGET/dev" 2>/dev/null || true
    fi
}

# Preserve Nix tools PATH for commands that need them
# This makes xorriso, mksquashfs, qemu, etc. available inside chroot
prepare_nix_tools() {
    local nix_tools=""

    # Find common Nix tool directories
    for path in \
        /run/current-system/sw/bin \
        /nix/var/nix/profiles/default/bin \
        ~/.nix-profile/bin \
        "$HOME/.nix-profile/bin"; do
        if [[ -d "$path" ]]; then
            nix_tools="$nix_tools:$path"
        fi
    done

    # Also include current PATH but prioritize system paths
    echo "$nix_tools:$PATH"
}

# Parse arguments
preserve_env=false
run_as_user=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --preserve-env)
            preserve_env=true
            shift
            ;;
        --root)
            run_as_user="root"
            shift
            ;;
        --user)
            run_as_user="${2:-root}"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "[chroot] Unknown option: $1" >&2
            echo "[chroot] Usage: $0 [--preserve-env] [--root|--user <user>] <command>" >&2
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

# Ensure we have a command to run
if [[ $# -eq 0 ]]; then
    echo "[chroot] ERROR: No command specified" >&2
    echo "[chroot] Usage: $0 [--preserve-env] [--root|--user <user>] <command>" >&2
    exit 1
fi

# Setup chroot
ensure_chroot

# Build the command
# We use chroot with proper environment setup
# PATH is extended to include Nix tools for commands that need them (like mksquashfs, xorriso)

export PATH="$(prepare_nix_tools)"
export WORKSPACE="$WORKSPACE"
export MQL_PROJECT_ROOT="$WORKSPACE_IN_CHROOT"

# Preserve important environment variables
export HOME="/root"
export TERM="${TERM:-xterm}"
export LANG="${LANG:-en_US.UTF-8}"

# Run in chroot
# Use sudo only if not already root
if [[ $EUID -ne 0 ]]; then
    exec sudo chroot "$CHROOT_TARGET" "$@"
else
    exec chroot "$CHROOT_TARGET" "$@"
fi
