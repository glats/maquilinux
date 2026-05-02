#!/usr/bin/env bash
# lib/repo.sh - Repository management for Maqui Linux

set -euo pipefail

# Guard against multiple sourcing
if [[ -n "${MQL_REPO_SOURCED:-}" ]]; then
    return 0
fi
readonly MQL_REPO_SOURCED=1

# Load common functions
source "$MQL_PROJECT_ROOT/lib/common.sh"

# ============================================================================
# Repo Functions
# ============================================================================

# mql_repo_update [arch]
# Regenerate repo metadata for x86_64 and/or i686.
# arch: x86_64 | i686 | both (default: both)
mql_repo_update() {
    local arch="${1:-both}"

    check_repo_deps

    local rpms_dir="$MQL_PROJECT_ROOT/RPMS"

    update_arch() {
        local a="$1"
        local dir="$rpms_dir/$a"
        if [[ ! -d "$dir" ]]; then
            log_warn "RPMS/$a not found — skipping"
            return 0
        fi
        log_step "Updating repo metadata: $dir"
        createrepo_c --update "$dir"
        log_ok "Metadata updated: $a"
    }

    case "$arch" in
        x86_64) update_arch x86_64 ;;
        i686)   update_arch i686   ;;
        both|*) update_arch x86_64; update_arch i686 ;;
    esac
}

# mql_repo_list
# Print table of all RPMs with arch column and total count.
mql_repo_list() {
    local rpms_dir="$MQL_PROJECT_ROOT/RPMS"

    if [[ ! -d "$rpms_dir" ]]; then
        log_error "RPMS/ directory not found: $rpms_dir"
        return 1
    fi

    local total=0
    printf "%-50s %s\n" "PACKAGE" "ARCH"
    printf "%-50s %s\n" "$(printf '%0.s-' {1..50})" "--------"

    for arch_dir in "$rpms_dir"/*/; do
        local arch
        arch="$(basename "$arch_dir")"
        [[ "$arch" == "repodata" ]] && continue

        for rpm in "$arch_dir"*.rpm; do
            [[ -f "$rpm" ]] || continue
            printf "%-50s %s\n" "$(basename "$rpm")" "$arch"
            ((total++))
        done
    done

    echo ""
    log_info "Total: $total package(s)"
}

# mql_repo_sync
# Update metadata then rsync to MQL_REPO_DEST.
mql_repo_sync() {
    local dest
    dest="$(get_repo_dest)"

    if [[ -z "${MQL_REPO_DEST:-}" ]]; then
        log_warn "MQL_REPO_DEST not set — syncing to default: $dest"
    fi

    log_step "Syncing to $dest"

    # Update metadata first
    mql_repo_update

    if [[ ! -d "$MQL_PROJECT_ROOT/RPMS" ]]; then
        log_error "RPMS/ directory not found"
        return 1
    fi

    # Create destination if local path
    if [[ "$dest" != *:* ]]; then
        mkdir -p "$dest"
    fi

    rsync -avz --delete "$MQL_PROJECT_ROOT/RPMS/" "$dest/"
    log_ok "Sync complete: $dest"
}

# ============================================================================
# CLI Dispatcher
# ============================================================================

mql_repo() {
    local subcmd="${1:-}"
    shift || true

    case "$subcmd" in
        update)
            mql_repo_update "$@"
            ;;
        list)
            mql_repo_list "$@"
            ;;
        sync)
            mql_repo_sync "$@"
            ;;
        --help|-h|"")
            echo "Usage: mql repo {update|list|sync}"
            echo ""
            echo "  update [arch]  Regenerate createrepo_c metadata (x86_64|i686|both)"
            echo "  list           List all RPMs in RPMS/"
            echo "  sync           Update metadata and rsync to MQL_REPO_DEST"
            return 1
            ;;
        *)
            log_error "Unknown repo subcommand: $subcmd"
            return 1
            ;;
    esac
}

# EOF
