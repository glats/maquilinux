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

# Function to expand RPM macros in spec content
expand_spec_macros() {
    local spec_file="$1"
    local expanded_content=""
    
    # Try rpmspec first (best option, expands all macros)
    if command -v rpmspec &> /dev/null; then
        expanded_content=$(rpmspec -P "$spec_file" 2>/dev/null) || true
    fi
    
    if [ -n "$expanded_content" ]; then
        echo "$expanded_content"
        return 0
    fi
    
    # Fallback: manual expansion of common macros
    # Extract common macro values from the spec
    local name version release
    name=$(grep -E '^Name:' "$spec_file" | head -1 | sed -E 's/^Name:[[:space:]]+//' | xargs)
    version=$(grep -E '^Version:' "$spec_file" | head -1 | sed -E 's/^Version:[[:space:]]+//' | xargs)
    release=$(grep -E '^Release:' "$spec_file" | head -1 | sed -E 's/^Release:[[:space:]]+//' | xargs | sed 's/%{.*$//')
    
    # Read spec and expand macros
    while IFS= read -r line; do
        # Expand %{name}, %{version}, %{release}, %{?_isa}, etc.
        line=$(echo "$line" | sed "s/%{name}/$name/g")
        line=$(echo "$line" | sed "s/%{version}/$version/g")
        line=$(echo "$line" | sed "s/%{release}/$release/g")
        line=$(echo "$line" | sed 's/%{[?]*_isa}//g')
        line=$(echo "$line" | sed 's/%{[?]*dist}//g')
        line=$(echo "$line" | sed 's/%{__.*}//g')  # Remove %{__macro} constructs
        echo "$line"
    done < "$spec_file"
}

log_info "Expanding macros in spec..."
expanded_spec=$(expand_spec_macros "$SPEC_FILE")

# Extract sources from expanded spec
# Supports two formats:
#   1. SourceN: URL (or URL -> local-name) - URL is the source
#   2. # Download URL: URL followed by SourceN: filename - comment has URL

# Get line numbers of Source definitions from expanded content
source_lines=$(echo "$expanded_spec" | grep -n -E '^Source[0-9]*:' | cut -d: -f1 || true)

if [ -z "$source_lines" ]; then
    log_info "No external sources defined in spec"
    exit 0
fi

log_info "Found $(echo "$source_lines" | wc -l) source(s) to process"

# Process each source by line number
while IFS= read -r line_num; do
    [ -z "$line_num" ] && continue
    
    # Get the Source line content from expanded spec
    source_line=$(echo "$expanded_spec" | sed -n "${line_num}p" | sed -E 's/^Source[0-9]*:[[:space:]]+//')
    
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
        # Format 2: filename in Source, look for URL in preceding comment (in ORIGINAL spec)
        local_name=$(echo "$source_line" | xargs)
        
        # Look for "# Download URL:" comment on previous line(s) in original spec
        url=$(sed -n "$((line_num - 1))p" "$SPEC_FILE" | grep -E '^#[[:space:]]*Download URL:' | sed -E 's/^#[[:space:]]*Download URL:[[:space:]]+//' | xargs)
        
        # If not found in comment, check if the expanded source_line is a URL
        if [ -z "$url" ]; then
            # Check if it's a URL pattern (starts with http/https/ftp)
            if echo "$source_line" | grep -Eq '^https?://|^ftp://'; then
                # It's a URL after macro expansion! Extract filename from URL
                url=$(echo "$source_line" | xargs)
                local_name=$(basename "$url" | sed 's/?.*$//')
                log_info "  Parsed from expanded URL: URL=$url, local_name=$local_name"
            else
                log_warn "  Cannot find download URL for $local_name (no preceding # Download URL: comment, and not a URL)"
                log_warn "  Expanded source_line was: $source_line"
                continue
            fi
        else
            log_info "  Parsed from comment: URL=$url, local_name=$local_name"
        fi
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
