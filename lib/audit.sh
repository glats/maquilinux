#!/usr/bin/env bash
# lib/audit.sh - Distro health audit library functions
# Phase 1: Core audit logic for Maqui Linux

# Note: Do NOT set set -euo pipefail here - this is a sourced library
# Individual functions handle errors appropriately

# Guard against multiple sourcing
if [[ -n "${MQL_AUDIT_SOURCED:-}" ]]; then
    return 0
fi
readonly MQL_AUDIT_SOURCED=1

# Load common library
source "$MQL_PROJECT_ROOT/lib/common.sh"

# ============================================================================
# Audit Data Structures
# ============================================================================

# Global associative arrays for audit results
declare -A AUDIT_SPEC_STATUS=()       # spec -> status (ok|missing-local|missing-prod|version-drift|not-installed)
declare -A AUDIT_SPEC_LOCAL_RPM=()   # spec -> local rpm path (if found)
declare -A AUDIT_SPEC_PROD_RPM=()    # spec -> prod rpm path (if found)
declare -A AUDIT_SPEC_VERSION_SPEC=() # spec -> version from spec
declare -A AUDIT_SPEC_VERSION_RPM=()  # spec -> version from rpm
declare -A AUDIT_INSTALLED_PACKAGES=() # installed packages in chroot

# Audit summary counts
AUDIT_TOTAL_SPECS=0
AUDIT_MISSING_LOCAL=0
AUDIT_MISSING_PROD=0
AUDIT_VERSION_DRIFT=0
AUDIT_NOT_INSTALLED=0
AUDIT_HEALTHY=0

# RPM sequoia build chain
declare -a RPM_SEQUOIA_CHAIN=(
    "nettle"
    "libgpg-error"
    "libgcrypt"
    "libassuan"
    "gpgme"
    "libssh2"
    "llvm"
    "rust"
    "rpm-sequoia"
    "rpm"
)

# ============================================================================
# Helper Functions
# ============================================================================

# parse_spec_version <spec_file>
# Extracts Name, Version, Release from a spec file (first line only)
parse_spec_version() {
    local spec_file="$1"
    local name version release

    # Get first matching line only, extract everything after first whitespace
    name=$(grep -m1 -E '^Name:' "$spec_file" | sed 's/^Name:[[:space:]]*//' | tr -d '\n' || echo "")
    version=$(grep -m1 -E '^Version:' "$spec_file" | sed 's/^Version:[[:space:]]*//' | tr -d '\n' || echo "")
    release=$(grep -m1 -E '^Release:' "$spec_file" | sed 's/^Release:[[:space:]]*//' | tr -d '\n' || echo "")

    echo "${name}|${version}|${release}"
}

# rpm_name_to_spec_name <rpm_name>
# Converts an RPM filename to its likely spec name (remove arch, release, version)
rpm_name_to_spec_name() {
    local rpm="$1"
    local name
    # rpm格式: name-version-release.arch.rpm
    name=$(basename "$rpm" | sed 's/\.rpm$//' | sed 's/-[0-9].*//' | sed 's/\.x86_64$//' | sed 's/\.i686$//' | sed 's/\.noarch$//')
    echo "$name"
}

# find_rpm_in_dir <spec_name> <rpm_dir>
# Finds an RPM matching the spec name in a directory (returns first match)
find_rpm_in_dir() {
    local spec_name="$1"
    local rpm_dir="$2"

    if [[ ! -d "$rpm_dir" ]]; then
        echo ""
        return
    fi

    # Fast lookup using glob (avoid expensive find)
    local match

    # Try exact name with various extensions (version can have dots like 5.3)
    for pattern in \
        "${spec_name}-[0-9.]*.x86_64.rpm" \
        "${spec_name}-[0-9.]*.i686.rpm" \
        "${spec_name}-[0-9.]*.noarch.rpm" \
        "${spec_name}-[0-9.]*.rpm"
    do
        match=$(ls -1 "$rpm_dir"/$pattern 2>/dev/null | head -1)
        [[ -n "$match" ]] && break
    done

    echo "$match"
}

