#!/usr/bin/env bash
# lib/init.sh - Developer onboarding: initialize rootfs from tarball
# Implements: mql init --from-file <tarball> [--rootfs <path>] [--force]

set -euo pipefail

# Guard against multiple sourcing
if [[ -n "${MQL_INIT_SOURCED:-}" ]]; then
    return 0
fi
readonly MQL_INIT_SOURCED=1

# Load common functions
source "$MQL_PROJECT_ROOT/lib/common.sh"

# ============================================================================
# mql_init - Initialize developer environment from rootfs tarball
#
# Usage:
#   mql init --from-file <tarball> [--rootfs <path>] [--force]
#
# Arguments:
#   --from-file <path>   Path to rootfs tarball (.tar.gz or .tar.xz) [required]
#   --rootfs <path>      Override MQL_ROOTFS (default: /mnt/maquilinux)
#   --force              Overwrite existing base/ and mql.local
#
# Returns:
#   0 on success, 1 on error
# ============================================================================

mql_init() {
    local tarball=""
    local rootfs="${MQL_ROOTFS:-/mnt/maquilinux}"
    local force=0

    # ----------------------------------------------------------------
    # A1 + A2: Argument parsing
    # ----------------------------------------------------------------
    if [[ $# -eq 0 ]]; then
        _init_usage
        return 1
    fi

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --from-file)
                [[ $# -lt 2 ]] && { log_error "--from-file requires a path argument"; return 1; }
                tarball="$2"
                shift 2
                ;;
            --rootfs)
                [[ $# -lt 2 ]] && { log_error "--rootfs requires a path argument"; return 1; }
                rootfs="$2"
                shift 2
                ;;
            --force)
                force=1
                shift
                ;;
            -h|--help)
                _init_usage
                return 0
                ;;
            *)
                log_error "Unknown argument: $1"
                _init_usage
                return 1
                ;;
        esac
    done

    # Required argument check
    if [[ -z "$tarball" ]]; then
        log_error "--from-file <path> is required"
        _init_usage
        return 1
    fi

    # Resolve tarball to absolute path
    tarball="$(realpath "$tarball" 2>/dev/null || echo "$tarball")"
    export MQL_ROOTFS="$rootfs"

    log_step "Initializing Maqui Linux developer environment"
    log_info "Tarball: $tarball"
    log_info "Target:  $MQL_ROOTFS"

    # ----------------------------------------------------------------
    # A3: Validate tarball exists and is readable
    # ----------------------------------------------------------------
    if [[ ! -f "$tarball" ]]; then
        log_error "Tarball not found: $tarball"
        return 1
    fi

    if [[ ! -r "$tarball" ]]; then
        log_error "Tarball is not readable: $tarball"
        return 1
    fi

    # Detect tarball format via file magic
    if check_cmd file; then
        local file_type
        file_type="$(file -b "$tarball")"
        case "$file_type" in
            *XZ\ compressed*|*gzip\ compressed*|*tar\ archive*)
                log_ok "Tarball format detected: $file_type"
                ;;
            *)
                log_error "Unsupported tarball format: $file_type"
                log_error "Expected gzip or xz compressed tar archive"
                return 1
                ;;
        esac
    else
        log_warn "'file' command not available, skipping format detection"
    fi

    # Check sudo is available
    local sudo_cmd
    sudo_cmd="$(find_sudo)" || { log_error "sudo is required but not found"; return 1; }

    # ----------------------------------------------------------------
    # A4: Checksum verification (best-effort)
    # ----------------------------------------------------------------
    if [[ -f "${tarball}.sha256" ]]; then
        if check_cmd sha256sum; then
            log_step "Verifying checksum"
            # cd to tarball directory so .sha256's relative path resolves correctly
            if (cd "$(dirname "$tarball")" && sha256sum -c "$(basename "$tarball").sha256") >/dev/null 2>&1; then
                log_ok "Checksum verified"
            else
                log_error "Checksum verification failed. Tarball may be corrupted."
                return 1
            fi
        else
            log_warn "sha256sum not found, skipping checksum verification"
        fi
    else
        log_warn "No checksum file found, skipping integrity verification"
    fi

    # ----------------------------------------------------------------
    # A5: Disk space check
    # ----------------------------------------------------------------
    local tarball_size
    tarball_size="$(stat --format=%s "$tarball" 2>/dev/null || stat -f%z "$tarball" 2>/dev/null || echo 0)"

    if [[ "$tarball_size" -gt 0 ]]; then
        local parent_dir
        parent_dir="$(dirname "$MQL_ROOTFS")"
        # Ensure parent exists for df
        if [[ -d "$parent_dir" ]]; then
            local avail_kb
            avail_kb="$(df --output=avail "$parent_dir" 2>/dev/null | tail -1 | tr -d ' ')"
            local avail_bytes=$((avail_kb * 1024))
            local tarball_bytes=$tarball_size
            local required_bytes=$((tarball_size * 2))

            local tarball_human
            tarball_human="$(numfmt --to=iec-i --suffix=B "$tarball_size" 2>/dev/null || echo "${tarball_size} bytes")"
            local avail_human
            avail_human="$(numfmt --to=iec-i --suffix=B "$avail_bytes" 2>/dev/null || echo "${avail_kb}K")"

            # Block if available < 1x tarball size
            if [[ "$avail_bytes" -lt "$tarball_bytes" ]]; then
                log_error "Insufficient disk space: $avail_human available, need at least $tarball_human"
                return 1
            fi

            # Warn if available < 2x tarball size
            if [[ "$avail_bytes" -lt "$required_bytes" ]]; then
                log_warn "Low disk space: $avail_human available, ~$(numfmt --to=iec-i --suffix=B "$required_bytes" 2>/dev/null || echo "$required_bytes bytes") recommended for $tarball_human tarball"
                if ! confirm "Continue anyway?"; then
                    log_info "Aborted by user"
                    return 1
                fi
            fi
        fi
    fi

    # ----------------------------------------------------------------
    # A6: Idempotency check - base/ already exists?
    # ----------------------------------------------------------------
    if [[ -d "$MQL_ROOTFS/base" ]] && [[ -n "$(ls -A "$MQL_ROOTFS/base" 2>/dev/null)" ]]; then
        if [[ "$force" -eq 1 ]]; then
            log_warn "Removing existing base/ (--force specified)"
            "$sudo_cmd" rm -rf "$MQL_ROOTFS/base"
        else
            log_error "Rootfs already exists at $MQL_ROOTFS/base/. Use --force to overwrite."
            return 1
        fi
    fi

    # ----------------------------------------------------------------
    # A7: Create overlay directory structure
    # ----------------------------------------------------------------
    log_step "Creating directory structure"
    "$sudo_cmd" mkdir -p "$MQL_ROOTFS/base"
    "$sudo_cmd" mkdir -p "$MQL_ROOTFS/layers/upper"
    "$sudo_cmd" mkdir -p "$MQL_ROOTFS/layers/work"
    "$sudo_cmd" mkdir -p "$MQL_ROOTFS/merged"
    "$sudo_cmd" mkdir -p "$MQL_ROOTFS/repo"
    log_ok "Directory structure created"

    # ----------------------------------------------------------------
    # A8: Extract tarball
    # ----------------------------------------------------------------
    log_step "Extracting tarball (this may take a few minutes)..."
    if "$sudo_cmd" tar -xf "$tarball" -C "$MQL_ROOTFS/base/"; then
        log_ok "Extraction complete"
    else
        log_error "Extraction failed. Use --force to retry."
        return 1
    fi

    # Sanity check: base/bin/sh should exist after extraction
    if [[ -e "$MQL_ROOTFS/base/bin/sh" ]] || [[ -e "$MQL_ROOTFS/base/usr/bin/sh" ]]; then
        log_ok "Sanity check passed: shell binary found in rootfs"
    else
        log_warn "Sanity check: bin/sh not found in extracted rootfs (may still be valid)"
    fi

    # ----------------------------------------------------------------
    # A9: Generate mql.local
    # ----------------------------------------------------------------
    local mql_local="$MQL_PROJECT_ROOT/mql.local"
    if [[ -f "$mql_local" ]]; then
        if [[ "$force" -eq 1 ]]; then
            log_warn "Overwriting existing mql.local (--force specified)"
            cp "$mql_local" "${mql_local}.bak"
        else
            log_warn "mql.local already exists. Use --force to overwrite."
            # Continue - mql.local is not critical
        fi
    fi

    # Write mql.local (always if --force or if it doesn't exist)
    if [[ ! -f "$mql_local" ]] || [[ "$force" -eq 1 ]]; then
        cat > "$mql_local" << EOF
