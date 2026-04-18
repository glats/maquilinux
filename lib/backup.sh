#!/usr/bin/env bash
# lib/backup.sh - Incremental backup system for Maqui Linux rootfs (museum/archive style)
#
# Philosophy: Preserve complete history. Never delete backups.
# Like a museum of distro evolution.

set -euo pipefail

# Guard against multiple sourcing
if [[ -n "${MQL_BACKUP_SOURCED:-}" ]]; then
    return 0
fi
readonly MQL_BACKUP_SOURCED=1

# Load common functions
source "$MQL_PROJECT_ROOT/lib/common.sh"

# Configuration
MQL_BACKUP_DIR="${MQL_BACKUP_DIR:-$HOME/maqui-backups}"
readonly MQL_BACKUP_DIR

# Archive location (cold storage - historical)
MQL_ARCHIVE_DIR="${MQL_ARCHIVE_DIR:-$HOME/maqui-archive}"
readonly MQL_ARCHIVE_DIR

# Backup naming
readonly BACKUP_PREFIX="maquilinux"
readonly BACKUP_SUFFIX="tar.xz"

# Helper Functions
get_base_dir() {
    local lfs
    lfs="$(get_lfs_path)"
    echo "$lfs/base"
}

check_base_dir() {
    local base_dir
    base_dir="$(get_base_dir)"
    if [[ ! -d "$base_dir" ]]; then
        log_error "Base directory not found: $base_dir"
        return 1
    fi
}

ensure_backup_dirs() {
    mkdir -p "$MQL_BACKUP_DIR"
    mkdir -p "$MQL_ARCHIVE_DIR" 2>/dev/null || true
}

# Capture git state for metadata
capture_git_state() {
    local git_commit="unknown"
    local git_branch="unknown"
    
    if [[ -d "$MQL_PROJECT_ROOT/.git" ]]; then
        git_commit="$(cd "$MQL_PROJECT_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
        git_branch="$(cd "$MQL_PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
    fi
    
    echo "commit:${git_commit},branch:${git_branch}"
}

# Create backup with metadata
backup_create() {
    local tag="${1:-manual}"
    
    check_base_dir || return 1
    ensure_backup_dirs
    
    local base_dir
    base_dir="$(get_base_dir)"
    
    local timestamp
    timestamp="$(date +%Y%m%d-%H%M%S)"
    
    local backup_name="${BACKUP_PREFIX}-${timestamp}-${tag}.${BACKUP_SUFFIX}"
    local backup_path="$MQL_BACKUP_DIR/$backup_name"
    
    log_step "Creating backup: $backup_name"
    log_info "Source: $base_dir"
    
    # Create tar.xz backup
    if tar -cJf "$backup_path" -C "$base_dir" . 2>/dev/null; then
        log_ok "Backup created: $backup_path"
    else
        log_error "Backup creation failed"
        return 1
    fi
    
    # Create metadata file
    local size_human
    size_human="$(du -h "$backup_path" | cut -f1)"
    
    local git_info
    git_info="$(capture_git_state)"
    
    cat > "${backup_path}.meta" <<EOF
# Maqui Linux Backup Metadata
timestamp: $(date -Iseconds)
tag: $tag
size: $size_human
git: $git_info
hostname: $(hostname)
EOF
    
    log_ok "Metadata saved: ${backup_path}.meta"
    log_info "Size: $size_human"
}

# List all backups
backup_list() {
    ensure_backup_dirs
    
    log_step "Maqui Linux Rootfs Archive (Museum Collection)"
    
    if [[ ! -d "$MQL_BACKUP_DIR" ]] || [[ -z "$(ls -A "$MQL_BACKUP_DIR"/*.tar.xz 2>/dev/null)" ]]; then
        log_info "No backups found"
        return 0
    fi
    
    printf "%-40s %-10s %s\n" "BACKUP" "SIZE" "TAG"
    printf "%-40s %-10s %s\n" "$(printf '%0.s-' {1..40})" "$(printf '%0.s-' {1..10})" "$(printf '%0.s-' {1..20})"
    
    for backup in "$MQL_BACKUP_DIR/${BACKUP_PREFIX}"-*.tar.xz; do
        [[ -f "$backup" ]] || continue
        
        local name size tag
        name="$(basename "$backup")"
        size="$(du -h "$backup" 2>/dev/null | cut -f1 || echo 'unknown')"
        tag="$(echo "$name" | sed -E "s/^${BACKUP_PREFIX}-[0-9]{8}-[0-9]{6}-(.+)\.${BACKUP_SUFFIX}$/\1/")"
        
        printf "%-40s %-10s %s\n" "$name" "$size" "$tag"
    done
}