# get_rpm_version <rpm_file> <spec_name>
# Extracts version-release from RPM filename by removing name prefix and arch suffix
get_rpm_version() {
    local rpm="$1"
    local spec_name="$2"
    local basename_rpm
    basename_rpm=$(basename "$rpm")
    # Remove spec name prefix
    local ver_rel="${basename_rpm#${spec_name}-}"
    # Remove arch suffix
    ver_rel="${ver_rel%.x86_64.rpm}"
    ver_rel="${ver_rel%.i686.rpm}"
    ver_rel="${ver_rel%.noarch.rpm}"
    ver_rel="${ver_rel%.rpm}"
    echo "$ver_rel"
}

# rpm_installed_in_chroot <package_name>
# Checks if a package is installed in the chroot rootfs
rpm_installed_in_chroot() {
    local pkg="$1"
    local rootfs
    rootfs="$(get_rootfs_path)"

    # Try rpm -q in chroot (with timeout to avoid hanging)
    if mountpoint -q "$rootfs/merged" 2>/dev/null; then
        local chroot_cmd="chroot \"$rootfs/merged\" /bin/sh -c 'export PATH=/bin:/sbin:/usr/bin:/usr/sbin && rpm -q \"$pkg\"'"
        if [[ $(id -u) -eq 0 ]]; then
            timeout 5 bash -c "$chroot_cmd" >/dev/null 2>&1
        else
            timeout 5 sudo bash -c "$chroot_cmd" >/dev/null 2>&1
        fi
        return $?
    fi

    return 1

    return 1
}

