#!/usr/bin/env bash
# build-chain.sh - Build specs with dependency ordering and error handling
#
# Usage:
#   ./build-chain.sh spec1,spec2,spec3,... [options]
#   ./build-chain.sh --all [options]
#
# Options:
#   --all           - Build all specs found in SPECS/ directory
#   --resume        - Resume from last failed spec (requires state file)
#   --state-file    - Specify custom state file (default: .build-chain-state)
#   --skip-failed   - Skip previously failed specs and continue
#   --continue      - Skip specs with existing RPMs (alias for --skip-built)
#   --skip-built    - Skip specs that already have built RPMs
#   --verbose       - Show all build output
#   --dry-run       - Show what would be built without executing
#   --skip-tests    - Skip test/check phase (rpmbuild --nocheck)
#   --heal          - Auto-fix common spec errors and retry on failure
#   --async         - Run build in detached tmux session
#
# Examples:
#   ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme
#   ./build-chain.sh --all --continue
#   ./build-chain.sh nettle,libgpg-error --resume
#   ./build-chain.sh rust --verbose
#   ./build-chain.sh rust --async
#   ./build-chain.sh nettle,libgcrypt --heal

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SPECS_DIR="$PROJECT_ROOT/SPECS"
DEFAULT_STATE_FILE="$PROJECT_ROOT/.build-chain-state"
LOG_DIR="$PROJECT_ROOT/logs"

# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"
# shellcheck source=../lib/repo.sh
source "$SCRIPT_DIR/../lib/repo.sh"

# Command line arguments
SPECS_LIST=""
BUILD_ALL=false
RESUME=false
SKIP_FAILED=false
SKIP_BUILT=false
VERBOSE=false
DRY_RUN=false
SKIP_TESTS=false
HEAL_MODE=false
ASYNC_MODE=false
STATE_FILE="$DEFAULT_STATE_FILE"
MAX_HEAL_RETRIES=3

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                BUILD_ALL=true
                shift
                ;;
            --resume)
                RESUME=true
                shift
                ;;
            --skip-failed)
                SKIP_FAILED=true
                shift
                ;;
            --continue|--skip-built)
                SKIP_BUILT=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --dry-run|-n)
                DRY_RUN=true
                shift
                ;;
            --skip-tests|--nocheck)
                SKIP_TESTS=true
                shift
                ;;
            --heal)
                HEAL_MODE=true
                shift
                ;;
            --async)
                ASYNC_MODE=true
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
                log_error "Unknown option: $1"
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
  ./build-chain.sh --all [options]

Options:
  --all           Build all specs found in SPECS/ directory
  --resume        Resume from last failed spec (requires state file)
  --skip-failed   Skip previously failed specs and continue
  --continue      Skip specs with existing RPMs (alias: --skip-built)
  --skip-built    Skip specs that already have built RPMs
  --skip-tests    Skip test/check phase for faster builds (rpmbuild --nocheck)
  --state-file    Use custom state file (default: .build-chain-state)
  --verbose       Show all build output (not just summary)
  --dry-run       Show what would be built without executing
  --heal          Auto-fix common spec errors on failure and retry
  --async         Run build in detached tmux session (for long builds like Rust)
  --help, -h      Show this help

Features:
  - Automatic source fetching
  - Resume capability (--resume)
  - Per-spec log files in logs/
  - State tracking (PENDING/BUILDING/SUCCESS/FAILED/SKIPPED)
  - Auto-heal: fixes missing %files, %doc dirs, C23/GCC15 nullptr (--heal)
  - Async builds via tmux for multi-hour builds (--async)

Examples:
  # Build crypto chain
  ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme

  # Build all specs, skipping already-built ones
  ./build-chain.sh --all --continue

  # Resume after fixing a failed build
  ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme --resume

  # Fast build - skip tests
  ./build-chain.sh nettle,libgpg-error,libgcrypt,libassuan,gpgme --skip-tests

  # Long build with auto-heal
  ./build-chain.sh glibc,gcc --heal

  # Detached async build (Rust takes hours)
  ./build-chain.sh rust --async

State File Format:
  Each line: spec_name|status|timestamp|log_file
  Status: PENDING, BUILDING, SUCCESS, FAILED, SKIPPED
EOF
}

