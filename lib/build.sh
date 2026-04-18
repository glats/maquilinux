#!/usr/bin/env bash
# lib/build.sh - Build RPMs for Maqui Linux
# Phase 1: Wrapper around scripts/build-spec.sh

set -euo pipefail

# Load common library (MQL_PROJECT_ROOT exported by mql)
source "$MQL_PROJECT_ROOT/lib/common.sh"

# Show spec info (placeholder)
show_spec_info() {
    local spec_name="$1"
    local spec_file="$MQL_PROJECT_ROOT/SPECS/${spec_name}.spec"
    
    if [[ ! -f "$spec_file" ]]; then
        log_error "Spec not found: $spec_name"
        exit 1
    fi
    
    log_step "Spec info: $spec_name"
    echo "File: $spec_file"
    echo "Summary: $(grep '^Summary:' "$spec_file" | cut -d: -f2- | sed 's/^[[:space:]]*//' || echo 'N/A')"
    echo "Version: $(grep '^Version:' "$spec_file" | awk '{print $2}' || echo 'N/A')"
    echo "Release: $(grep '^Release:' "$spec_file" | awk '{print $2}' || echo 'N/A')"
    echo "License: $(grep '^License:' "$spec_file" | cut -d: -f2- | sed 's/^[[:space:]]*//' || echo 'N/A')"
    echo "BuildArch: $(grep '^BuildArch:' "$spec_file" | awk '{print $2}' || echo 'x86_64')"
    echo ""
    echo "Sources:"
    grep '^Source[0-9]*:' "$spec_file" | head -5
}

# Main build function
mql_build() {
    local spec_name=""
    local extra_args=()
    
    # Parse arguments (simple)
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                echo "Usage: mql build <spec> [--both] [--arch=<arch>]"
                echo "       mql build info <spec>"
                exit 0
                ;;
            *)
                if [[ -z "$spec_name" ]]; then
                    spec_name="$1"
                else
                    extra_args+=("$1")
                fi
                ;;
        esac
        shift
    done
    
    if [[ -z "$spec_name" ]]; then
        log_error "Missing spec name"
        exit 1
    fi
    
    # Ensure spec exists
    local spec_file="$MQL_PROJECT_ROOT/SPECS/${spec_name}.spec"
    if [[ ! -f "$spec_file" ]]; then
        log_error "Spec not found: $spec_name"
        exit 1
    fi
    
    log_step "Building $spec_name"
    
    # Run build-spec.sh with all arguments
    "$MQL_PROJECT_ROOT/scripts/build-spec.sh" "$spec_name" "${extra_args[@]}"
}