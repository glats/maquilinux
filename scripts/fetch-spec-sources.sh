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

# Extract sources from spec
# Supports two formats:
#   1. SourceN: URL (or URL -> local-name) - URL is the source
#   2. # Download URL: URL followed by SourceN: filename - comment has URL

# Get line numbers of Source definitions
source_lines=$(grep -n -E '^Source[0-9]*:' "$SPEC_FILE" 2>/dev/null | cut -d: -f1 || true)

if [ -z "$source_lines" ]; then
    log_info "No external sources defined in spec"
    exit 0
fi

log_info "Found $(echo "$source_lines" | wc -l) source(s) to process"

# Process each source by line number
while IFS= read -r line_num; do
    [ -z "$line_num" ] && continue
    
    # Get the Source line content
    source_line=$(sed -n "${line_num}p" "$SPEC_FILE" | sed -E 's/^Source[0-9]*:[[:space:]]+//')
    
    log_info "Processing: $source_line"
    
    # Check if source_line is a URL or just a filename
    if echo "$source_line" | grep -Eq '^https?://|^ftp://'; then
        # Format 1: URL directly in Source
        if echo "$source_line" | grep -q -- '->'; then
            # Has local rename: URL -> local-name
            url=$(echo "$source_line" | sed -E 's/[[:space:]]*->.*$//' | xargs)
            local_name=$(echo "$source_line" | sed -E 's/^.*->[[:space:]]*//' | xargs)
            log_info "  Parsed: URL=$url, local_name=$local_name"
        else
            # No rename: extract filename from URL
            url=$(echo "$source_line" | xargs)
            local_name=$(basename "$url" | sed 's/?.*$//')  # Remove query params
            log_info "  Parsed: URL=$url, local_name=$local_name (from basename)"
        fi
    else
        # Format 2: filename in Source, look for URL in preceding comment
        local_name=$(echo "$source_line" | xargs)
        
        # Look for "# Download URL:" comment on previous line(s)
        url=$(sed -n "$((line_num - 1))p" "$SPEC_FILE" | grep -E '^#[[:space:]]*Download URL:' | sed -E 's/^#[[:space:]]*Download URL:[[:space:]]+//' | xargs)
        
        if [ -z "$url" ]; then
            log_warn "  Cannot find download URL for $local_name (no preceding # Download URL: comment)"
            continue
        fi
        
        log_info "  Parsed from comment: URL=$url, local_name=$local_name"
    fi
    
    # Skip if no valid URL
    if ! echo "$url" | grep -Eq '^https?://|^ftp://'; then
        log_warn "Skipping invalid URL for $local_name: $url"
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
done <<< "$source_lines"

log_info "All sources ready for: $SPEC_NAME"
