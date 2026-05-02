#!/usr/bin/env bash
# lib/chroot.sh - Overlay chroot management for Maqui Linux

set -euo pipefail

# Guard against multiple sourcing
if [[ -n "${MQL_CHROOT_SOURCED:-}" ]]; then
    return 0
fi
readonly MQL_CHROOT_SOURCED=1

# Load common functions
source "$MQL_PROJECT_ROOT/lib/common.sh"

# ============================================================================
# Mount / Unmount
# ============================================================================

# mql_chroot_mount [disk_path]
# Mount overlayfs + virtual filesystems + workspace bind mount.
mql_chroot_mount() {
    local disk="${1:-$(get_rootfs_path)}"
    local sudo_cmd
    sudo_cmd="$(find_sudo)" || { log_error "sudo not found"; return 1; }

    log_step "Mounting overlay at $disk/merged"

    # Create workspace mountpoint inside merged
    "$sudo_cmd" mkdir -p "$disk/merged/mnt/workspace"

    # Mount overlayfs
    "$sudo_cmd" mount -t overlay overlay \
        -o lowerdir="$disk/base",upperdir="$disk/layers/upper",workdir="$disk/layers/work" \
        "$disk/merged"

    # Mount virtual filesystems
    "$sudo_cmd" mount -t proc proc        "$disk/merged/proc"
    "$sudo_cmd" mount --bind /dev         "$disk/merged/dev"
    "$sudo_cmd" mount -t devpts devpts    "$disk/merged/dev/pts"
    "$sudo_cmd" mount --bind /sys         "$disk/merged/sys"
    "$sudo_cmd" mount -t tmpfs tmpfs      "$disk/merged/run"
    "$sudo_cmd" mount --bind /dev/shm     "$disk/merged/dev/shm"

    # Bind workspace (project root) into chroot
    "$sudo_cmd" mount --bind "$(get_project_root)" "$disk/merged/mnt/workspace"

    log_ok "Overlay mounted at $disk/merged"
}

# mql_chroot_umount [disk_path]
# Lazy unmount in reverse order. Idempotent.
mql_chroot_umount() {
    local disk="${1:-$(get_rootfs_path)}"
    local sudo_cmd
    sudo_cmd="$(find_sudo)" || { log_error "sudo not found"; return 1; }

    log_step "Unmounting overlay at $disk/merged"

    # Unmount in reverse order (lazy -l to handle busy mounts)
    for mp in \
        "$disk/merged/mnt/workspace" \
        "$disk/merged/dev/shm" \
        "$disk/merged/dev/pts" \
        "$disk/merged/run" \
        "$disk/merged/sys" \
        "$disk/merged/proc" \
        "$disk/merged/dev" \
        "$disk/merged"
    do
        if mountpoint -q "$mp" 2>/dev/null; then
            "$sudo_cmd" umount -l "$mp" 2>/dev/null || true
        fi
    done

    log_ok "Overlay unmounted"
}

# ============================================================================
# Execute / Interactive
# ============================================================================

# mql_chroot_exec <cmd> [--preserve-env]
# Run a command inside the chroot. Returns command exit code. Does NOT exec.
# Note: no exec here -- must return for --both multi-arch support
mql_chroot_exec() {
    local cmd="$1"
    local preserve_env="${2:-false}"
    local disk
    disk="$(get_rootfs_path)"

    local sudo_cmd chroot_cmd
    sudo_cmd="$(find_sudo)"   || { log_error "sudo not found"; return 1; }
    chroot_cmd="$(find_chroot)" || { log_error "chroot not found"; return 1; }

    check_overlay "$disk" || return 1

    if [[ "$preserve_env" == "--preserve-env" ]] || [[ "$preserve_env" == "true" ]]; then
        if [[ $EUID -eq 0 ]]; then
            "$chroot_cmd" "$disk/merged" /bin/sh -c "$cmd"
        else
            "$sudo_cmd" "$chroot_cmd" "$disk/merged" /bin/sh -c "$cmd"
        fi
    else
        local env_prefix=(
            /usr/bin/env -i
            HOME=/root
            TERM="${TERM:-xterm}"
            LANG="${LANG:-en_US.UTF-8}"
            PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
        )
        if [[ $EUID -eq 0 ]]; then
            "$chroot_cmd" "$disk/merged" "${env_prefix[@]}" /bin/sh -c "$cmd"
        else
            "$sudo_cmd" "$chroot_cmd" "$disk/merged" "${env_prefix[@]}" /bin/sh -c "$cmd"
        fi
    fi
}

