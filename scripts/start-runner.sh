#!/run/current-system/sw/bin/bash
# scripts/start-runner.sh - Start GitHub Actions self-hosted runner
# Auto-restart on failure with health check

set -euo pipefail

# Ensure proper PATH for NixOS environment
export PATH="/run/current-system/sw/bin:/run/wrappers/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Required for .NET runner on NixOS (ICU not available)
export DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Runner directory (default: ~/actions-runner/)
RUNNER_DIR="${RUNNER_DIR:-$HOME/actions-runner}"
MAX_RETRIES=5
RETRY_DELAY=30

log_step() {
    echo "[runner] $(date '+%Y-%m-%d %H:%M:%S') $*"
}

# Health check: verify runner is registered and responding
health_check() {
    local retries=3
    local delay=5
    for i in $(seq 1 $retries); do
        if "$RUNNER_DIR/bin/Runner.Listener" true 2>/dev/null; then
            return 0
        fi
        log_step "Health check attempt $i/$retries failed, retrying in ${delay}s..."
        sleep "$delay"
    done
    return 1
}

# Start the runner using Runner.Listener directly (avoids run-helper.sh /bin/bash issue)
start_runner() {
    log_step "Starting GitHub Actions runner in $RUNNER_DIR"

    if [[ ! -d "$RUNNER_DIR" ]]; then
        log_step "ERROR: Runner directory not found: $RUNNER_DIR"
        log_step "Please configure the runner first: cd $RUNNER_DIR && ./config.sh"
        exit 1
    fi

    if [[ ! -x "$RUNNER_DIR/bin/Runner.Listener" ]]; then
        log_step "ERROR: Runner.Listener not found or not executable in $RUNNER_DIR/bin/"
        exit 1
    fi

    # Change to runner directory
    cd "$RUNNER_DIR"

    log_step "Starting runner process (via Runner.Listener)..."
    "$RUNNER_DIR/bin/Runner.Listener" run &

    local runner_pid=$!
    log_step "Runner started with PID $runner_pid"

    # Wait a moment for startup
    sleep 5

    # Check if still running
    if ! kill -0 "$runner_pid" 2>/dev/null; then
        log_step "ERROR: Runner process exited immediately"
        return 1
    fi

    # Run health check
    if health_check; then
        log_step "Runner is healthy and registered"
    else
        log_step "WARNING: Runner may not be fully registered yet"
    fi

    log_step "Waiting for runner process to exit..."
    wait "$runner_pid"
    local exit_code=$?
    log_step "Runner process exited with code $exit_code"
    return "$exit_code"
}

# Main loop with restart on failure
main() {
    local attempt=1

    log_step "GitHub Actions Runner Manager starting"
    log_step "Runner directory: $RUNNER_DIR"

    while true; do
        if start_runner; then
            log_step "Runner running normally"
        else
            log_step "Runner stopped unexpectedly"
        fi

        if [[ $attempt -ge $MAX_RETRIES ]]; then
            log_step "Max retries ($MAX_RETRIES) reached, exiting"
            exit 1
        fi

        log_step "Restarting in ${RETRY_DELAY}s... (attempt $((++attempt))/$MAX_RETRIES)"
        sleep "$RETRY_DELAY"
    done
}

main "$@"