# get_repodata_timestamp <repo_dir>
# Returns modification time of repodata directory
get_repodata_timestamp() {
    local repo_dir="$1"
    local repodata="$repo_dir/repodata"

    if [[ -d "$repodata" ]]; then
        stat -c %Y "$repodata" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# get_newest_rpm_timestamp <repo_dir>
# Returns modification time of newest RPM in repo
get_newest_rpm_timestamp() {
    local repo_dir="$1"

    if [[ ! -d "$repo_dir" ]]; then
        echo "0"
        return
    fi

    local newest
    newest=$(find "$repo_dir" -maxdepth 1 -name "*.rpm" -type f -printf '%T@\n' 2>/dev/null | sort -rn | head -1)
    if [[ -n "$newest" ]]; then
        printf "%.0f" "$newest"
    else
        echo "0"
    fi
}

# ============================================================================
# Core Audit Functions
# ============================================================================

# audit_init
# Initialize/reset audit state
audit_init() {
    AUDIT_SPEC_STATUS=()
    AUDIT_SPEC_LOCAL_RPM=()
    AUDIT_SPEC_PROD_RPM=()
    AUDIT_SPEC_VERSION_SPEC=()
    AUDIT_SPEC_VERSION_RPM=()
    AUDIT_INSTALLED_PACKAGES=()
    AUDIT_TOTAL_SPECS=0
    AUDIT_MISSING_LOCAL=0
    AUDIT_MISSING_PROD=0
    AUDIT_VERSION_DRIFT=0
    AUDIT_NOT_INSTALLED=0
    AUDIT_HEALTHY=0
}

# audit_specs
# Main function: audit all specs
audit_specs() {
    local specs_dir="$MQL_PROJECT_ROOT/SPECS"
    local local_rpms_dir="$MQL_PROJECT_ROOT/RPMS"
    local prod_rpms_dir
    # Production repo: /srv/glats/nginx/repo/linux/maquilinux/26.4/x86_64/stable/
    local releasever="${MQL_RELEASEVER:-26.4}"
    prod_rpms_dir="${MQL_REPO_PROD:-/srv/glats/nginx/repo/linux/maquilinux/${releasever}/x86_64/stable}"

    # Detect arch subdirs in local RPMS (including noarch)
    local archs=()
    for d in "$local_rpms_dir"/*/; do
        [[ -d "$d" ]] || continue
        local arch
        arch=$(basename "$d")
        [[ "$arch" == "repodata" ]] && continue
        archs+=("$arch")
    done
    # Also check noarch if not already included
    if [[ -d "$local_rpms_dir/noarch" ]] && [[ ! " ${archs[*]} " =~ " noarch " ]]; then
        archs+=("noarch")
    fi

    log_step "Auditing $specs_dir ..."

    # Cache installed packages list
    cache_installed_packages

    # Iterate all spec files
    for spec_file in "$specs_dir"/*.spec; do
        [[ -f "$spec_file" ]] || continue

        local spec_name
        spec_name=$(basename "$spec_file" .spec)

        AUDIT_TOTAL_SPECS=$((AUDIT_TOTAL_SPECS + 1))

        # Parse spec version
        local parsed
        parsed=$(parse_spec_version "$spec_file")
        local spec_version
        spec_version=$(echo "$parsed" | cut -d'|' -f2)
        AUDIT_SPEC_VERSION_SPEC["$spec_name"]="$spec_version"

        # Find local RPM (check all arch directories)
        local local_rpm=""
        for arch in "${archs[@]}"; do
            local found
            found=$(find_rpm_in_dir "$spec_name" "$local_rpms_dir/$arch")
            if [[ -n "$found" ]]; then
                local_rpm="$found"
                break
            fi
        done

        if [[ -n "$local_rpm" ]]; then
            AUDIT_SPEC_LOCAL_RPM["$spec_name"]="$local_rpm"
            local rpm_ver
            rpm_ver=$(get_rpm_version "$local_rpm" "$spec_name")
            AUDIT_SPEC_VERSION_RPM["$spec_name"]="$rpm_ver"

            # Check version drift (compare spec version vs rpm version-release)
            # Skip drift check if spec uses macros we can't resolve
            local ver_from_rpm
            ver_from_rpm=$(echo "$rpm_ver" | sed 's/-[0-9].*//')
            if [[ "$spec_version" == *"%{"* ]] || [[ "$spec_version" == *"%"* ]]; then
                # Spec uses macros - can't reliably compare, assume ok
                AUDIT_SPEC_STATUS["$spec_name"]="ok"
                AUDIT_HEALTHY=$((AUDIT_HEALTHY + 1))
            elif [[ "$spec_version" != "$ver_from_rpm" ]]; then
                AUDIT_SPEC_STATUS["$spec_name"]="version-drift"
                AUDIT_VERSION_DRIFT=$((AUDIT_VERSION_DRIFT + 1))
            else
                AUDIT_SPEC_STATUS["$spec_name"]="ok"
                AUDIT_HEALTHY=$((AUDIT_HEALTHY + 1))
            fi
        else
            AUDIT_SPEC_STATUS["$spec_name"]="missing-local"
            AUDIT_SPEC_LOCAL_RPM["$spec_name"]=""
            AUDIT_MISSING_LOCAL=$((AUDIT_MISSING_LOCAL + 1))
        fi

        # Find prod RPM
        if [[ -d "$prod_rpms_dir" ]]; then
            local prod_rpm
            prod_rpm=$(find_rpm_in_dir "$spec_name" "$prod_rpms_dir")
            if [[ -n "$prod_rpm" ]]; then
                AUDIT_SPEC_PROD_RPM["$spec_name"]="$prod_rpm"
            fi
        fi

        # Check if installed in chroot (only for specs with RPMs)
        if [[ -n "$local_rpm" ]]; then
            if ! rpm_installed_in_chroot "$spec_name" 2>/dev/null; then
                if [[ "${AUDIT_SPEC_STATUS["$spec_name"]}" == "ok" ]]; then
                    AUDIT_SPEC_STATUS["$spec_name"]="not-installed"
                    AUDIT_NOT_INSTALLED=$((AUDIT_NOT_INSTALLED + 1))
                    AUDIT_HEALTHY=$((AUDIT_HEALTHY - 1))
                fi
            fi
        fi

        # Update prod status (count all specs missing from production repo)
        if [[ -z "${AUDIT_SPEC_PROD_RPM["$spec_name"]:-}" ]]; then
            AUDIT_MISSING_PROD=$((AUDIT_MISSING_PROD + 1))
        fi
    done

    log_ok "Audited $AUDIT_TOTAL_SPECS specs"
}

# cache_installed_packages
# Cache list of installed packages in chroot
cache_installed_packages() {
    local rootfs
    rootfs="$(get_rootfs_path)"

    if ! mountpoint -q "$rootfs/merged" 2>/dev/null; then
        log_warn "Chroot not mounted at $rootfs/merged - skipping installed package check"
        return
    fi

    log_step "Caching installed packages ..."
    local rpm_list=""
    if [[ $(id -u) -eq 0 ]]; then
        rpm_list=$(timeout 30 chroot "$rootfs/merged" /bin/sh -c 'export PATH=/bin:/sbin:/usr/bin:/usr/sbin && rpm -qa --queryformat "%{NAME}\n"' 2>/dev/null || true)
    elif command -v sudo >/dev/null 2>&1; then
        rpm_list=$(timeout 30 sudo chroot "$rootfs/merged" /bin/sh -c 'export PATH=/bin:/sbin:/usr/bin:/usr/sbin && rpm -qa --queryformat "%{NAME}\n"' 2>/dev/null || true)
    else
        log_warn "Cannot check installed packages (need root or sudo)"
        return
    fi

    while IFS= read -r pkg; do
        [[ -n "$pkg" ]] && AUDIT_INSTALLED_PACKAGES["$pkg"]=1
    done <<< "$rpm_list"

    log_ok "Cached ${#AUDIT_INSTALLED_PACKAGES[@]} installed packages"
}

# audit_rpm_sequoia_chain
# Check the rpm-sequoia build dependency chain
audit_rpm_sequoia_chain() {
    log_step "Checking rpm-sequoia build chain ..."

    local chain_status=()
    local all_ok=true

    for pkg in "${RPM_SEQUOIA_CHAIN[@]}"; do
        if [[ -n "${AUDIT_INSTALLED_PACKAGES[$pkg]:-}" ]]; then
            chain_status+=("ok:$pkg")
        else
            chain_status+=("missing:$pkg")
            all_ok=false
        fi
    done

    if $all_ok; then
        log_ok "rpm-sequoia chain complete"
    else
        log_warn "rpm-sequoia chain incomplete"
        for status in "${chain_status[@]}"; do
            local state pkg
            state="${status%%:*}"
            pkg="${status#*:}"
            if [[ "$state" == "ok" ]]; then
                echo "  ${COLOR_GREEN}[OK]${COLOR_NC}   $pkg"
            else
                echo "  ${COLOR_RED}[MISS]${COLOR_NC} $pkg"
            fi
        done
    fi

    echo ""
}

# audit_repo_freshness
# Check if repo metadata is up to date
audit_repo_freshness() {
    log_step "Checking repo metadata freshness ..."

    local local_rpms_dir="$MQL_PROJECT_ROOT/RPMS/x86_64"
    local repodata_ts newest_rpm_ts

    repodata_ts=$(get_repodata_timestamp "$local_rpms_dir")
    newest_rpm_ts=$(get_newest_rpm_timestamp "$local_rpms_dir")

    if [[ "$repodata_ts" == "0" ]]; then
        log_warn "No repodata found in $local_rpms_dir"
        return
    fi

    if [[ "$newest_rpm_ts" == "0" ]]; then
        log_warn "No RPMs found in $local_rpms_dir"
        return
    fi

    if [[ "$newest_rpm_ts" -gt "$repodata_ts" ]]; then
        log_warn "Repo metadata is stale (RPMs newer than repodata)"
        echo "  Run: mql repo update"
    else
        log_ok "Repo metadata is up to date"
    fi

    echo ""
}

# ============================================================================
# Output Formatters
# ============================================================================

# json_escape <string>
# Escape a string for JSON
json_escape() {
    local str="$1"
    str="${str//\\/\\\\}"
    str="${str//\"/\\\"}"
    str="${str//$'\n'/\\n}"
    str="${str//$'\r'/\\r}"
    str="${str//$'\t'/\\t}"
    echo "$str"
}

# output_json
# Output audit results as JSON
output_json() {
    local healthy=false
    [[ $AUDIT_MISSING_LOCAL -eq 0 ]] && [[ $AUDIT_MISSING_PROD -eq 0 ]] && [[ $AUDIT_VERSION_DRIFT -eq 0 ]] && [[ $AUDIT_NOT_INSTALLED -eq 0 ]] && healthy=true

    printf "{\n"
    printf '  "healthy": %s,\n' "$healthy"
    printf "  \"summary\": {\n"
    printf "    \"total_specs\": %d,\n" "$AUDIT_TOTAL_SPECS"
    printf "    \"healthy\": %d,\n" "$AUDIT_HEALTHY"
    printf "    \"missing_local\": %d,\n" "$AUDIT_MISSING_LOCAL"
    printf "    \"missing_prod\": %d,\n" "$AUDIT_MISSING_PROD"
    printf "    \"version_drift\": %d,\n" "$AUDIT_VERSION_DRIFT"
    printf "    \"not_installed\": %d\n" "$AUDIT_NOT_INSTALLED"
    printf "  },\n"

    # Build issue lists
    local -a missing_local_specs version_drift_specs not_installed_specs
    for spec in "${!AUDIT_SPEC_STATUS[@]}"; do
        case "${AUDIT_SPEC_STATUS[$spec]}" in
            missing-local) missing_local_specs+=("$spec") ;;
            version-drift) version_drift_specs+=("$spec") ;;
            not-installed) not_installed_specs+=("$spec") ;;
        esac
    done

    # Helper function to output sorted JSON array
    # Usage: output_json_array "prefix" "arr[@]"
    output_json_array() {
        local prefix="$1"
        shift
        local -a arr=("$@")
        printf '%s [' "$prefix"
        if [[ ${#arr[@]} -gt 0 ]]; then
            local -a sorted
            IFS=$'\n' sorted=($(for s in "${arr[@]}"; do echo "$s"; done | sort)); unset IFS
            for ((i=0; i<${#sorted[@]}; i++)); do
                [[ $i -gt 0 ]] && printf ", "
                printf "\"%s\"" "$(json_escape "${sorted[$i]}")"
            done
        fi
        printf ']\n'
    }

    printf '  "issues": {\n'
    output_json_array '    "missing_local":' "${missing_local_specs[@]}"
    printf ',\n'
    output_json_array '    "version_drift_specs":' "${version_drift_specs[@]}"
    printf ',\n'
    output_json_array '    "not_installed_specs":' "${not_installed_specs[@]}"
    printf "\n  },\n"

    printf '  "specs": {\n'
    local -a sorted_specs
    IFS=$'\n' sorted_specs=($(for s in "${!AUDIT_SPEC_STATUS[@]}"; do echo "$s"; done | sort)); unset IFS
    for ((i=0; i<${#sorted_specs[@]}; i++)); do
        [[ $i -gt 0 ]] && printf ",\n"
        spec="${sorted_specs[$i]}"
        printf '    "%s": {' "$(json_escape "$spec")"
        printf ' "status": "%s",' "$(json_escape "${AUDIT_SPEC_STATUS[$spec]:-}")"
        printf ' "spec_version": "%s",' "$(json_escape "${AUDIT_SPEC_VERSION_SPEC[$spec]:-}")"
        printf ' "rpm_version": "%s",' "$(json_escape "${AUDIT_SPEC_VERSION_RPM[$spec]:-}")"
        printf ' "local_rpm": "%s",' "$(json_escape "${AUDIT_SPEC_LOCAL_RPM[$spec]:-}")"
        printf ' "prod_rpm": "%s"' "$(json_escape "${AUDIT_SPEC_PROD_RPM[$spec]:-}")"
        printf '}'
    done
    printf "\n  }\n"
    printf "}\n"
}

# output_brief
# Output one-line summary
output_brief() {
    local status="PASS"
    local color="$COLOR_GREEN"

    if [[ $AUDIT_MISSING_LOCAL -gt 0 ]] || [[ $AUDIT_VERSION_DRIFT -gt 0 ]] || [[ $AUDIT_NOT_INSTALLED -gt 0 ]]; then
        status="FAIL"
        color="$COLOR_RED"
    fi

    echo -e "${color}[${status}]${COLOR_NC} Specs: $AUDIT_TOTAL_SPECS | OK: $AUDIT_HEALTHY | MissingLocal: $AUDIT_MISSING_LOCAL | MissingProd: $AUDIT_MISSING_PROD | Drift: $AUDIT_VERSION_DRIFT | NotInstalled: $AUDIT_NOT_INSTALLED"
}

# output_human
# Output human-readable colored summary
output_human() {
    echo ""
    echo "============================================================"
    echo "  DISTRO HEALTH AUDIT"
    echo "============================================================"
    echo ""

    # Summary counts
    echo -e "${COLOR_CYAN}Summary:${COLOR_NC}"
    printf "  Total specs:     %d\n" "$AUDIT_TOTAL_SPECS"
    printf "  Healthy:         ${COLOR_GREEN}%d${COLOR_NC}\n" "$AUDIT_HEALTHY"
    printf "  Missing local:   ${COLOR_RED}%d${COLOR_NC}\n" "$AUDIT_MISSING_LOCAL"
    printf "  Missing prod:    ${COLOR_YELLOW}%d${COLOR_NC}\n" "$AUDIT_MISSING_PROD"
    printf "  Version drift:   ${COLOR_YELLOW}%d${COLOR_NC}\n" "$AUDIT_VERSION_DRIFT"
    printf "  Not installed:   ${COLOR_YELLOW}%d${COLOR_NC}\n" "$AUDIT_NOT_INSTALLED"
    echo ""

    # Overall status
    if [[ $AUDIT_MISSING_LOCAL -gt 0 ]] || [[ $AUDIT_MISSING_PROD -gt 0 ]] || [[ $AUDIT_VERSION_DRIFT -gt 0 ]] || [[ $AUDIT_NOT_INSTALLED -gt 0 ]]; then
        echo -e "${COLOR_RED}Status: UNHEALTHY${COLOR_NC} - issues found"
    else
        echo -e "${COLOR_GREEN}Status: HEALTHY${COLOR_NC} - all specs have RPMs and match versions"
    fi
    echo ""

    # Detailed lists
    if [[ $AUDIT_MISSING_LOCAL -gt 0 ]]; then
        echo -e "${COLOR_RED}Specs without local RPMs:${COLOR_NC}"
        for spec in "${!AUDIT_SPEC_STATUS[@]}"; do
            if [[ "${AUDIT_SPEC_STATUS[$spec]}" == "missing-local" ]]; then
                printf "  - %s\n" "$spec"
            fi
        done
        echo ""
    fi

    if [[ $AUDIT_MISSING_PROD -gt 0 ]]; then
        echo -e "${COLOR_YELLOW}Specs not in production repo:${COLOR_NC}"
        for spec in "${!AUDIT_SPEC_STATUS[@]}"; do
            if [[ -z "${AUDIT_SPEC_PROD_RPM[$spec]:-}" ]]; then
                printf "  - %s\n" "$spec"
            fi
        done
        echo ""
    fi

    if [[ $AUDIT_VERSION_DRIFT -gt 0 ]]; then
        echo -e "${COLOR_YELLOW}Specs with version drift:${COLOR_NC}"
        for spec in "${!AUDIT_SPEC_STATUS[@]}"; do
            if [[ "${AUDIT_SPEC_STATUS[$spec]}" == "version-drift" ]]; then
                printf "  - %s (spec: %s, rpm: %s)\n" "$spec" "${AUDIT_SPEC_VERSION_SPEC[$spec]:-}" "${AUDIT_SPEC_VERSION_RPM[$spec]:-}"
            fi
        done
        echo ""
    fi

    if [[ $AUDIT_NOT_INSTALLED -gt 0 ]]; then
        echo -e "${COLOR_YELLOW}Specs with RPM but not installed in chroot:${COLOR_NC}"
        for spec in "${!AUDIT_SPEC_STATUS[@]}"; do
            if [[ "${AUDIT_SPEC_STATUS[$spec]}" == "not-installed" ]]; then
                printf "  - %s\n" "$spec"
            fi
        done
        echo ""
    fi
}

# output_fix
# Generate shell commands to rebuild missing packages
output_fix() {
    echo "#!/bin/bash"
    echo "# Auto-generated fix script for missing packages"
    echo "# Run this to rebuild all packages without local RPMs"
    echo ""
    echo "set -e"

    local missing=()
    for spec in "${!AUDIT_SPEC_STATUS[@]}"; do
        if [[ "${AUDIT_SPEC_STATUS[$spec]}" == "missing-local" ]]; then
            missing+=("$spec")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo ""
        echo "# Missing packages (${#missing[@]}):"
        for spec in "${missing[@]}"; do
            printf '# mql build %s\n' "$spec"
        done
        echo ""
        echo "# Build all missing:"
        printf "mql build %s \\\n" "${missing[@]}" | sed 's/ \\$//'
        echo ""
    else
        echo "# No missing packages found"
    fi
}

# ============================================================================
# CLI Dispatcher
# ============================================================================

mql_audit() {
    local format="human"
    local run_chain=true
    local run_freshness=true

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --json)  format="json"; run_chain=false; run_freshness=false; shift ;;
            --brief) format="brief"; shift ;;
            --fix)   format="fix"; shift ;;
            --no-chain)    run_chain=false; shift ;;
            --no-freshness) run_freshness=false; shift ;;
            --help|-h)
                echo "Usage: mql audit [--json|--brief|--fix] [--no-chain] [--no-freshness]"
                echo ""
                echo "Options:"
                echo "  --json          Machine-readable JSON output"
                echo "  --brief         One-line summary (pass/fail with counts)"
                echo "  --fix           Generate shell commands to rebuild missing"
                echo "  --no-chain      Skip rpm-sequoia build chain check"
                echo "  --no-freshness  Skip repo metadata freshness check"
                echo "  --help          Show this help"
                return 0
                ;;
            *)
                shift ;;
        esac
    done

    # Initialize and run audit
    audit_init
    audit_specs

    # Additional checks (skip for fix mode)
    if [[ "$format" != "fix" ]]; then
        [[ "$run_chain" == "true" ]] && audit_rpm_sequoia_chain
        [[ "$run_freshness" == "true" ]] && audit_repo_freshness
    fi

    # Output based on format
    case "$format" in
        json)   output_json ;;
        brief)  output_brief ;;
        fix)    output_fix ;;
        *)      output_human ;;
    esac

    # Return exit code based on health
    if [[ $AUDIT_MISSING_LOCAL -gt 0 ]] || [[ $AUDIT_MISSING_PROD -gt 0 ]] || [[ $AUDIT_VERSION_DRIFT -gt 0 ]] || [[ $AUDIT_NOT_INSTALLED -gt 0 ]]; then
        return 1
    fi
    return 0
}

# EOF