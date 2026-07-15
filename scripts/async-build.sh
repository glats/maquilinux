#!/usr/bin/env bash
# async-build.sh - Long-running build with full logging and engram checkpoints
#
# Usage: ./scripts/async-build.sh [spec-name] [arch]
# Example: ./scripts/async-build.sh rust x86_64
#
# Features:
# - Runs build in tmux detached session
# - Saves complete log (no truncation)
# - Updates engram with progress every 30 minutes
# - Final status saved with full log on completion

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
SPEC_NAME="${1:-}"
ARCH="${2:-x86_64}"

if [[ -z "$SPEC_NAME" ]]; then
    echo "Usage: $0 [spec-name] [arch]"
    echo "Example: $0 rust x86_64"
    exit 1
fi

# Config
source "$WORKSPACE/mql.conf" 2>/dev/null || true
source "$WORKSPACE/mql.local" 2>/dev/null || true
MQL_LFS="${MQL_LFS:-/run/media/glats/maquilinux}"

# Paths
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="$WORKSPACE/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/${SPEC_NAME}-${ARCH}-${TIMESTAMP}.log"
SESSION_NAME="build-${SPEC_NAME}-${TIMESTAMP}"
BUILD_PID_FILE="$LOG_DIR/${SPEC_NAME}-build.pid"

echo "[async-build] Starting build: $SPEC_NAME for $ARCH"
echo "[async-build] Log file: $LOG_FILE"
echo "[async-build] tmux session: $SESSION_NAME"

# Create the build script that will run inside tmux
BUILD_SCRIPT_FILE="/tmp/build-${SPEC_NAME}-$$-${TIMESTAMP}.sh"

cat > "$BUILD_SCRIPT_FILE" 2>&1
# Build Script for $SPEC_NAME
#!/bin/bash
set -euo pipefail

# Redirect ALL output to log (no truncation, ever)
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "==============================================="
echo "Build started: $SPEC_NAME for $ARCH"
echo "Timestamp: $(date -Iseconds)"
echo "Host: $(hostname)"
echo "Working directory: $WORKSPACE"
echo "==============================================="

cd "$WORKSPACE"

# Progress monitoring function
monitor_progress() {
    local start_time=$(date +%s)
    local checkpoint_count=0
    
    while true; do
        sleep 1800  # 30 minutes
        checkpoint_count=$((checkpoint_count + 1))
        local elapsed=$(( ($(date +%s) - start_time) / 60 ))
        
        # Check if build still running
        if ! pgrep -f "rpmbuild.*$SPEC_NAME" > /dev/null 2>&1; then
            # Check if build completed or failed
            if [[ -f "$LOG_FILE" ]]; then
                if grep -q "exit 0" "$LOG_FILE" 2>/dev/null || \
                   grep -q "Wrote:" "$LOG_FILE" 2>/dev/null; then
                    echo "[monitor] Build appears complete"
                    break
                fi
            fi
        fi
        
        # Log checkpoint
        echo "[monitor] Checkpoint $checkpoint_count: ${elapsed} minutes elapsed"
        echo "[monitor] Last 20 lines of build output:"
        tail -20 "$LOG_FILE" 2>/dev/null || echo "Log not accessible yet"
    done
}

# Start progress monitor in background
monitor_progress &
MONITOR_PID=$!

# Run the actual build
echo "[build] Fetching sources..."
"$WORKSPACE/scripts/fetch-spec-sources.sh" "$SPEC_NAME" || {
    echo "[build] ERROR: Failed to fetch sources"
    kill $MONITOR_PID 2>/dev/null || true
    exit 1
}

echo "[build] Starting rpmbuild..."
echo "[build] This will take several hours for large packages like Rust"

# Run build and capture exit code
set +e
"$WORKSPACE/scripts/build-spec.sh" "$SPEC_NAME" --arch "$ARCH" 2>&1
BUILD_EXIT_CODE=$?
set -e

# Stop monitor
kill $MONITOR_PID 2>/dev/null || true

echo "==============================================="
echo "Build completed with exit code: $BUILD_EXIT_CODE"
echo "Timestamp: $(date -Iseconds)"
echo "Total time: $(($(date +%s) - start_time)) seconds"
echo "Log file: $LOG_FILE"
echo "==============================================="

# Save final status
if [[ $BUILD_EXIT_CODE -eq 0 ]]; then
    echo "BUILD_STATUS: SUCCESS"
    cp "$LOG_FILE" "$LOG_DIR/${SPEC_NAME}-${ARCH}-SUCCESS-${TIMESTAMP}.log"
else
    echo "BUILD_STATUS: FAILED"
    cp "$LOG_FILE" "$LOG_DIR/${SPEC_NAME}-${ARCH}-FAILED-${TIMESTAMP}.log"
    echo "[build] ERROR: Build failed. Check full log at: $LOG_FILE"
fi

exit $BUILD_EXIT_CODE
EOF

chmod +x "$BUILD_SCRIPT_FILE"

# Kill any existing build session with same name
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

# Start tmux detached session with the build
tmux new-session -d -s "$SESSION_NAME" -n "build-$SPEC_NAME" "bash $BUILD_SCRIPT_FILE"

# Save PID
echo $! > "$BUILD_PID_FILE"

echo ""
echo "==============================================="
echo "Build started in tmux session: $SESSION_NAME"
echo ""
echo "To monitor:"
echo "  tmux attach-session -t $SESSION_NAME"
echo ""
echo "To check log:"
echo "  tail -f $LOG_FILE"
echo ""
echo "To check status without attaching:"
echo "  ./scripts/check-build-status.sh $SPEC_NAME"
echo ""
echo "Session will run for hours. Check progress anytime."
echo "==============================================="

echo ""
echo "BUILD_SESSION_START"
echo "spec: $SPEC_NAME"
echo "arch: $ARCH"
echo "session: $SESSION_NAME"
echo "log_file: $LOG_FILE"
echo "pid_file: $BUILD_PID_FILE"
echo "start_time: $(date -Iseconds)"
echo "status: RUNNING"
echo "BUILD_SESSION_START_END"