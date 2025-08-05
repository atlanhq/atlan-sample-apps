#!/bin/bash
set -e

# Use writable log location for non-root user in home directory
LOG_DIR="/home/appuser/logs"
LOG_FILE="$LOG_DIR/entrypoint.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Redirect output to log file
exec > >(tee -a "$LOG_FILE") 2>&1

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $@"
}

error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $@" >&2
    exit 1
}

log "Entrypoint execution started."

# Create necessary directories in user home directory
WORK_DIR="/home/appuser/runtime"
log "Creating necessary directories for logs and supervisor configurations..."
mkdir -p "$WORK_DIR/supervisor" "$WORK_DIR/dapr" "$WORK_DIR/application" || error "Failed to create necessary directories."

# Initialize Dapr in user space (non-root)
log "Initializing Dapr runtime ..."
if ! dapr init --slim --runtime-version=1.14.4; then
    error "Failed to initialize Dapr."
fi
log "Dapr initialized successfully in standalone mode.."

# Find the correct location of supervisord
log "Locating the supervisord binary..."
SUPERVISORD_PATH=$(which supervisord) || error "Failed to find supervisord binary."
if [[ -z "$SUPERVISORD_PATH" ]]; then
    error "Supervisord binary not found. Please ensure it is installed."
fi
log "Supervisord binary found at $SUPERVISORD_PATH."

log "Activating virtual environment..."
source .venv/bin/activate || error "Failed to activate virtual environment."

# Start Supervisor to manage all processes
log "Starting supervisord with configuration file /etc/supervisor/conf.d/supervisord.conf..."
exec "$SUPERVISORD_PATH" -c /etc/supervisor/conf.d/supervisord.conf || error "Failed to start supervisord."

# Final log entry
log "Entrypoint execution completed successfully."