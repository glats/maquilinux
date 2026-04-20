#!/usr/bin/env bash
# build-chain.sh - Build a chain of specs with dependency ordering and error handling
#
# Usage:
#   ./build-chain.sh spec1,spec2,spec3,... [options]
#
# Options:
#   --resume        - Resume from last failed spec (requires state file)
#   --state-file    - Specify custom state file (default: .build-chain-state)
#   --skip-failed   - Skip previously failed specs and continue
#   --verbose       - Show all build output
#   --dry-run       - Show what would be built without executing
#
# Examples:
#   ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme
#   ./build-chain.sh nettle,libgpg-error --resume
#   ./build-chain.sh rust --verbose

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPECS_DIR="$PROJECT_ROOT/SPECS"
DEFAULT_STATE_FILE="$PROJECT_ROOT/.build-chain-state"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Command line arguments
SPECS_LIST=""
RESUME=false
SKIP_FAILED=false
VERBOSE=false
DRY_RUN=false
SKIP_TESTS=false
STATE_FILE="$DEFAULT_STATE_FILE"

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --resume)
                RESUME=true
                shift
                ;;
            --skip-failed)
                SKIP_FAILED=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-tests|--nocheck)
                SKIP_TESTS=true
                shift
                ;;
            --state-file)
                STATE_FILE="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            --*)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                SPECS_LIST="$1"
                shift
                ;;
        esac
    done
}

