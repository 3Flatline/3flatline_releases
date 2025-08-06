#!/bin/bash
# Creates a venv environment in the scripts directory and installs dependencies.

set -euo pipefail

# Change to the directory where the script is located to ensure paths are correct.
cd "$(dirname "$0")"

VENV_DIR=".venv"

if ! command -v uv &> /dev/null; then
    echo "Error: uv command not found. Please install uv first."
    echo "See: https://github.com/astral-sh/uv"
    exit 1
fi

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at scripts/.venv"
else
    echo "Creating virtual environment at scripts/.venv..."
    uv venv "$VENV_DIR"
fi

echo "Installing dependencies..."
uv pip sync uv.lock

echo
echo "Setup complete."
echo "To activate the virtual environment, run the following command from the repository root:"
echo "source scripts/.venv/bin/activate"