# mql.local - User overrides (auto-generated by mql init)
MQL_ROOTFS=$MQL_ROOTFS
EOF
        log_ok "Generated mql.local with MQL_ROOTFS=$MQL_ROOTFS"
    fi

    # ----------------------------------------------------------------
    # B1 + B2 + B3: NixOS systemd service generation
    # ----------------------------------------------------------------
    if is_nixos; then
        _init_nixos_service "$MQL_ROOTFS" "$force"
    fi

    # ----------------------------------------------------------------
    # B4 + D1: Print next-step instructions
    # ----------------------------------------------------------------
    _init_print_next_steps

    log_ok "Init complete!"
    return 0
}

# ============================================================================
# Helper functions
# ============================================================================

_init_usage() {
    cat << 'EOF'
Usage: mql init --from-file <tarball> [--rootfs <path>] [--force]

Initialize Maqui Linux developer environment from a rootfs tarball.

Arguments:
  --from-file <path>   Path to rootfs tarball (.tar.gz or .tar.xz) [required]
  --rootfs <path>      Override target directory (default: /mnt/maquilinux)
  --force              Overwrite existing base/ and mql.local

Examples:
  mql init --from-file ~/Downloads/maquiroot.tar.xz
  mql init --from-file /tmp/rootfs.tar.gz --rootfs /mnt/custom
  mql init --from-file rootfs.tar.xz --force
EOF
}