show_help() {
    cat << 'EOF'
build-chain.sh - Build specs in dependency order with error handling

Usage:
  ./build-chain.sh spec1,spec2,spec3,... [options]

Options:
  --resume        Resume from last failed spec (requires state file)
  --skip-failed   Skip previously failed specs and continue
  --skip-tests    Skip test/check phase for faster builds (rpmbuild --nocheck)
  --state-file    Use custom state file (default: .build-chain-state)
  --verbose       Show all build output (not just summary)
  --dry-run       Show what would be built without executing
  --help, -h      Show this help

Examples:
  # Build crypto chain
  ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme

  # Resume after fixing a failed build
  ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme --resume

  # Skip failed and continue with rest
  ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme --skip-failed

  # Fast build - skip tests (useful for bootstrap/development)
  ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme --skip-tests

State File Format:
  Each line: spec_name|status|timestamp|log_file
  Status: PENDING, BUILDING, SUCCESS, FAILED, SKIPPED
EOF
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Parse comma-separated specs into array
parse_specs() {
    local specs_str="$1"
    IFS=',' read -ra SPECS_ARRAY <<< "$specs_str"
    # Trim whitespace
    for i in "${!SPECS_ARRAY[@]}"; do
        SPECS_ARRAY[$i]="$(echo "${SPECS_ARRAY[$i]}" | xargs)"
    done
}

# Verify spec files exist
verify_specs() {
    local missing=()
    for spec in "${SPECS_ARRAY[@]}"; do
        local spec_file="$SPECS_DIR/${spec}.spec"
        if [[ ! -f "$spec_file" ]]; then
            missing+=("$spec")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing spec files:"
        for spec in "${missing[@]}"; do
            echo "  - $SPECS_DIR/${spec}.spec" >&2
        done
        exit 1
    fi
}

# Initialize or load state file
init_state() {
    if [[ "$RESUME" == true ]]; then
        if [[ ! -f "$STATE_FILE" ]]; then
            log_warn "No state file found at $STATE_FILE"
            log_info "Starting fresh build..."
        else
            log_info "Resuming from state file: $STATE_FILE"
        fi
    else
        # Fresh start - create new state file
        log_info "Creating new state file: $STATE_FILE"
        : > "$STATE_FILE"
        for spec in "${SPECS_ARRAY[@]}"; do
            echo "${spec}|PENDING|$(date -Iseconds)|" >> "$STATE_FILE"
        done
    fi
}

# Update state for a spec
update_state() {
    local spec="$1"
    local status="$2"
    local log_file="${3:-}"
    
    # Read current state
    local temp_file=$(mktemp)
    while IFS='|' read -r name old_status timestamp old_log; do
        if [[ "$name" == "$spec" ]]; then
            echo "${spec}|${status}|$(date -Iseconds)|${log_file}" >> "$temp_file"
        else
            echo "${name}|${old_status}|${timestamp}|${old_log}" >> "$temp_file"
        fi
    done < "$STATE_FILE"
    
    mv "$temp_file" "$STATE_FILE"
}

# Get current status of a spec
get_spec_status() {
    local spec="$1"
    while IFS='|' read -r name status timestamp log_file; do
        if [[ "$name" == "$spec" ]]; then
            echo "$status"
            return 0
        fi
    done < "$STATE_FILE"
    echo "PENDING"
}

# Check if spec should be skipped
should_skip() {
    local spec="$1"
    local status=$(get_spec_status "$spec")
    
    if [[ "$status" == "SUCCESS" ]]; then
        log_info "Skipping $spec (already built successfully)"
        return 0
    fi
    
    if [[ "$status" == "FAILED" && "$SKIP_FAILED" == true ]]; then
        log_warn "Skipping $spec (previously failed)"
        update_state "$spec" "SKIPPED"
        return 0
    fi
    
    if [[ "$status" == "FAILED" && "$RESUME" != true ]]; then
        log_error "$spec previously failed. Use --resume to retry or --skip-failed to continue."
        return 0
    fi
    
    return 1
}

# Build a single spec
build_spec() {
    local spec="$1"
    local log_dir="$PROJECT_ROOT/BUILD-LOGS"
    mkdir -p "$log_dir"
    local log_file="$log_dir/${spec}-$(date +%Y%m%d-%H%M%S).log"
    
    log_info "=========================================="
    log_info "Building: $spec"
    log_info "Log file: $log_file"
    log_info "=========================================="
    
    update_state "$spec" "BUILDING" "$log_file"
    
    # Build command with optional flags
    local build_cmd=("$SCRIPT_DIR/build-spec.sh" "$spec")
    if [[ "$SKIP_TESTS" == true ]]; then
        build_cmd+=("--skip-tests")
    fi
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would execute: ${build_cmd[*]}"
        update_state "$spec" "SUCCESS" "$log_file"
        return 0
    fi
    
    # Run the build
    local start_time=$(date +%s)
    
    if [[ "$VERBOSE" == true ]]; then
        # Show all output
        if "${build_cmd[@]}" 2>&1 | tee "$log_file"; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            log_success "$spec built successfully in ${duration}s"
            update_state "$spec" "SUCCESS" "$log_file"
            return 0
        else
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            log_error "$spec failed after ${duration}s"
            log_error "See log: $log_file"
            update_state "$spec" "FAILED" "$log_file"
            return 1
        fi
    else
        # Capture output to log only, show summary
        if "${build_cmd[@]}" > "$log_file" 2>&1; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            log_success "$spec built successfully in ${duration}s"
            update_state "$spec" "SUCCESS" "$log_file"
            
            # Show last lines of log for verification
            echo "  Last 5 lines of log:" >&2
            tail -5 "$log_file" | sed 's/^/    /' >&2
            return 0
        else
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            log_error "$spec failed after ${duration}s"
            log_error "See full log: $log_file"
            log_error "Last 20 lines of failed build:" >&2
            tail -20 "$log_file" | sed 's/^/  /' >&2
            update_state "$spec" "FAILED" "$log_file"
            return 1
        fi
    fi
}

# Print final summary
print_summary() {
    local total=${#SPECS_ARRAY[@]}
    local success=0
    local failed=0
    local skipped=0
    local pending=0
    
    log_info ""
    log_info "=========================================="
    log_info "BUILD SUMMARY"
    log_info "=========================================="
    
    while IFS='|' read -r name status timestamp log_file; do
        case "$status" in
            SUCCESS)
                success=$((success + 1))
                echo -e "  ${GREEN}✓${NC} $name" >&2
                ;;
            FAILED)
                failed=$((failed + 1))
                echo -e "  ${RED}✗${NC} $name (see: $log_file)" >&2
                ;;
            SKIPPED)
                skipped=$((skipped + 1))
                echo -e "  ${YELLOW}○${NC} $name (skipped)" >&2
                ;;
            *)
                pending=$((pending + 1))
                echo -e "  ${BLUE}?${NC} $name ($status)" >&2
                ;;
        esac
    done < "$STATE_FILE"
    
    log_info "------------------------------------------"
    log_info "Total: $total | ${GREEN}Success: $success${NC} | ${RED}Failed: $failed${NC} | ${YELLOW}Skipped: $skipped${NC} | ${BLUE}Pending: $pending${NC}"
    log_info "State file: $STATE_FILE"
    log_info "=========================================="
    
    if [[ $failed -gt 0 ]]; then
        log_error ""
        log_error "Some builds failed! To resume:"
        log_error "  ./build-chain.sh SPECS --resume"
        log_error ""
        log_error "To skip failed and continue:"
        log_error "  ./build-chain.sh SPECS --skip-failed"
        return 1
    fi
    
    if [[ $pending -gt 0 ]]; then
        log_warn ""
        log_warn "Some specs still pending. To resume:"
        log_warn "  ./build-chain.sh SPECS --resume"
        return 1
    fi
    
    log_success ""
    log_success "All builds completed successfully!"
    return 0
}

# Main execution
main() {
    parse_args "$@"
    
    if [[ -z "$SPECS_LIST" ]]; then
        log_error "No specs specified!"
        show_help
        exit 1
    fi
    
    parse_specs "$SPECS_LIST"
    
    log_info "Build chain: ${SPECS_ARRAY[*]}"
    log_info "Total specs: ${#SPECS_ARRAY[@]}"
    
    verify_specs
    init_state
    
    # Build each spec
    local exit_code=0
    for spec in "${SPECS_ARRAY[@]}"; do
        if should_skip "$spec"; then
            continue
        fi
        
        if ! build_spec "$spec"; then
            exit_code=1
            if [[ "$DRY_RUN" != true ]]; then
                log_error ""
                log_error "Build chain stopped at: $spec"
                log_error "Fix the issue and resume with: --resume"
                break
            fi
        fi
    done
    
    print_summary
    exit $exit_code
}

main "$@"
