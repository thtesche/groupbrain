#!/bin/bash

# GroupBrain — Weekly Cron Runner
# Wraps main.py with venv activation for cron jobs.
#
# Usage:
#   ./run_weekly.sh                    # 7 days (default)
#   ./run_weekly.sh --days 14          # 14 days

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

PROJECT_ROOT="$SCRIPT_DIR"
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

# Pass --days to main.py
"$PYTHON_EXE" "$PROJECT_ROOT/main.py" --days "$DAYS"