# _init_nixos_service <rootfs> <force>
# Offer to generate a systemd user service for auto-mounting the overlay on NixOS.
_init_nixos_service() {
    local rootfs="$1"
    local force="$2"
    local service_dir="$HOME/.config/systemd/user"
    local service_file="$service_dir/maquilinux-mounts.service"

    log_step "NixOS detected"

    if [[ -f "$service_file" ]] && [[ "$force" -eq 0 ]]; then
        log_warn "Systemd service already exists at $service_file"
        log_info "Use --force to regenerate"
        return 0
    fi

    if confirm "Create systemd auto-mount service?"; then
        mkdir -p "$service_dir"

        cat > "$service_file" << SVCEOF
[Unit]
Description=Maqui Linux overlay mounts
After=local-fs.target

[Service]
Type=oneshot
RemainAfterExit=yes
Environment=PATH=/run/current-system/sw/bin:/usr/bin:/bin
ExecStart=/bin/bash -c '\
  rootfs="$rootfs"; \
  mkdir -p "\$rootfs"/{base,layers/upper,layers/work,merged,repo}; \
  if ! mountpoint -q "\$rootfs/merged" 2>/dev/null; then \
    mount -t overlay overlay \
      -o "lowerdir=\$rootfs/base,upperdir=\$rootfs/layers/upper,workdir=\$rootfs/layers/work" \
      "\$rootfs/merged"; \
  fi; \
  for mp in proc dev dev/pts sys run dev/shm; do \
    if ! mountpoint -q "\$rootfs/merged/\$mp" 2>/dev/null; then \
      case "\$mp" in \
        proc)    mount -t proc proc "\$rootfs/merged/proc" ;; \
        dev)     mount --bind /dev "\$rootfs/merged/dev" ;; \
        dev/pts) mount -t devpts devpts "\$rootfs/merged/dev/pts" ;; \
        sys)     mount --bind /sys "\$rootfs/merged/sys" ;; \
        run)     mount -t tmpfs tmpfs "\$rootfs/merged/run" ;; \
        dev/shm) mount --bind /dev/shm "\$rootfs/merged/dev/shm" ;; \
      esac; \
    fi; \
  done'

ExecStop=/bin/bash -c '\
  rootfs="$rootfs"; \
  for mp in "\$rootfs/merged/mnt/repo" "\$rootfs/merged/mnt/workspace" \
            "\$rootfs/merged/dev/shm" "\$rootfs/merged/dev/pts" \
            "\$rootfs/merged/run" "\$rootfs/merged/sys" \
            "\$rootfs/merged/proc" "\$rootfs/merged/dev" \
            "\$rootfs/merged"; do \
    if mountpoint -q "\$mp" 2>/dev/null; then \
      umount -l "\$mp" 2>/dev/null || true; \
    fi; \
  done'

[Install]
WantedBy=default.target
SVCEOF

        # Enable linger for user services to run at boot
        local sudo_cmd
        sudo_cmd="$(find_sudo)" || true
        if [[ -n "$sudo_cmd" ]]; then
            "$sudo_cmd" loginctl enable-linger "$(whoami)" 2>/dev/null || true
        fi

        systemctl --user daemon-reload 2>/dev/null || true
        systemctl --user enable maquilinux-mounts.service 2>/dev/null || true

        log_ok "Auto-mount service installed at $service_file"
        log_info "Overlay will auto-mount on next boot"
    else
        log_info "Skipping service creation"
        _init_manual_mount_instructions
    fi
}

# _init_manual_mount_instructions
# Print manual mount instructions for non-NixOS or declined service.
_init_manual_mount_instructions() {
    echo ""
    log_info "Manual mount instructions (run after each reboot):"
    echo "  sudo mql chroot --mount"
    echo ""
}

# _init_print_next_steps
# Print context-aware next-step instructions after successful init.
_init_print_next_steps() {
    local rootfs="${MQL_ROOTFS:-/mnt/maquilinux}"

    echo ""
    echo "========================================"
    echo "  Init complete! Next steps:"
    echo "========================================"
    echo ""

    if is_nixos; then
        echo "  1. Mount overlay:  mql chroot --mount"
        echo "  2. Enter chroot:   mql chroot"
        echo "  3. Build a spec:   mql build SPECS/<name>.spec"
        echo "  4. Install it:     mql install SPECS/<name>.spec"
        echo ""
        echo "  The overlay will auto-mount on next boot."
    else
        echo "  1. Mount overlay:  sudo mql chroot --mount"
        echo "  2. Enter chroot:   mql chroot"
        echo "  3. Build a spec:   mql build SPECS/<name>.spec"
        echo "  4. Install it:     mql install SPECS/<name>.spec"
        echo ""
        echo "  NOTE: You must mount the overlay after each reboot."
        echo "  Run 'mql chroot --mount' or set up auto-mount for your distro."
    fi

    echo ""
    echo "  Configuration:     mql config"
    echo "  Edit overrides:    $MQL_PROJECT_ROOT/mql.local"
    echo ""
}
