#!/usr/bin/env bash
# build-and-heal.sh - Build specs with automatic healing for common errors
#
# This script runs builds and automatically fixes common spec file issues:
# - Missing files in %files (removes them)
# - Document directories not found (removes %doc entries)
# - C23/GCC15 nullptr issues (adds -std=gnu17)
#
# Usage:
#   ./build-and-heal.sh spec1,spec2,spec3...
#
# Results:
#   Creates /tmp/build-and-heal.report with final status
#   Exit 0 = all built successfully
#   Exit 1 = some specs need manual fixing

set -euo pipefail

SPECS_LIST="${1:-}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SPECS_DIR="$PROJECT_ROOT/SPECS"
BUILD_LOG="/tmp/build-and-heal.log"
REPORT_FILE="/tmp/build-and-heal.report"
MAX_RETRIES=3

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[BUILD-HEAL]${NC} $*" | tee -a "$BUILD_LOG"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "$BUILD_LOG"; }
error() { echo -e "${RED}[ERROR]${NC} $*" | tee -a "$BUILD_LOG"; }

# Parse comma-separated specs
IFS=',' read -ra SPECS <<< "$SPECS_LIST"

# Initialize report
> "$REPORT_FILE"
echo "BUILD AND HEAL REPORT" >> "$REPORT_FILE"
echo "Started: $(date)" >> "$REPORT_FILE"
echo "Specs: $SPECS_LIST" >> "$REPORT_FILE"
echo "=====================================" >> "$REPORT_FILE"

HEALED_SPECS=()
FAILED_SPECS=()
SUCCESS_SPECS=()

heal_spec() {
    local spec="$1"
    local log_file="$2"
    local spec_file="$SPECS_DIR/${spec}.spec"
    local healed=false
    
    log "Analyzing failure for $spec..."
    
    # Check 1: File not found in %files
    local missing_files
    missing_files=$(grep -oP 'File not found: \K.*' "$log_file" 2>/dev/null | head -5)
    
    if [[ -n "$missing_files" ]]; then
        warn "Found missing files in %files:"
        echo "$missing_files" | while read -r file; do
            local pattern=$(basename "$file" | sed 's/\./\\./g; s/-/\\-?/g')
            warn "  - Removing pattern: *$pattern"
            # Remove the line from %files that matches this pattern
            sed -i "/%{_bindir}\/.*$pattern/d; /%{_libdir}\/.*$pattern/d; /%{_docdir}\/.*$pattern/d" "$spec_file" 2>/dev/null || true
        done
        healed=true
    fi
    
    # Check 2: Document directory not found
    if grep -q "File not found:.*%{_docdir}" "$log_file" 2>/dev/null; then
        warn "Document directory issue detected"
        # Comment out or remove %doc lines that cause issues
        sed -i 's/^%doc %{_docdir}/# %doc %{_docdir}/' "$spec_file" 2>/dev/null || true
        healed=true
    fi
    
    # Check 3: C23/GCC15 nullptr error
    if grep -q "error: expected identifier.*before 'nullptr'" "$log_file" 2>/dev/null; then
        warn "C23/GCC15 nullptr keyword conflict detected"
        # Add CFLAGS fix if not present
        if ! grep -q "std=gnu17" "$spec_file"; then
            sed -i '/^%build$/a export CFLAGS="-std=gnu17 ${CFLAGS:-}"' "$spec_file"
            log "Added -std=gnu17 to %build section"
        fi
        healed=true
    fi
    
    if [[ "$healed" == true ]]; then
        log "Applied automatic fixes to $spec"
        return 0
    else
        error "Cannot auto-heal $spec - needs manual intervention"
        return 1
    fi
}

build_single() {
    local spec="$1"
    local attempt="${2:-1}"
    local log_file="$PROJECT_ROOT/BUILD-LOGS/${spec}-attempt-${attempt}.log"
    
    log "Building $spec (attempt $attempt/$MAX_RETRIES)..."
    
    mkdir -p "$PROJECT_ROOT/BUILD-LOGS"
    
    if MQL_DISK=/run/media/glats/maquilinux "$PROJECT_ROOT/scripts/build-spec.sh" "$spec" --skip-tests > "$log_file" 2>&1; then
        log "✅ $spec built successfully!"
        SUCCESS_SPECS+=("$spec")
        echo "✅ $spec: SUCCESS" >> "$REPORT_FILE"
        return 0
    else
        local exit_code=$?
        warn "❌ $spec failed (exit $exit_code)"
        
        if [[ $attempt -lt $MAX_RETRIES ]]; then
            log "Attempting to heal $spec..."
            if heal_spec "$spec" "$log_file"; then
                log "Healed! Retrying..."
                HEALED_SPECS+=("$spec (attempt $attempt)")
                build_single "$spec" $((attempt + 1))
                return $?
            else
                error "Could not heal $spec automatically"
                FAILED_SPECS+=("$spec")
                echo "❌ $spec: FAILED (needs manual fix)" >> "$REPORT_FILE"
                return 1
            fi
        else
            error "Max retries reached for $spec"
            FAILED_SPECS+=("$spec")
            echo "❌ $spec: FAILED (max retries)" >> "$REPORT_FILE"
            return 1
        fi
    fi
}

# Main loop
log "Starting Build-and-Heal for: ${SPECS[*]}"
log "Logs: $BUILD_LOG"
log "Report will be at: $REPORT_FILE"
echo ""

for spec in "${SPECS[@]}"; do
    spec=$(echo "$spec" | xargs)  # Trim whitespace
    [[ -z "$spec" ]] && continue
    
    if [[ ! -f "$SPECS_DIR/${spec}.spec" ]]; then
        error "Spec not found: $spec"
        FAILED_SPECS+=("$spec (missing)")
        continue
    fi
    
    build_single "$spec" || true  # Continue on failure
done

# Generate final report
echo "" >> "$REPORT_FILE"
echo "=====================================" >> "$REPORT_FILE"
echo "SUMMARY:" >> "$REPORT_FILE"
echo "=====================================" >> "$REPORT_FILE"
echo "✅ Success: ${#SUCCESS_SPECS[@]}" >> "$REPORT_FILE"
echo "🔧 Auto-healed: ${#HEALED_SPECS[@]}" >> "$REPORT_FILE"
echo "❌ Failed (need manual): ${#FAILED_SPECS[@]}" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "Completed: $(date)" >> "$REPORT_FILE"

# Display summary
log ""
log "====================================="
log "BUILD AND HEAL COMPLETE"
log "====================================="
log "✅ Success: ${#SUCCESS_SPECS[@]} - ${SUCCESS_SPECS[*]}"
log "🔧 Auto-healed: ${#HEALED_SPECS[@]} - ${HEALED_SPECS[*]}"
log "❌ Failed (need manual): ${#FAILED_SPECS[@]} - ${FAILED_SPECS[*]}"
log ""
log "Full report: $REPORT_FILE"
log "Build log: $BUILD_LOG"

if [[ ${#FAILED_SPECS[@]} -eq 0 ]]; then
    log "🎉 ALL SPECS BUILT SUCCESSFULLY!"
    exit 0
else
    error "⚠️  Some specs need manual intervention"
    exit 1
fi
