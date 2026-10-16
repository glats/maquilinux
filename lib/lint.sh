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

# lint_parse_args [--report] [file...]
# Sets LINT_REPORT (0|1) and LINT_FILES. Unknown options and missing files
# fail, so a typo can never produce a false green.
lint_parse_args() {
    LINT_REPORT=0
    LINT_FILES=()
    local arg
    for arg in "$@"; do
        case "$arg" in
            --report) LINT_REPORT=1 ;;
            -*) log_error "Unknown option: $arg"; return 2 ;;
            *)
                if [[ ! -f "$arg" ]]; then
                    log_error "No such file: $arg"
                    return 2
                fi
                LINT_FILES+=("$arg")
                ;;
        esac
    done
}

# ============================================================================
# lint spec: Maqui spec conventions (agent_docs/spec-conventions.md)
#   SPEC-RELEASE    Release is N.m<YY><M> with optional %{?dist}, from MQL_RELEASEVER
#   SPEC-DEBUG      debug packages disabled: %define|%global debug_package %{nil}
#   SPEC-LICENSE    License: field present
#   SPEC-CHANGELOG  %changelog section present
# ============================================================================

# spec_violations <spec> <tag>
spec_violations() {
    local spec="$1" tag="$2" release
    release=$(sed -nE 's/^Release:[[:space:]]*//p' "$spec" | head -1 | sed -E 's/[[:space:]]+$//')
    if [[ ! "$release" =~ ^[0-9]+\.${tag}(%\{\?dist\})?$ ]]; then
        echo "SPEC-RELEASE: ${release:-<missing>} (want N.${tag})"
    fi
    grep -qE '^%(define|global)[[:space:]]+debug_package[[:space:]]+%\{nil\}' "$spec" \
        || echo "SPEC-DEBUG: missing '%global debug_package %{nil}'"
    grep -qE '^License:' "$spec" || echo "SPEC-LICENSE: missing License field"
    grep -qE '^%changelog' "$spec" || echo "SPEC-CHANGELOG: missing %changelog"
}

# lint_spec [--report] [spec...]
# Defaults to SPECS/*.spec. Exit 1 on any violation unless --report.
lint_spec() {
    lint_parse_args "$@" || return 2
    local specs=("${LINT_FILES[@]}")
    if [[ ${#specs[@]} -eq 0 ]]; then
        shopt -s nullglob
        specs=("$MQL_PROJECT_ROOT"/SPECS/*.spec)
        shopt -u nullglob
    fi

    # 26.4 -> m264; 26.10 -> m2610
    local tag="m${MQL_RELEASEVER:-26.4}"
    tag="${tag//./}"

    local count=0 spec line
    for spec in "${specs[@]}"; do
        while IFS= read -r line; do
            echo "$(basename "$spec"): $line"
            count=$((count + 1))
        done < <(spec_violations "$spec" "$tag")
    done

    echo "lint spec: ${#specs[@]} spec(s), $count violation(s)"
    [[ $LINT_REPORT -eq 1 || $count -eq 0 ]]
}

# ============================================================================
# lint docs: repository paths cited in agent docs must exist
#   DOC-PATH  a backticked repo path (agent_docs/, docs/, lib/, scripts/,
#             SPECS/, SOURCES/, tests/, odd/, .github/) that does not exist.
#             Globs and <placeholders> are skipped.
# ============================================================================

readonly LINT_DOC_ROOTS='(agent_docs|docs|lib|scripts|SPECS|SOURCES|tests|odd|\.github)/'

# doc_violations <file>
doc_violations() {
    local file="$1" n path
    while IFS=: read -r n path; do
        [[ "$path" == *[\*\<\>\$\{]* ]] && continue
        [[ -e "$MQL_PROJECT_ROOT/$path" ]] || echo "$file:$n: DOC-PATH: $path"
    done < <(grep -noE "\`${LINT_DOC_ROOTS}[^\` ]+\`" "$file" 2>/dev/null \
        | sed -E 's/`//g' | grep -E "^[0-9]+:${LINT_DOC_ROOTS}" || true)
}

# lint_docs [--report] [file...]
# Defaults to AGENTS.md, CONTRIBUTING.md, README.md, agent_docs/, docs/,
# and .opencode/agents/.
lint_docs() {
    lint_parse_args "$@" || return 2
    local files=("${LINT_FILES[@]}")
    if [[ ${#files[@]} -eq 0 ]]; then
        mapfile -t files < <(git -C "$MQL_PROJECT_ROOT" ls-files \
            AGENTS.md CONTRIBUTING.md README.md 'agent_docs/*.md' 'docs/*.md' \
            '.opencode/agents/*.md' \
            | sed "s|^|$MQL_PROJECT_ROOT/|")
    fi

    local count=0 line f
    for f in "${files[@]}"; do
        while IFS= read -r line; do
            echo "${line#"$MQL_PROJECT_ROOT"/}"
            count=$((count + 1))
        done < <(doc_violations "$f")
    done

    echo "lint docs: ${#files[@]} file(s), $count violation(s)"
    [[ $LINT_REPORT -eq 1 || $count -eq 0 ]]
}

# lint_endpoints [--report] [file...]
# Defaults to git-tracked files minus LINT_ENDPOINTS_EXCLUDE. Exit 1 on any
# violation unless --report.
lint_endpoints() {
    lint_parse_args "$@" || return 2
    local report=$LINT_REPORT files=("${LINT_FILES[@]}")

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
        spec) lint_spec "$@" ;;
        docs) lint_docs "$@" ;;
        *)
            log_error "Unknown lint subcommand: ${subcmd:-<none>} (available: fhs, spec, docs, endpoints)"
            return 1
            ;;
    esac
}
