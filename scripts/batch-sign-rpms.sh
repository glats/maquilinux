#!/usr/bin/env bash
# scripts/batch-sign-rpms.sh - Batch sign all production RPMs
# Pulls unsigned RPMs from rog, signs locally, pushes back.
# Usage: ./scripts/batch-sign-rpms.sh [--dry-run]

set -euo pipefail

ROG_HOST="rog.local"
REPO_BASE="/srv/glats/nginx/repo/linux/maquilinux/26.4"
ARCHES=("x86_64" "i686")
BATCH_DIR="/tmp/sign-batch"
GPG_NAME="Maqui Linux <security@maqui-linux.org>"
FAILURES_LOG="$BATCH_DIR/failures.log"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "[batch-sign] DRY RUN MODE - no signing will occur"
fi

log() {
    echo "[batch-sign] $(date '+%Y-%m-%d %H:%M:%S') $*"
}

cleanup() {
    log "Cleaning up $BATCH_DIR"
    rm -rf "$BATCH_DIR"
}
trap cleanup EXIT

mkdir -p "$BATCH_DIR"
touch "$FAILURES_LOG"

total_signed=0
total_failed=0

for arch in "${ARCHES[@]}"; do
    remote_path="$REPO_BASE/$arch/stable/"

    # Check if arch directory exists on rog
    if ! ssh "$ROG_HOST" "test -d $remote_path" 2>/dev/null; then
        log "SKIP: $arch/stable/ does not exist on rog"
        continue
    fi

    # Count RPMs on remote
    rpm_count=$(ssh "$ROG_HOST" "ls $remote_path*.rpm 2>/dev/null | wc -l" 2>/dev/null || echo "0")
    if [[ "$rpm_count" == "0" ]]; then
        log "SKIP: No RPMs found in $arch/stable/"
        continue
    fi
    log "Found $rpm_count RPMs in $arch/stable/"

    arch_batch="$BATCH_DIR/$arch"
    mkdir -p "$arch_batch"

    # Step 1: Pull RPMs from rog
    log "Pulling RPMs from rog:$remote_path -> $arch_batch/"
    rsync -avz --progress "${ROG_HOST}:${remote_path}*.rpm" "$arch_batch/" 2>&1 | tail -3

    # Step 2: Ensure we own the files for signing
    chown glats:users "$arch_batch"/*.rpm 2>/dev/null || true

    if $DRY_RUN; then
        log "DRY RUN: Would sign $(ls "$arch_batch"/*.rpm 2>/dev/null | wc -l) RPMs"
        continue
    fi

    # Step 3: Sign each RPM
    sign_count=0
    fail_count=0
    for rpm in "$arch_batch"/*.rpm; do
        [[ -f "$rpm" ]] || continue
        rpm_name=$(basename "$rpm")

        if nix shell nixpkgs#rpm -c rpmsign --define "_gpg_name $GPG_NAME" --addsign "$rpm" 2>&1; then
            sign_count=$((sign_count + 1))
        else
            echo "FAIL: $arch/$rpm_name" >> "$FAILURES_LOG"
            fail_count=$((fail_count + 1))
        fi
    done

    log "$arch: signed=$sign_count failed=$fail_count"
    total_signed=$((total_signed + sign_count))
    total_failed=$((total_failed + fail_count))

    # Step 4: Push signed RPMs back to rog
    log "Pushing signed RPMs back to rog:$remote_path"
    rsync -avz --progress "$arch_batch"/*.rpm "${ROG_HOST}:${remote_path}" 2>&1 | tail -3
done

# Summary
echo ""
echo "========================================="
echo "  BATCH SIGNING SUMMARY"
echo "========================================="
echo "  Total signed: $total_signed"
echo "  Total failed: $total_failed"

if [[ $total_failed -gt 0 ]]; then
    echo ""
    echo "  Failed RPMs (see $FAILURES_LOG):"
    cat "$FAILURES_LOG"
    exit 1
fi

echo "  Status: ALL OK"
echo "========================================="
exit 0
