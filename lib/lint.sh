#!/usr/bin/env bash
# lib/lint.sh - Policy lints for Maqui Linux packages
#
# `mql lint fhs` checks built RPM file lists against the Debian filesystem
# hierarchy rules Maqui follows (Debian Policy 9.1.1, on top of FHS 3.0):
#   FHS-USR-LIB64  no files under /usr/lib64
#   FHS-LIB64      only the dynamic linker may live under /lib64
#   FHS-TRIPLET    a package installs only into its own architecture triplet
#   FHS-LIB32      no files under /lib32 or /usr/lib32 (Maqui uses the i386 triplet)
# /usr/libexec is permitted by FHS 3.0 and is not flagged.

source "$MQL_PROJECT_ROOT/lib/common.sh"

readonly LINT_LOADER_X86_64="/lib64/ld-linux-x86-64.so.2"

# fhs_violations <arch>
# Reads one path per line on stdin; prints "<RULE>: <path>" per violation.
fhs_violations() {
    local arch="$1" foreign=""
    case "$arch" in
        x86_64) foreign="i386-linux-gnu" ;;
        i686|i386) foreign="x86_64-linux-gnu" ;;
    esac

    local path
    while IFS= read -r path; do
        [[ -n "$path" && "$path" != "(contains no files)" ]] || continue
        case "$path" in
            /usr/lib64/*)
                echo "FHS-USR-LIB64: $path" ;;
            /lib64/*)
                [[ "$path" == "$LINT_LOADER_X86_64" ]] || echo "FHS-LIB64: $path" ;;
            /lib32/*|/usr/lib32/*)
                echo "FHS-LIB32: $path" ;;
        esac
        if [[ -n "$foreign" ]]; then
            case "$path" in
                "/usr/lib/$foreign"|"/usr/lib/$foreign/"*|"/lib/$foreign"|"/lib/$foreign/"*)
                    echo "FHS-TRIPLET: $path" ;;
            esac
        fi
    done
}

# lint_fhs [rpm...]
# Defaults to every RPM under $MQL_PROJECT_ROOT/RPMS. Exit 1 on any violation.
lint_fhs() {
    if ! command -v rpm &>/dev/null; then
        log_error "lint fhs needs 'rpm' on PATH (on NixOS: nix shell nixpkgs#rpm)"
        return 2
    fi

    local rpms=("$@")
    if [[ ${#rpms[@]} -eq 0 ]]; then
        shopt -s nullglob
        rpms=("$MQL_PROJECT_ROOT"/RPMS/*/*.rpm)
        shopt -u nullglob
    fi
    if [[ ${#rpms[@]} -eq 0 ]]; then
        log_error "No RPMs to lint"
        return 2
    fi

    local count=0 rpm_file arch line
    for rpm_file in "${rpms[@]}"; do
        arch=$(rpm -qp --qf '%{ARCH}' "$rpm_file")
        while IFS= read -r line; do
            echo "$(basename "$rpm_file"): $line"
            count=$((count + 1))
        done < <(rpm -qlp "$rpm_file" | fhs_violations "$arch")
    done

    echo "lint fhs: ${#rpms[@]} package(s), $count violation(s)"
    [[ $count -eq 0 ]]
}

# ============================================================================
# lint endpoints: public names never name machines (ODD distro-quality-stack S10)
#   EP-HOST     mDNS machine names (*.local); the name is not printed
#   EP-LEGACY   legacy public domains (MQL_LINT_LEGACY_DOMAINS); use canonical names
#   EP-PRIVATE  patterns from MQL_LINT_PRIVATE_PATTERNS, set only in mql.local or
#               CI variables; matches are not printed (the repository is public)
# ============================================================================

# Paths excluded from the default scan: history, design records, lint fixtures.
readonly LINT_ENDPOINTS_EXCLUDE='^(openspec|sdd|\.sdd|specs|odd)/|^tests/lint-endpoints\.bats$'

# endpoint_violations <file>
endpoint_violations() {
    local file="$1" d p re
    grep -noIE '\b[A-Za-z0-9-]+\.local\b' "$file" 2>/dev/null \
        | grep -vE ':mql\.local$' | cut -d: -f1 | sort -un \
        | sed "s|^|$file:|; s|$|: EP-HOST|" || true

    # Lines that configure this lint (MQL_LINT_*) name the legacy domains on purpose.
    local skip
    skip=" $( (grep -nE '^MQL_LINT_' "$file" 2>/dev/null || true) | cut -d: -f1 | tr '\n' ' ') "
    for d in ${MQL_LINT_LEGACY_DOMAINS:-glats.org}; do
        re="(^|[^@A-Za-z0-9.-])([A-Za-z0-9-]+\.)*${d//./\\.}"
        grep -noIE "$re" "$file" 2>/dev/null \
            | awk -F: -v skip="$skip" 'index(skip, " " $1 " ") == 0' \
            | sed -E "s|^([0-9]+):[^A-Za-z0-9]?|$file:\1: EP-LEGACY: |" | sort -u || true
    done

    for p in ${MQL_LINT_PRIVATE_PATTERNS:-}; do
        grep -nIE "$p" "$file" 2>/dev/null | cut -d: -f1 \
            | sed "s|^|$file:|; s|$|: EP-PRIVATE|" || true
    done
}

# lint_endpoints [--report] [file...]
# Defaults to git-tracked files minus LINT_ENDPOINTS_EXCLUDE. Exit 1 on any
# violation unless --report.
lint_endpoints() {
    local report=0 arg files=()
    for arg in "$@"; do
        case "$arg" in
            --report) report=1 ;;
            -*) log_error "Unknown option: $arg"; return 2 ;;
            *)
                if [[ ! -f "$arg" ]]; then
                    log_error "No such file: $arg"
                    return 2
                fi
                files+=("$arg")
                ;;
        esac
    done

    # A broken private pattern must fail the gate, never pass it silently.
    local p rc
    for p in ${MQL_LINT_PRIVATE_PATTERNS:-}; do
        rc=0
        grep -qE "$p" </dev/null 2>/dev/null || rc=$?
        if [[ $rc -gt 1 ]]; then
            log_error "Invalid pattern in MQL_LINT_PRIVATE_PATTERNS (entry hidden)"
            return 2
        fi
    done

    if [[ ${#files[@]} -eq 0 ]]; then
        mapfile -t files < <(git -C "$MQL_PROJECT_ROOT" ls-files \
            | grep -vE "$LINT_ENDPOINTS_EXCLUDE" | sed "s|^|$MQL_PROJECT_ROOT/|")
    fi

    local count=0 line f
    for f in "${files[@]}"; do
        [[ -f "$f" ]] || continue
        while IFS= read -r line; do
            echo "${line#"$MQL_PROJECT_ROOT"/}"
            count=$((count + 1))
        done < <(endpoint_violations "$f")
    done

    echo "lint endpoints: ${#files[@]} file(s), $count violation(s)"
    [[ $report -eq 1 || $count -eq 0 ]]
}

mql_lint() {
    local subcmd="${1:-}"
    shift || true
    case "$subcmd" in
        fhs) lint_fhs "$@" ;;
        endpoints) lint_endpoints "$@" ;;
        *)
            log_error "Unknown lint subcommand: ${subcmd:-<none>} (available: fhs, endpoints)"
            return 1
            ;;
    esac
}
