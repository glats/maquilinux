#!/usr/bin/env bash
# check-build-status.sh - Check status of async build
#
# Usage: ./scripts/check-build-status.sh [spec-name]
# Or: ./scripts/check-build-status.sh --session [session-name]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$WORKSPACE/logs"

SPEC_NAME="${1:-}"

if [[ -z "$SPEC_NAME" ]]; then
    # List all active builds
    echo "Active tmux sessions:"
    tmux list-sessions 2>/dev/null | grep "build-" || echo "  No active build sessions"
    echo ""
    echo "Recent log files:"
    ls -lt "$LOG_DIR"/*.log 2>/dev/null | head -10 || echo "  No log files found"
    exit 0
fi

# Check if it's a session name
if [[ "$SPEC_NAME" == --session ]]; then
    SESSION_NAME="${2:-}"
    if [[ -z "$SESSION_NAME" ]]; then
        echo "Usage: $0 --session [session-name]"
        exit 1
    fi
else
    # Find most recent session for this spec
    SESSION_NAME=$(tmux list-sessions 2>/dev/null | grep "build-$SPEC_NAME" | tail -1 | cut -d: -f1)
    if [[ -z "$SESSION_NAME" ]]; then
        echo "No active build session found for: $SPEC_NAME"
        echo "Recent completed builds:"
        ls -1t "$LOG_DIR"/*${SPEC_NAME}*.log 2>/dev/null | head -5 || echo "  No logs found"
        exit 1
    fi
fi

echo "==============================================="
echo "Build Status: $SESSION_NAME"
echo "Timestamp: $(date -Iseconds)"
echo "==============================================="
echo ""

# Check tmux session
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Session Status: 🟢 RUNNING"
    echo ""
    echo "To attach and watch:"
    echo "  tmux attach-session -t $SESSION_NAME"
else
    echo "Session Status: ⚪ COMPLETED or FAILED"
    echo ""
fi

# Find log file
LOG_FILE=$(ls -1t "$LOG_DIR"/*${SPEC_NAME}*.log 2>/dev/null | head -1)
if [[ -n "$LOG_FILE" && -f "$LOG_FILE" ]]; then
    echo "Log File: $LOG_FILE"
    echo "Log Size: $(du -h "$LOG_FILE" | cut -f1)"
    echo ""
    
    # Check for completion markers
    if grep -q "Build completed with exit code:" "$LOG_FILE" 2>/dev/null; then
        EXIT_CODE=$(grep "Build completed with exit code:" "$LOG_FILE" | tail -1 | grep -oE '[0-9]+' | tail -1)
        if [[ "$EXIT_CODE" == "0" ]]; then
            echo "Build Result: ✅ SUCCESS (exit code 0)"
        else
            echo "Build Result: ❌ FAILED (exit code $EXIT_CODE)"
        fi
        echo ""
        echo "Last 20 lines of log:"
        echo "---"
        tail -20 "$LOG_FILE"
        echo "---"
        echo ""
        echo "Full log available at: $LOG_FILE"
        
        if [[ "$EXIT_CODE" != "0" ]]; then
            echo ""
            echo "❌ ERROR ANALYSIS - Last 100 lines (for debugging):"
            echo "---"
            tail -100 "$LOG_FILE"
            echo "---"
        fi
    else
        echo "Build Result: 🟡 IN PROGRESS"
        echo ""
        echo "Last 50 lines of log:"
        echo "---"
        tail -50 "$LOG_FILE"
        echo "---"
        echo ""
        echo "Log growing... Check again later."
    fi
    
    # Check for RPMs created
    if [[ -d "$WORKSPACE/RPMS/x86_64" ]]; then
        RPMS=$(ls -1t "$WORKSPACE/RPMS/x86_64"/*${SPEC_NAME}*.rpm 2>/dev/null | head -5 || true)
        if [[ -n "$RPMS" ]]; then
            echo ""
            echo "RPMs found:"
            echo "$RPMS" | while read rpm; do
                echo "  - $(basename "$rpm") ($(du -h "$rpm" | cut -f1))"
            done
        fi
    fi
else
    echo "Log File: Not found"
fi

echo ""
echo "==============================================="