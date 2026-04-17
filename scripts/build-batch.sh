#!/usr/bin/env bash
# build-batch.sh - Build a batch of specs
#
# Usage:
#   ./build-batch.sh spec1 spec2 spec3 ...

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$WORKSPACE/logs"

mkdir -p "$LOG_DIR"

for spec in "$@"; do
    spec_file="$WORKSPACE/SPECS/${spec}.spec"
    
    if [[ ! -f "$spec_file" ]]; then
        echo "SKIP: $spec (spec not found)"
        continue
    fi
    
    # Check if already built
    existing=$(ls "$WORKSPACE"/RPMS/*/${spec}-*.rpm 2>/dev/null | head -1 || true)
    
    if [[ -n "$existing" ]]; then
        echo "SKIP: $spec (already built)"
        continue
    fi
    
    log_file="$LOG_DIR/${spec}.log"
    
    echo "Building: $spec"
    echo "$(date): Building $spec" > "$log_file"
    
    if sudo "$SCRIPT_DIR/enter-chroot-build.sh" -c "cd /workspace && rpmbuild -ba SPECS/${spec}.spec --define '_topdir /workspace' --nodeps 2>&1" >> "$log_file" 2>&1; then
        echo "  OK: $spec"
        echo "$(date): SUCCESS" >> "$log_file"
    else
        echo "  FAIL: $spec (see $log_file)"
        echo "$(date): FAILED" >> "$log_file"
    fi
done