# Restore from backup
backup_restore() {
    local name="${1:-}"
    
    if [[ -z "$name" ]]; then
        log_error "Usage: mql backup restore <backup-name>"
        return 1
    fi
    
    check_base_dir || return 1
    
    local backup_path
    if [[ -f "$name" ]]; then
        backup_path="$name"
    elif [[ -f "$MQL_BACKUP_DIR/$name" ]]; then
        backup_path="$MQL_BACKUP_DIR/$name"
    else
        # Try to find
        backup_path="$(find "$MQL_BACKUP_DIR" -name "*${name}*.tar.xz" -print -quit 2>/dev/null)"
        if [[ -z "$backup_path" ]]; then
            log_error "Backup not found: $name"
            return 1
        fi
    fi
    
    log_step "Restoring: $(basename "$backup_path")"
    log_warn "This will OVERWRITE the current base rootfs!"
    
    local base_dir parent_dir
    base_dir="$(get_base_dir)"
    parent_dir="$(dirname "$base_dir")"
    
    # Remove existing
    if [[ -d "$base_dir" ]]; then
        rm -rf "$base_dir"
    fi
    
    mkdir -p "$base_dir"
    
    # Extract
    if tar -xJf "$backup_path" -C "$parent_dir"; then
        log_ok "Restored successfully"
    else
        log_error "Restore failed"
        return 1
    fi
}

# Archive to cold storage
backup_archive() {
    local days="${1:-90}"
    
    ensure_backup_dirs
    
    log_step "Archiving backups older than $days days"
    
    local cutoff archived
    cutoff="$(date -d "$days days ago" +%s 2>/dev/null || echo 0)"
    archived=0
    
    for backup in "$MQL_BACKUP_DIR/${BACKUP_PREFIX}"-*.tar.xz; do
        [[ -f "$backup" ]] || continue
        
        local mtime
        mtime="$(stat -c '%Y' "$backup" 2>/dev/null || stat -f '%m' "$backup" 2>/dev/null || echo 0)"
        
        if [[ $mtime -lt $cutoff ]]; then
            local bname
            bname="$(basename "$backup")"
            
            log_info "Archiving: $bname"
            mv "$backup" "$MQL_ARCHIVE_DIR/"
            [[ -f "${backup}.meta" ]] && mv "${backup}.meta" "$MQL_ARCHIVE_DIR/"
            ((archived++))
        fi
    done
    
    log_ok "Archived: $archived backups"
}

# Show archive contents
backup_archive_list() {
    if [[ ! -d "$MQL_ARCHIVE_DIR" ]] || [[ -z "$(ls -A "$MQL_ARCHIVE_DIR"/*.tar.xz 2>/dev/null)" ]]; then
        log_info "Archive is empty"
        return
    fi
    
    log_step "Cold Storage Archive"
    printf "%-40s %s\n" "BACKUP" "SIZE"
    
    for backup in "$MQL_ARCHIVE_DIR/${BACKUP_PREFIX}"-*.tar.xz; do
        [[ -f "$backup" ]] || continue
        printf "%-40s %s\n" "$(basename "$backup")" "$(du -h "$backup" | cut -f1)"
    done
}

# Museum view - all backups
backup_museum() {
    backup_list
    echo ""
    backup_archive_list
    
    local hot_size cold_size
    hot_size="$(du -sh "$MQL_BACKUP_DIR" 2>/dev/null | cut -f1 || echo '0')"
    cold_size="$(du -sh "$MQL_ARCHIVE_DIR" 2>/dev/null | cut -f1 || echo '0')"
    
    echo ""
    log_info "Hot storage:  $hot_size"
    log_info "Cold storage: $cold_size"
    log_info "Total: $(du -sh "$MQL_BACKUP_DIR" "$MQL_ARCHIVE_DIR" 2>/dev/null | tail -1 | cut -f1 || echo 'unknown')"
}

# CLI dispatcher
mql_backup() {
    local subcmd="${1:-}"
    shift || true
    
    case "$subcmd" in
        create)
            backup_create "$@"
            ;;
        list)
            backup_list "$@"
            ;;
        restore)
            backup_restore "$@"
            ;;
        archive)
            backup_archive "$@"
            ;;
        archive-list)
            backup_archive_list "$@"
            ;;
        museum)
            backup_museum "$@"
            ;;
        *)
            echo "Usage: mql backup {create|list|restore|archive|archive-list|museum}"
            echo ""
            echo "Philosophy: Never delete backups. Archive to cold storage."
            return 1
            ;;
    esac
}

# EOF
