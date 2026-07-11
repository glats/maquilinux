#!/usr/bin/env bash
# scripts/acceptance-test.sh - Post-build verification with structured JSON output
#
# Usage:
#   ./acceptance-test.sh <spec> [--arch=x86_64|i686] [--json]
#
# Tests:
#   1. rpm_installed  - Package registered in RPM database (rpm -q)
#   2. rpm_verify     - File integrity check (rpm -V)
#   3. binary_exec    - Binary execution test (--version)
#   4. library_linkage - Shared library linkage check (ldd)
#   5. multiarch      - Multiarch library path check
#
# Exit code: 0 = all required tests pass, 1 = any required test fails
# Output: JSON to stdout with per-check status, regardless of exit code
#
# Design: openspec/changes/remote-spec-build-pipeline/design.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Defaults
SPEC=""
ARCH="x86_64"
JSON_MODE=false

show_help() {
    cat << 'EOF'
Usage: ./acceptance-test.sh <spec> [--arch=x86_64|i686] [--json]

Run acceptance tests for a built RPM package inside the Maqui Linux chroot.

Arguments:
  <spec>            Package spec name (e.g., bash, zlib, glibc)

Options:
  --arch=x86_64     Target architecture for multiarch check (default: x86_64)
  --arch i686       Short form
  --json            Output JSON to stdout (always enabled, flag is a no-op)
  --help, -h        Show this help

Exit codes:
  0  All required tests pass
  1  One or more required tests fail (rpm_installed, rpm_verify)
  2  Usage error (wrong arguments)
  3  Prerequisite error (mql not available or chroot not mounted)

Output JSON format:
{
  "spec": "bash",
  "arch": "x86_64",
  "timestamp": "2026-07-10T12:00:00Z",
  "status": "pass",
  "checks": [
    {"name": "rpm_installed", "status": "pass"},
    {"name": "rpm_verify", "status": "pass"},
    {"name": "binary_exec", "status": "pass", "detail": "bash --version exit 0"},
    {"name": "library_linkage", "status": "skip", "detail": "no shared libs"},
    {"name": "multiarch", "status": "pass"}
  ],
  "failures": []
}
EOF
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --arch=*)
                ARCH="${1#*=}"
                shift
                ;;
            --arch)
                ARCH="$2"
                shift 2
                ;;
            --json)
                JSON_MODE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            -*)
                echo "Unknown option: $1" >&2
                show_help >&2
                exit 2
                ;;
            *)
                if [[ -z "$SPEC" ]]; then
                    SPEC="$1"
                else
                    echo "Unexpected argument: $1" >&2
                    show_help >&2
                    exit 2
                fi
                shift
                ;;
        esac
    done
}

parse_args "$@"

# Validate
if [[ -z "$SPEC" ]]; then
    echo "Error: spec name is required" >&2
    show_help >&2
    exit 2
fi

# JSON mode is always on for output; this flag controls whether log messages
# also go to stderr (when --json is explicitly passed, suppress log chatter)
CHATTY=true
if [[ "$JSON_MODE" == true ]]; then
    CHATTY=false
fi

# Verify mql is available
if ! command -v mql &>/dev/null; then
    echo "Error: mql command not found. Are you in the Maqui Linux project root?" >&2
    exit 3
fi

# Verify chroot is mounted by checking a known path
if ! mql chroot --exec "true" 2>/dev/null; then
    echo "Error: Cannot execute in chroot. Is the overlay mounted?" >&2
    exit 3
fi

# Run a command inside the chroot and return its exit code
# Usage: check_chroot <command...>
# Returns 0 if command succeeds, 1 if it fails
check_chroot() {
    mql chroot --exec "$*" >/dev/null 2>&1
}

# Run a command inside the chroot and capture its stdout
# Usage: capture_chroot <command...>
capture_chroot() {
    mql chroot --exec "$*" 2>/dev/null
}

# --- Initialize results ---
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
OVERALL_STATUS="pass"
FAILURES=()
CHECKS_JSON=""
CHECK_SEP=""

# Helper: append a check result to the checks JSON array
add_check() {
    local name="$1"
    local status="$2"
    local detail="${3:-}"

    CHECKS_JSON+="${CHECK_SEP}{\"name\":\"${name}\",\"status\":\"${status}\""
    if [[ -n "$detail" ]]; then
        # Escape double quotes in detail
        local detail_escaped="${detail//\"/\\\"}"
        CHECKS_JSON+=",\"detail\":\"${detail_escaped}\""
    fi
    CHECKS_JSON+="}"
    CHECK_SEP=","
}

add_failure() {
    local check_name="$1"
    local detail="${2:-}"
    FAILURES+=("{\"check\":\"${check_name}\",\"detail\":\"${detail}\"}")
}

# ============================================================================
# Test 1: Package Installation (rpm -q)
# ============================================================================
if [[ "$CHATTY" == true ]]; then echo "Test 1: rpm_installed" >&2; fi

if check_chroot "rpm -q ${SPEC}"; then
    add_check "rpm_installed" "pass"
else
    add_check "rpm_installed" "fail" "rpm -q ${SPEC} failed: package not installed"
    add_failure "rpm_installed" "Package ${SPEC} is not installed in the RPM database"
    OVERALL_STATUS="fail"
fi

# ============================================================================
# Test 2: File Integrity (rpm -V)
# ============================================================================
if [[ "$CHATTY" == true ]]; then echo "Test 2: rpm_verify" >&2; fi

