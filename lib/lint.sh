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

mql_lint() {
    local subcmd="${1:-}"
    shift || true
    case "$subcmd" in
        fhs) lint_fhs "$@" ;;
        *)
            log_error "Unknown lint subcommand: ${subcmd:-<none>} (available: fhs)"
            return 1
            ;;
    esac
}
