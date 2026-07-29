#!/bin/bash

# GroupBrain — Weekly Cron Runner
# Wraps main.py with venv activation for cron jobs.
#
# Usage:
#   ./run_weekly.sh                    # 7 days (default)
#   ./run_weekly.sh --days 14          # 14 days
#
# Environment variables (override defaults):
#   GROUPBRAIN_PROJECT_ROOT  — Absolute path to project directory (default: script location)
#   GROUPBRAIN_ENV_PATH      — Absolute path to .env file (default: $PROJECT_ROOT/.env)
#   GROUPBRAIN_DB_PATH       — Override DB_PATH for this run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Allow overriding project root via environment variable
PROJECT_ROOT="${GROUPBRAIN_PROJECT_ROOT:-$SCRIPT_DIR}"

# Parse --days argument
DAYS=7
if [ "$1" = "--days" ]; then
    if [ -n "$2" ] && [[ "$2" =~ ^[0-9]+$ ]]; then
        DAYS="$2"
    else
        echo "[ERROR] --days requires a positive integer argument"
        exit 1
    fi
fi

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

# Pass --days to main.py
"$PYTHON_EXE" "$PROJECT_ROOT/main.py" --days "$DAYS"
