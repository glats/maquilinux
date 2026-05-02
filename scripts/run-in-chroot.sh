#!/usr/bin/env bash
# scripts/run-in-chroot.sh - Run commands inside Maqui Linux chroot
#
# Usage: ./run-in-chroot.sh [options] <command>
#
# Options:
#   --preserve-env  Keep current environment variables inside chroot
#   --              End of options, rest is the command
#
# Prerequisites:
#   - Overlay must be mounted (run: mql chroot --mount first)
#   - Workspace bind-mounted at $MQL_ROOTFS/merged/mnt/workspace
#
# Examples:
#   ./run-in-chroot.sh rpmbuild -ba SPECS/bash.spec
#   ./run-in-chroot.sh mql backup create pre-rust
#   ./run-in-chroot.sh --preserve-env bash -c 'echo $HOME'

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"

# Resolve rootfs path from config/env
MQL_PROJECT_ROOT="${MQL_PROJECT_ROOT:-$(dirname "$SCRIPT_DIR")}"
export MQL_PROJECT_ROOT

# Load configuration (order: mql.conf then mql.local)
if [[ -f "$MQL_PROJECT_ROOT/mql.conf" ]]; then
    source "$MQL_PROJECT_ROOT/mql.conf" 2>/dev/null || true
fi
if [[ -f "$MQL_PROJECT_ROOT/mql.local" ]]; then
    source "$MQL_PROJECT_ROOT/mql.local" 2>/dev/null || true
fi

# shellcheck source=../lib/chroot.sh
source "$SCRIPT_DIR/../lib/chroot.sh"

# Parse arguments
preserve_env=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --preserve-env)
            preserve_env=true
            shift
            ;;
        --)
            shift
            break
            ;;
        -*)
            log_error "Unknown option: $1"
            log_info "Usage: $0 [--preserve-env] <command>"
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -eq 0 ]]; then
    log_error "No command specified"
    log_info "Usage: $0 [--preserve-env] <command>"
    exit 1
fi

# Delegate to lib/chroot.sh
if [[ "$preserve_env" == "true" ]]; then
    mql_chroot_exec "$*" "--preserve-env"
else
    mql_chroot_exec "$*"
fi
