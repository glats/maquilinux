#!/usr/bin/env bash
# scripts/publish-rootfs.sh - Publish rootfs backup to maquiroot server
#
# Usage: ./publish-rootfs.sh <backup-file> [tag]
#
# Example:
#   ./publish-rootfs.sh ~/maqui-backups/maquilinux-20260418-150000-post-rust.tar.xz latest
#   ./publish-rootfs.sh ~/maqui-backups/maquilinux-20260418-150000-base.tar.xz 2026-04-18

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
PUBLISH_HOST="${MAQUIROOT_HOST:-maquiroot.glats.org}"
PUBLISH_USER="${MAQUIROOT_USER:-root}"
PUBLISH_BASE_DIR="${MAQUIROOT_DIR:-/var/www/maquiroot}"
LATEST_LINK="${PUBLISH_BASE_DIR}/latest"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Check arguments
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <backup-file.tar.xz> [tag]"
    echo ""
    echo "Tags:"
    echo "  latest    - Update the 'latest' symlink (default if omitted)"
    echo "  YYYY-MM-DD - Archive in dated directory"
    echo "  bootstrap - Minimal bootstrap rootfs"
    echo ""
    echo "Environment:"
    echo "  MAQUIROOT_HOST    - SSH host (default: maquiroot.glats.org)"
    echo "  MAQUIROOT_USER    - SSH user (default: root)"
    echo "  MAQUIROOT_DIR     - Server directory (default: /var/www/maquiroot)"
    exit 1
fi

BACKUP_FILE="$1"
TAG="${2:-latest}"

# Verify backup exists
if [[ ! -f "$BACKUP_FILE" ]]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Verify it's a valid tar.xz
if [[ ! "$BACKUP_FILE" == *.tar.xz ]]; then
    log_error "File must be .tar.xz format"
    exit 1
fi

# Get metadata file
META_FILE="${BACKUP_FILE}.meta"
if [[ ! -f "$META_FILE" ]]; then
    log_warn "Metadata file not found: $META_FILE"
    log_warn "Creating minimal metadata..."
    cat > "$META_FILE" << EOF
timestamp: $(date -Iseconds)
tag: $TAG
size: $(du -h "$BACKUP_FILE" | cut -f1)
hostname: $(hostname)
EOF
fi

# Extract date from filename for dated archive
FILENAME="$(basename "$BACKUP_FILE")"
if [[ "$FILENAME" =~ maquilinux-([0-9]{8})-([0-9]{6}) ]]; then
    DATE_STR="${BASH_REMATCH[1]}"
    FORMATTED_DATE="${DATE_STR:0:4}-${DATE_STR:4:2}-${DATE_STR:6:2}"
else
    FORMATTED_DATE="$(date +%Y-%m-%d)"
fi

# Determine destination
if [[ "$TAG" == "latest" ]]; then
    DEST_DIR="$PUBLISH_BASE_DIR/latest"
    DEST_FILENAME="maquilinux-rootfs-latest.tar.xz"
elif [[ "$TAG" == "bootstrap" ]]; then
    DEST_DIR="$PUBLISH_BASE_DIR/bootstrap"
    DEST_FILENAME="maquilinux-bootstrap.tar.xz"
else
    # Dated archive
    DEST_DIR="$PUBLISH_BASE_DIR/$FORMATTED_DATE"
    DEST_FILENAME="$FILENAME"
fi

log_info "Publishing to $PUBLISH_USER@$PUBLISH_HOST:$DEST_DIR/"
log_info "File: $DEST_FILENAME"
log_info "Size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Create remote directory
ssh "${PUBLISH_USER}@${PUBLISH_HOST}" "mkdir -p $DEST_DIR"

# Calculate checksum locally
log_info "Calculating SHA256..."
CHECKSUM="$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)"
log_info "Checksum: $CHECKSUM"

# Create metadata JSON
cat > /tmp/publish-meta.json << EOF
{
  "filename": "$DEST_FILENAME",
  "sha256": "$CHECKSUM",
  "tag": "$TAG",
  "published_at": "$(date -Iseconds)",
  "bytes": $(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null || echo 0),
  "source_metadata": $(cat "$META_FILE" 2>/dev/null | python3 -c 'import json,sys,datetime; d={}; exec(sys.stdin.read()) if "=" in sys.stdin.read() else None; print(json.dumps(d))' 2>/dev/null || echo '{}')
}
EOF

# Upload using rsync for resume support
log_info "Uploading (resumable)..."
rsync --partial --progress \
  "$BACKUP_FILE" \
  "${PUBLISH_USER}@${PUBLISH_HOST}:${DEST_DIR}/${DEST_FILENAME}.tmp"

# Upload checksum
log_info "Uploading checksum..."
echo "$CHECKSUM  $DEST_FILENAME" > /tmp/checksum.txt
scp /tmp/checksum.txt "${PUBLISH_USER}@${PUBLISH_HOST}:${DEST_DIR}/${DEST_FILENAME}.sha256"

# Upload metadata
log_info "Uploading metadata..."
scp /tmp/publish-meta.json "${PUBLISH_USER}@${PUBLISH_HOST}:${DEST_DIR}/metadata.json"

# Atomic move (remove old if latest, then move new)
log_info "Finalizing..."
ssh "${PUBLISH_USER}@${PUBLISH_HOST}" << EOF
    cd "$DEST_DIR"
    
    # Remove old file if this is latest
    if [[ "$TAG" == "latest" ]] && [[ -f "$DEST_FILENAME" ]]; then
        rm -f "$DEST_FILENAME"
    fi
    
    # Atomic move
    mv "${DEST_FILENAME}.tmp" "$DEST_FILENAME"
    
    # Set permissions
    chmod 644 "$DEST_FILENAME"
    chmod 644 "${DEST_FILENAME}.sha256" 2>/dev/null || true
    chmod 644 metadata.json 2>/dev/null || true
    
    # Update index
    $PUBLISH_BASE_DIR/../scripts/update-index.sh
    
    echo "Published successfully"
EOF

# Cleanup
rm -f /tmp/publish-meta.json /tmp/checksum.txt

log_info "Published: https://${PUBLISH_HOST}/${TAG}/${DEST_FILENAME}"
log_info "Checksum: $CHECKSUM"

# If this is a dated archive, also offer to update latest
if [[ "$TAG" == "$FORMATTED_DATE" ]] && [[ -z "${2:-}" ]]; then
    log_info ""
    log_info "To make this the 'latest' release:"
    log_info "  $0 $BACKUP_FILE latest"
fi

exit 0
