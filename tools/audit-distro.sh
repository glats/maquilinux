#!/usr/bin/env bash
# tools/audit-distro.sh - Distro Health Audit Tool
# Quick health check: is my distro healthy in one command?

set -euo pipefail

# Script location (project root)
MQL_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export MQL_PROJECT_ROOT

# Load config (same as mql CLI)
source "$MQL_PROJECT_ROOT/mql.conf" 2>/dev/null || true
source "$MQL_PROJECT_ROOT/mql.local" 2>/dev/null || true

# Load common library
source "$MQL_PROJECT_ROOT/lib/common.sh"

# Load audit library
source "$MQL_PROJECT_ROOT/lib/audit.sh"

# ============================================================================
# Main
# ============================================================================

mql_audit "$@"