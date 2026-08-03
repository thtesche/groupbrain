#!/bin/bash

# GroupBrain — Weekly Cron Runner
# Wraps main.py with venv activation for cron jobs.
#
# Usage:
#   ./run_weekly.sh                    # 7 days (default)
#   ./run_weekly.sh --days 14          # 14 days
#   ./run_weekly.sh --silent           # dry-run, no Telegram message
#   ./run_weekly.sh --silent --days 14 # dry-run with 14 days
#
# Environment variables (override defaults):
#   GROUPBRAIN_PROJECT_ROOT  — Absolute path to project directory (default: script location)
#   GROUPBRAIN_ENV_PATH      — Absolute path to .env file (default: $PROJECT_ROOT/.env)
#   GROUPBRAIN_DB_PATH       — Override DB_PATH for this run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Allow overriding project root via environment variable
PROJECT_ROOT="${GROUPBRAIN_PROJECT_ROOT:-$SCRIPT_DIR}"

# Parse arguments
DAYS=7
SILENT=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --days)
            if [ -n "$2" ] && [[ "$2" =~ ^[0-9]+$ ]]; then
                DAYS="$2"
                shift 2
            else
                echo "[ERROR] --days requires a positive integer argument"
                exit 1
            fi
            ;;
        --silent)
            SILENT=1
            shift
            ;;
        *)
            echo "[ERROR] Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Load .env if present
ENV_PATH="${GROUPBRAIN_ENV_PATH:-$PROJECT_ROOT/.env}"
if [ -f "$ENV_PATH" ]; then
    set -a
    source "$ENV_PATH"
    set +a
else
    echo "[!] Warning: .env file not found at $ENV_PATH"
fi

VENV_PATH="$PROJECT_ROOT/venv"

# Validate venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "[ERROR] Virtual environment not found at $VENV_PATH"
    exit 1
fi

PYTHON_EXE="$VENV_PATH/bin/python3"

# Clear PYTHONPATH then set to project root only
export PYTHONPATH=""
export PYTHONPATH="$PROJECT_ROOT"

# Allow overriding DB_PATH via environment variable
if [ -n "$GROUPBRAIN_DB_PATH" ]; then
    export DB_PATH="$GROUPBRAIN_DB_PATH"
fi

# Build command arguments
CMD=("$PYTHON_EXE" "$PROJECT_ROOT/main.py" --days "$DAYS")
if [ "$SILENT" -eq 1 ]; then
    CMD+=("--silent")
fi

"${CMD[@]}"
