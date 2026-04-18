#!/usr/bin/env bash
set -euo pipefail

# Download rust stage0 bootstrap binary for Maqui Linux
# This script downloads the x86_64 stage0 binary (rustc-1.75.0-x86_64-unknown-linux-gnu.tar.xz)
# into SOURCES/, verifying its SHA256 checksum.
# It is idempotent: if the file already exists with correct checksum, it skips.

# Workspace root (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOPDIR="$(dirname "$SCRIPT_DIR")"
SOURCES_DIR="$TOPDIR/SOURCES"

RUST_VERSION="1.75.0"
STAGE0_FILENAME="rustc-${RUST_VERSION}-x86_64-unknown-linux-gnu.tar.xz"
STAGE0_URL="https://static.rust-lang.org/dist/${STAGE0_FILENAME}"
EXPECTED_SHA256="2824ba4045acdddfa436da4f0bb72807b64a089aa2e7c9a66ca1a3a571114ce7"

# Ensure SOURCES directory exists
mkdir -p "$SOURCES_DIR"

# Function to compute SHA256
sha256_file() {
    sha256sum "$1" | cut -d ' ' -f1
}

# Check if file already exists and matches checksum
if [[ -f "$SOURCES_DIR/$STAGE0_FILENAME" ]]; then
    echo "[download] Found existing stage0 binary: $STAGE0_FILENAME"
    ACTUAL_SHA256=$(sha256_file "$SOURCES_DIR/$STAGE0_FILENAME")
    if [[ "$ACTUAL_SHA256" == "$EXPECTED_SHA256" ]]; then
        echo "[download] SHA256 matches, nothing to do."
        exit 0
    else
        echo "[download] SHA256 mismatch! Expected: $EXPECTED_SHA256"
        echo "[download] Actual:   $ACTUAL_SHA256"
        echo "[download] Removing corrupted file."
        rm -f "$SOURCES_DIR/$STAGE0_FILENAME"
    fi
fi

# Download with curl, follow redirects, show progress
echo "[download] Downloading stage0 binary from $STAGE0_URL"
if ! curl -L --fail --progress-bar "$STAGE0_URL" -o "$SOURCES_DIR/$STAGE0_FILENAME.tmp"; then
    echo "[download] ERROR: Download failed."
    exit 1
fi

# Verify checksum
echo "[download] Verifying SHA256..."
ACTUAL_SHA256=$(sha256_file "$SOURCES_DIR/$STAGE0_FILENAME.tmp")
if [[ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]]; then
    echo "[download] ERROR: SHA256 mismatch after download."
    echo "[download] Expected: $EXPECTED_SHA256"
    echo "[download] Actual:   $ACTUAL_SHA256"
    rm -f "$SOURCES_DIR/$STAGE0_FILENAME.tmp"
    exit 1
fi

# Move temporary file to final location
mv "$SOURCES_DIR/$STAGE0_FILENAME.tmp" "$SOURCES_DIR/$STAGE0_FILENAME"
echo "[download] Successfully downloaded and verified $STAGE0_FILENAME"
echo "[download] File saved to $SOURCES_DIR/$STAGE0_FILENAME"