# mql_chroot_interactive
# Enter an interactive shell in the chroot.
mql_chroot_interactive() {
    local disk
    disk="$(get_rootfs_path)"

    local sudo_cmd chroot_cmd
    sudo_cmd="$(find_sudo)"    || { log_error "sudo not found"; return 1; }
    chroot_cmd="$(find_chroot)" || { log_error "chroot not found"; return 1; }

    check_overlay "$disk" || return 1

    log_step "Entering chroot at $disk/merged"
    log_info "Type 'exit' to leave"

    local env_prefix=(
        /usr/bin/env -i
        HOME=/root
        TERM="${TERM:-xterm}"
        LANG="${LANG:-en_US.UTF-8}"
        PS1="(maquilinux) \u:\w\$ "
        PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
    )

    if [[ $EUID -eq 0 ]]; then
        "$chroot_cmd" "$disk/merged" "${env_prefix[@]}" /bin/bash
    else
        "$sudo_cmd" "$chroot_cmd" "$disk/merged" "${env_prefix[@]}" /bin/bash
    fi
}

# ============================================================================
# Overlay State Management
# ============================================================================

# mql_chroot_reset [disk_path]
# Unmount overlay and clear upper/work layers (discard changes).
mql_chroot_reset() {
    local disk="${1:-$(get_rootfs_path)}"
    local sudo_cmd
    sudo_cmd="$(find_sudo)" || { log_error "sudo not found"; return 1; }

    log_warn "Resetting overlay — all uncommitted changes will be discarded"

    mql_chroot_umount "$disk"

    log_step "Clearing overlay layers"
    "$sudo_cmd" rm -rf "$disk/layers/upper/"* "$disk/layers/work/"* 2>/dev/null || true

    log_ok "Overlay reset complete"
}

# mql_chroot_persist <name> [disk_path]
# Archive current overlay upper layer as a named snapshot.
mql_chroot_persist() {
    local name="${1:-}"
    local disk="${2:-$(get_rootfs_path)}"

    if [[ -z "$name" ]]; then
        log_error "Usage: mql chroot --persist <name>"
        return 1
    fi

    local timestamp
    timestamp="$(date +%Y%m%d-%H%M%S)"
    local archive_dir="$disk/backup"
    local archive_file="$archive_dir/${name}-${timestamp}.tar.xz"

    mkdir -p "$archive_dir"

    log_step "Persisting overlay snapshot: $name"
    tar -cJf "$archive_file" -C "$disk/layers/upper" . 2>/dev/null

    log_ok "Snapshot saved: $archive_file"
}

# mql_chroot_promote [disk_path]
# Merge overlay upper into base (destructive, requires confirmation).
mql_chroot_promote() {
    local disk="${1:-$(get_rootfs_path)}"
    local sudo_cmd
    sudo_cmd="$(find_sudo)" || { log_error "sudo not found"; return 1; }

    log_warn "PROMOTE: Merge overlay into base rootfs — this is irreversible!"
    log_warn "Consider running 'mql backup create pre-promote' first."

    if ! confirm "Proceed with promote?"; then
        log_info "Promote cancelled"
        return 1
    fi

    # Unmount first to ensure consistency
    mql_chroot_umount "$disk"

    log_step "Merging upper into base"
    "$sudo_cmd" rsync -a --inplace "$disk/layers/upper/" "$disk/base/"

    log_step "Clearing overlay layers"
    "$sudo_cmd" rm -rf "$disk/layers/upper/"* "$disk/layers/work/"* 2>/dev/null || true

    log_ok "Promote complete — base updated"
}

# ============================================================================
# CLI Dispatcher
# ============================================================================

# mql_chroot [options]
# Subcommand dispatcher for 'mql chroot'.
mql_chroot() {
    local subcmd="${1:-interactive}"
    shift || true

    case "$subcmd" in
        --exec)
            local cmd="${1:-}"
            if [[ -z "$cmd" ]]; then
                log_error "Usage: mql chroot --exec \"<command>\""
                return 1
            fi
            mql_chroot_exec "$cmd"
            ;;
        --mount)
            mql_chroot_mount "$@"
            ;;
        --umount|--unmount)
            mql_chroot_umount "$@"
            ;;
        --reset)
            mql_chroot_reset "$@"
            ;;
        --persist)
            mql_chroot_persist "${1:-}" "${2:-}"
            ;;
        --promote)
            mql_chroot_promote "$@"
            ;;
        --help|-h)
            echo "Usage: mql chroot [--exec CMD | --mount | --umount | --reset | --persist NAME | --promote]"
            echo ""
            echo "  (no args)          Enter interactive shell"
            echo "  --exec CMD         Run CMD inside chroot"
            echo "  --mount            Mount overlay + virtual filesystems"
            echo "  --umount           Lazy unmount all filesystems"
            echo "  --reset            Unmount and discard overlay changes"
            echo "  --persist NAME     Snapshot current overlay to backup/"
            echo "  --promote          Merge overlay into base (interactive confirm)"
            ;;
        *)
            # No recognized flag — enter interactive (pass arg back)
            mql_chroot_interactive
            ;;
    esac
}

# EOF