RPMV_OUTPUT=$(capture_chroot "rpm -V ${SPEC}" 2>&1) || true
if [[ -z "$RPMV_OUTPUT" ]]; then
    add_check "rpm_verify" "pass"
else
    # rpm -V has output = files were modified
    local rpmv_detail
    rpmv_detail="rpm -V shows discrepancies: $(echo "$RPMV_OUTPUT" | head -5 | tr '\n' ';')"
    add_check "rpm_verify" "fail" "${rpmv_detail}"
    add_failure "rpm_verify" "File integrity check failed for ${SPEC}"
    OVERALL_STATUS="fail"
fi

# ============================================================================
# Test 3: Binary Execution Test
# ============================================================================
if [[ "$CHATTY" == true ]]; then echo "Test 3: binary_exec" >&2; fi

# Find binaries installed by this package
BINARY_LIST=$(capture_chroot "rpm -ql ${SPEC} 2>/dev/null" | grep -E '^/(usr/)?(s?bin)/' || true)

if [[ -z "$BINARY_LIST" ]]; then
    add_check "binary_exec" "skip" "no binaries found in package"
else
    # Pick the first binary
    FIRST_BINARY=$(echo "$BINARY_LIST" | head -1)
    if check_chroot "${FIRST_BINARY} --version"; then
        add_check "binary_exec" "pass" "${FIRST_BINARY} --version exit 0"
    else
        # Try --help as fallback
        if check_chroot "${FIRST_BINARY} --help"; then
            add_check "binary_exec" "pass" "${FIRST_BINARY} --help exit 0"
        else
            add_check "binary_exec" "fail" "${FIRST_BINARY} --version/--help failed"
            add_failure "binary_exec" "Binary ${FIRST_BINARY} failed to execute"
            OVERALL_STATUS="fail"
        fi
    fi
fi

# ============================================================================
# Test 4: Library Linkage (ldd)
# ============================================================================
if [[ "$CHATTY" == true ]]; then echo "Test 4: library_linkage" >&2; fi

SO_FILES=$(capture_chroot "rpm -ql ${SPEC} 2>/dev/null" | grep -E '\.so(\.|$)' || true)

if [[ -z "$SO_FILES" ]]; then
    add_check "library_linkage" "skip" "no shared libraries found"
else
    LDD_FAILED=false
    LDD_DETAIL=""
    while IFS= read -r so_file; do
        [[ -z "$so_file" ]] && continue
        LDD_OUTPUT=$(capture_chroot "ldd ${so_file} 2>&1" || true)
        if echo "$LDD_OUTPUT" | grep -q "not found"; then
            LDD_FAILED=true
            NOT_FOUND=$(echo "$LDD_OUTPUT" | grep "not found" | head -3 | tr '\n' ';')
            LDD_DETAIL+="${so_file}: unresolved: ${NOT_FOUND} "
        fi
    done <<< "$SO_FILES"

    if [[ "$LDD_FAILED" == true ]]; then
        add_check "library_linkage" "fail" "${LDD_DETAIL}"
        add_failure "library_linkage" "Unresolved library dependencies for ${SPEC}"
        OVERALL_STATUS="fail"
    else
        add_check "library_linkage" "pass"
    fi
fi

# ============================================================================
# Test 5: Multiarch Check
# ============================================================================
if [[ "$CHATTY" == true ]]; then echo "Test 5: multiarch" >&2; fi

if [[ -z "$SO_FILES" ]]; then
    # No shared libs = skip multiarch check
    add_check "multiarch" "skip" "no shared libraries, multiarch check skipped"
else
    # Determine expected lib path based on arch
    if [[ "$ARCH" == "x86_64" ]]; then
        MULTIARCH_LIBDIRS="/usr/lib64 /usr/lib/x86_64-linux-gnu"
    elif [[ "$ARCH" == "i686" ]]; then
        MULTIARCH_LIBDIRS="/usr/lib /usr/lib/i386-linux-gnu"
    else
        MULTIARCH_LIBDIRS="/usr/lib"
    fi

    MULTIARCH_MISSING=false
    MULTIARCH_DETAIL=""
    for libdir in $MULTIARCH_LIBDIRS; do
        DIR_EXISTS=$(capture_chroot "test -d ${libdir} && echo yes || echo no")
        if [[ "$DIR_EXISTS" == "no" ]]; then
            MULTIARCH_MISSING=true
            MULTIARCH_DETAIL+="missing dir: ${libdir} "
        fi
    done

    if [[ "$MULTIARCH_MISSING" == true ]]; then
        add_check "multiarch" "fail" "${MULTIARCH_DETAIL}"
        add_failure "multiarch" "Missing expected library directories for arch ${ARCH}"
        OVERALL_STATUS="fail"
    else
        add_check "multiarch" "pass"
    fi
fi

# ============================================================================
# Build JSON Output
# ============================================================================
FAILURES_JSON="["
FAIL_SEP=""
for failure in "${FAILURES[@]}"; do
    FAILURES_JSON+="${FAIL_SEP}${failure}"
    FAIL_SEP=","
done
FAILURES_JSON+="]"

# Escape spec name for JSON
SPEC_ESCAPED="${SPEC//\"/\\\"}"

cat << EOF
{"spec":"${SPEC_ESCAPED}","arch":"${ARCH}","timestamp":"${TIMESTAMP}","status":"${OVERALL_STATUS}","checks":[${CHECKS_JSON}],"failures":${FAILURES_JSON}}
EOF

# Exit code: 0 if all required tests pass (rpm_installed + rpm_verify required)
if [[ "$OVERALL_STATUS" == "pass" ]]; then
    exit 0
else
    exit 1
fi