# Collect all spec names from SPECS/ directory
collect_all_specs() {
    local specs=()
    for spec_file in "$SPECS_DIR"/*.spec; do
        [[ -f "$spec_file" ]] || continue
        specs+=("$(basename "$spec_file" .spec)")
    done
    if [[ ${#specs[@]} -eq 0 ]]; then
        log_error "No spec files found in $SPECS_DIR"
        exit 1
    fi
    # Join with commas
    local IFS=','
    echo "${specs[*]}"
}

# Parse comma-separated specs into array
parse_specs() {
    local specs_str="$1"
    IFS=',' read -ra SPECS_ARRAY <<< "$specs_str"
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

# Check if RPMs already exist for a spec
rpms_exist() {
    local spec="$1"
    local count=0
    for f in "$PROJECT_ROOT/RPMS"/*/${spec}-[0-9]*.rpm; do
        [[ -f "$f" ]] && ((count++)) || true
    done
    [[ $count -gt 0 ]]
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

    local temp_file
    temp_file="$(mktemp)"
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
    local status
    status="$(get_spec_status "$spec")"

    if [[ "$status" == "SUCCESS" ]]; then
        log_info "Skipping $spec (already built successfully)"
        install_built_rpms "$spec" "" || true
        return 0
    fi

    if [[ "$SKIP_BUILT" == true ]] && rpms_exist "$spec"; then
        log_info "Skipping $spec (RPMs already exist)"
        update_state "$spec" "SKIPPED"
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

# Fetch sources for a spec
fetch_sources() {
    local spec="$1"

    log_info "Fetching sources for: $spec"

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would execute: ./scripts/fetch-spec-sources.sh $spec"
        return 0
    fi

    if "$SCRIPT_DIR/fetch-spec-sources.sh" "$spec" > /dev/null 2>&1; then
        log_info "Sources ready for: $spec"
        return 0
    else
        log_error "Failed to fetch sources for: $spec"
        return 1
    fi
}

# Install built RPMs for BuildRequires chain support
install_built_rpms() {
    local spec="$1"
    local log_file="$2"

    log_info "Installing built RPMs for: $spec (BuildRequires chain)"

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would install RPMs from RPMS/"
        return 0
    fi

    local chroot_target
    chroot_target="${MQL_ROOTFS:-${MQL_LFS:-${MQL_DISK:-/mnt/maquilinux}}}/merged"

    local rpms_dir="$PROJECT_ROOT/RPMS"
    local rpms_installed=0

    for rpm_file in "$rpms_dir"/*/${spec}-[0-9]*.rpm "$rpms_dir"/*/${spec}-[a-z]*-[0-9]*.rpm; do
        [[ -f "$rpm_file" ]] || continue

        log_info "  Installing: $(basename "$rpm_file")"

        if sudo chroot "$chroot_target" /usr/bin/dnf5 install -y "$rpm_file" > /dev/null 2>&1; then
            ((rpms_installed++))
        elif sudo chroot "$chroot_target" /usr/bin/rpm -Uvh --nodeps "$rpm_file" > /dev/null 2>&1; then
            log_warn "  Installed with rpm --nodeps (dnf5 failed): $(basename "$rpm_file")"
            ((rpms_installed++))
        else
            log_warn "  Failed to install: $(basename "$rpm_file")"
        fi
    done

    if [[ $rpms_installed -gt 0 ]]; then
        log_info "Installed $rpms_installed RPM(s) for $spec"
        sudo chroot "$chroot_target" /sbin/ldconfig || true
        return 0
    else
        log_warn "No RPMs found/installed for $spec"
        return 0
    fi
}

# Update repo metadata for the arch that just had a spec built.
# Detects which arch (x86_64 or i686) has RPMs for the spec, then runs
# createrepo_c on that arch dir. Called after each successful spec build
# so the next spec in the chain can resolve BuildRequires immediately.
update_repo_for_spec() {
    local spec="$1"

    if ! command -v createrepo_c &>/dev/null; then
        log_warn "createrepo_c not found — run 'mql repo update' manually after the build"
        return 0
    fi

    local rpms_dir="$PROJECT_ROOT/RPMS"
    local detected_arch=""

    for arch in x86_64 i686; do
        local arch_dir="$rpms_dir/$arch"
        [[ -d "$arch_dir" ]] || continue

        # Check if this arch has an RPM for the just-built spec
        if ls "$arch_dir"/${spec}-[0-9]*.rpm "$arch_dir"/${spec}-[a-z]*-[0-9]*.rpm &>/dev/null 2>&1; then
            detected_arch="$arch"
            break
        fi
    done

    if [[ -z "$detected_arch" ]]; then
        log_warn "Could not detect arch for $spec — skipping repo update"
        return 0
    fi

    log_info "Updating repo metadata for $detected_arch..."
    if mql_repo_update "$detected_arch" 2>/dev/null; then
        log_ok "Repo metadata updated: $detected_arch"
    else
        log_warn "Failed to update repo metadata for $detected_arch"
    fi
}

# Auto-heal common spec errors and return 0 if something was fixed
heal_spec() {
    local spec="$1"
    local log_file="$2"
    local spec_file="$SPECS_DIR/${spec}.spec"
    local healed=false

    log_info "Analyzing failure for $spec..."

    # Fix 1: Missing files listed in %files section
    local missing_files
    missing_files=$(grep -oP 'File not found: \K.*' "$log_file" 2>/dev/null | head -5 || true)

    if [[ -n "$missing_files" ]]; then
        log_warn "Found missing files in %files:"
        while IFS= read -r file; do
            local pattern
            pattern="$(basename "$file" | sed 's/\./\\./g; s/-/\\-?/g')"
            log_warn "  Removing pattern: *$pattern"
            sed -i "/%{_bindir}\/.*$pattern/d; /%{_libdir}\/.*$pattern/d; /%{_docdir}\/.*$pattern/d" "$spec_file" 2>/dev/null || true
        done <<< "$missing_files"
        healed=true
    fi

    # Fix 2: Document directory not found
    if grep -q "File not found:.*%{_docdir}" "$log_file" 2>/dev/null; then
        log_warn "Document directory issue detected — commenting out %doc %{_docdir} lines"
        sed -i 's/^%doc %{_docdir}/# %doc %{_docdir}/' "$spec_file" 2>/dev/null || true
        healed=true
    fi

    # Fix 3: C23/GCC15 nullptr keyword conflict
    if grep -q "error: expected identifier.*before 'nullptr'" "$log_file" 2>/dev/null; then
        log_warn "C23/GCC15 nullptr conflict detected — adding -std=gnu17"
        if ! grep -q "std=gnu17" "$spec_file"; then
            sed -i '/^%build$/a export CFLAGS="-std=gnu17 ${CFLAGS:-}"' "$spec_file"
        fi
        healed=true
    fi

    if [[ "$healed" == true ]]; then
        log_info "Applied automatic fixes to $spec"
        return 0
    else
        log_error "Cannot auto-heal $spec — needs manual intervention"
        return 1
    fi
}

# Build a single spec (with optional heal loop)
build_spec() {
    local spec="$1"
    local attempt="${2:-1}"
    mkdir -p "$LOG_DIR"
    local log_file="$LOG_DIR/${spec}-$(date +%Y%m%d-%H%M%S).log"

    log_info "=========================================="
    log_info "Building: $spec (attempt $attempt)"
    log_info "Log file: $log_file"
    log_info "=========================================="

    update_state "$spec" "BUILDING" "$log_file"

    if ! fetch_sources "$spec"; then
        update_state "$spec" "FAILED" "$log_file"
        return 1
    fi

    local build_cmd=("$SCRIPT_DIR/build-spec.sh" "$spec")
    if [[ "$SKIP_TESTS" == true ]]; then
        build_cmd+=("--skip-tests")
    fi

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would execute: ${build_cmd[*]}"
        update_state "$spec" "SUCCESS" "$log_file"
        return 0
    fi

    local start_time
    start_time="$(date +%s)"
    local build_ok=true

    if [[ "$VERBOSE" == true ]]; then
        "${build_cmd[@]}" 2>&1 | tee "$log_file" || build_ok=false
    else
        "${build_cmd[@]}" > "$log_file" 2>&1 || build_ok=false
    fi

    local duration=$(( $(date +%s) - start_time ))

    if [[ "$build_ok" == true ]]; then
        log_info "$spec built successfully in ${duration}s"
        update_state "$spec" "SUCCESS" "$log_file"

        # Update repo metadata so DNF can see the new package immediately
        # This runs after each individual spec succeeds so the next spec in the
        # chain can resolve BuildRequires against the just-built package.
        update_repo_for_spec "$spec"

        install_built_rpms "$spec" "$log_file" || true
        if [[ "$VERBOSE" != true ]]; then
            echo "  Last 5 lines of log:" >&2
            tail -5 "$log_file" | sed 's/^/    /' >&2
        fi
        return 0
    else
        log_error "$spec failed after ${duration}s"
        log_error "See full log: $log_file"
        tail -20 "$log_file" | sed 's/^/  /' >&2

        # Heal mode: try auto-fix and retry
        if [[ "$HEAL_MODE" == true && $attempt -lt $MAX_HEAL_RETRIES ]]; then
            log_info "Attempting to auto-heal $spec..."
            if heal_spec "$spec" "$log_file"; then
                log_info "Healed! Retrying (attempt $((attempt + 1)))..."
                build_spec "$spec" $((attempt + 1))
                return $?
            else
                log_error "Could not auto-heal $spec"
            fi
        fi

        update_state "$spec" "FAILED" "$log_file"
        return 1
    fi
}

# Launch async build in detached tmux session
build_async() {
    local spec="$1"
    local timestamp
    timestamp="$(date +%Y%m%d-%H%M%S)"
    local session_name="build-${spec}-${timestamp}"
    mkdir -p "$LOG_DIR"
    local log_file="$LOG_DIR/${spec}-async-${timestamp}.log"

    log_info "Starting async build: $spec"
    log_info "tmux session: $session_name"
    log_info "Log file: $log_file"

    # Build the inline build command
    local build_flags=()
    [[ "$SKIP_TESTS" == true ]] && build_flags+=("--skip-tests")
    [[ "$HEAL_MODE" == true ]] && build_flags+=("--heal")
    [[ "$VERBOSE" == true ]] && build_flags+=("--verbose")

    local inner_cmd="$SCRIPT_DIR/build-chain.sh $spec ${build_flags[*]:-} 2>&1 | tee '$log_file'; echo BUILD_EXIT:\$?"

    tmux kill-session -t "$session_name" 2>/dev/null || true
    tmux new-session -d -s "$session_name" -n "build-$spec" "bash -c '$inner_cmd'"

    echo ""
    echo "=========================================="
    echo "Async build started in tmux session: $session_name"
    echo ""
    echo "To monitor:"
    echo "  tmux attach-session -t $session_name"
    echo ""
    echo "To check log:"
    echo "  tail -f $log_file"
    echo ""
    echo "To check status:"
    echo "  ./scripts/check-build-status.sh $spec"
    echo "=========================================="
}

# Print final summary
print_summary() {
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
                echo "  [OK] $name" >&2
                ;;
            FAILED)
                failed=$((failed + 1))
                echo "  [FAIL] $name (see: $log_file)" >&2
                ;;
            SKIPPED)
                skipped=$((skipped + 1))
                echo "  [SKIP] $name" >&2
                ;;
            *)
                pending=$((pending + 1))
                echo "  [?] $name ($status)" >&2
                ;;
        esac
    done < "$STATE_FILE"

    log_info "------------------------------------------"
    log_info "Success: $success | Failed: $failed | Skipped: $skipped | Pending: $pending"
    log_info "State file: $STATE_FILE"
    log_info "=========================================="

    if [[ $failed -gt 0 ]]; then
        log_error "Some builds failed! To resume:"
        log_error "  ./build-chain.sh SPECS --resume"
        log_error "To skip failed and continue:"
        log_error "  ./build-chain.sh SPECS --skip-failed"
        return 1
    fi

    if [[ $pending -gt 0 ]]; then
        log_warn "Some specs still pending. To resume:"
        log_warn "  ./build-chain.sh SPECS --resume"
        return 1
    fi

    log_info "All builds completed successfully!"
    return 0
}

# Main execution
main() {
    parse_args "$@"

    # Collect spec list
    if [[ "$BUILD_ALL" == true ]]; then
        SPECS_LIST="$(collect_all_specs)"
    fi

    if [[ -z "$SPECS_LIST" ]]; then
        log_error "No specs specified!"
        show_help
        exit 1
    fi

    parse_specs "$SPECS_LIST"

    log_info "Build chain: ${SPECS_ARRAY[*]}"
    log_info "Total specs: ${#SPECS_ARRAY[@]}"

    verify_specs
    mkdir -p "$LOG_DIR"

    # Async mode: delegate to tmux sessions
    if [[ "$ASYNC_MODE" == true ]]; then
        for spec in "${SPECS_ARRAY[@]}"; do
            build_async "$spec"
        done
        exit 0
    fi

    init_state

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
