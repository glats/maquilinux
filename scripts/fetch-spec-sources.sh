#!/usr/bin/env bash
# scripts/fetch-spec-sources.sh - Download source tarballs for a spec
#
# Usage: ./fetch-spec-sources.sh <spec-name>
# Example: ./fetch-spec-sources.sh rust
#          ./fetch-spec-sources.sh bash
#
# This script reads Source* lines from the spec and downloads
# any missing tarballs to SOURCES/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
SOURCES_DIR="$WORKSPACE/SOURCES"
SPECS_DIR="$WORKSPACE/SPECS"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[fetch]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[fetch]${NC} $1"; }
log_error() { echo -e "${RED}[fetch]${NC} $1"; }

# Ensure SOURCES directory exists
mkdir -p "$SOURCES_DIR"

# Get spec file
SPEC_NAME="${1:-}"
if [ -z "$SPEC_NAME" ]; then
    log_error "Usage: $0 <spec-name>"
    exit 1
fi

SPEC_FILE="$SPECS_DIR/${SPEC_NAME}.spec"
if [ ! -f "$SPEC_FILE" ]; then
    log_error "Spec not found: $SPEC_FILE"
    exit 1
fi

log_info "Checking sources for: $SPEC_NAME"

# Expand RPM macros in spec to get actual URLs
# Use rpmspec -P to parse and expand, then grep sources
if command -v rpmspec >/dev/null 2>&1; then
    # Expand macros
    expanded_spec=$(rpmspec -P "$SPEC_FILE" 2>/dev/null || cat "$SPEC_FILE")
else
    # Fallback: just cat the spec (macros won't expand)
    expanded_spec=$(cat "$SPEC_FILE")
    log_warn "rpmspec not available, macros won't be expanded"
fi

# Extract Source* URLs from expanded spec
# Format: SourceN: URL (optionally -> local-name)
sources=$(echo "$expanded_spec" | grep -E '^Source[0-9]*:' | sed -E 's/^Source[0-9]*:[[:space:]]+//' || true)

if [ -z "$sources" ]; then
    log_info "No external sources defined in spec"
    exit 0
fi

# Process each source
while IFS= read -r source_line; do
    [ -z "$source_line" ] && continue
    
    # Parse: URL or URL -> local-name
    if echo "$source_line" | grep -q '->'; then
        # Has local rename: URL -> local-name
        url=$(echo "$source_line" | sed -E 's/[[:space:]]*->.*$//' | xargs)
        local_name=$(echo "$source_line" | sed -E 's/^.*->[[:space:]]*//' | xargs)
    else
        # No rename: extract filename from URL
        url=$(echo "$source_line" | xargs)
        local_name=$(basename "$url" | sed 's/?.*$//')  # Remove query params
    fi
    
    # Skip if not HTTP(S) or FTP
    if ! echo "$url" | grep -Eq '^https?://|^ftp://'; then
        log_warn "Skipping non-URL source: $url"
        continue
    fi
    
    target_file="$SOURCES_DIR/$local_name"
    
    # Check if already exists
    if [ -f "$target_file" ]; then
        log_info "Already present: $local_name"
        continue
    fi
    
    # Download
    log_info "Downloading: $local_name"
    log_info "  From: $url"
    
    if curl -L --fail --progress-bar -o "$target_file.tmp" "$url"; then
        mv "$target_file.tmp" "$target_file"
        log_info "  Saved: $local_name"
    else
        log_error "  Failed to download: $url"
        rm -f "$target_file.tmp"
        exit 1
    fi
done <<< "$sources"

log_info "All sources ready for: $SPEC_NAME"
