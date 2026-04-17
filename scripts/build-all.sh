#!/usr/bin/env bash
# build-all.sh - Build all specs in the workspace
#
# Usage:
#   ./build-all.sh              # Build all specs
#   ./build-all.sh --dry-run    # Show what would be built
#   ./build-all.sh --continue   # Continue from last failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
SPECS_DIR="$WORKSPACE/SPECS"
LOG_DIR="$WORKSPACE/logs"

# Dry run mode
DRY_RUN=false
CONTINUE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --continue|-c)
            CONTINUE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# Create log directory
mkdir -p "$LOG_DIR"

# Get list of specs
SPECS=($(ls "$SPECS_DIR"/*.spec 2>/dev/null | sort))
TOTAL=${#SPECS[@]}

if [[ $TOTAL -eq 0 ]]; then
    echo "ERROR: No specs found in $SPECS_DIR"
    exit 1
fi

echo "=== Maquilinux Build All ==="
echo "Workspace: $WORKSPACE"
echo "Specs:     $TOTAL"
echo ""

# Build counter
BUILT=0
FAILED=0
SKIPPED=0

# Track failed builds
FAILED_SPECS=()

for spec_file in "${SPECS[@]}"; do
    spec_name=$(basename "$spec_file" .spec)
    log_file="$LOG_DIR/${spec_name}.log"
    
    echo "----------------------------------------"
    echo "[$((BUILT + FAILED + SKIPPED + 1))/$TOTAL] $spec_name"
    
    # Check if already built (RPM exists)
    rpm_pattern="$WORKSPACE/RPMS/*/${spec_name}-*.rpm"
    existing_rpms=( $rpm_pattern 2>/dev/null || true )
    
    if [[ ${#existing_rpms[@]} -gt 0 ]] && [[ "$CONTINUE" = true ]]; then
        echo "  SKIP: RPM already exists"
        ((SKIPPED++))
        continue
    fi
    
    if [[ "$DRY_RUN" = true ]]; then
        echo "  WOULD BUILD: $spec_name"
        ((BUILT++))
        continue
    fi
    
    # Build
    echo "  Building..."
    echo "$(date): Building $spec_name" > "$log_file"
    
    if sudo "$SCRIPT_DIR/enter-chroot-build.sh" -c "cd /workspace && rpmbuild -ba SPECS/${spec_name}.spec --define '_topdir /workspace' --nodeps 2>&1" >> "$log_file" 2>&1; then
        echo "  OK"
        ((BUILT++))
        echo "$(date): SUCCESS" >> "$log_file"
    else
        echo "  FAILED (see $log_file)"
        ((FAILED++))
        FAILED_SPECS+=("$spec_name")
        echo "$(date): FAILED" >> "$log_file"
    fi
done

echo ""
echo "=== Build Summary ==="
echo "Total:   $TOTAL"
echo "Built:   $BUILT"
echo "Failed:  $FAILED"
echo "Skipped: $SKIPPED"

if [[ $FAILED -gt 0 ]]; then
    echo ""
    echo "Failed specs:"
    for s in "${FAILED_SPECS[@]}"; do
        echo "  - $s"
    done
    exit 1
fi

echo ""
echo "All specs built successfully!"
