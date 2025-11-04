#!/bin/bash
# Installation script for dbinfer-relbench-adapter
# This script handles the special DGL dependency that requires a custom wheel

set -e  # Exit on error

echo "Installing dbinfer-relbench-adapter..."
echo ""

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Using uv for faster installation..."
    PIP_CMD="uv pip"
else
    echo "Using pip for installation..."
    PIP_CMD="pip"
fi

# Uninstall any existing DGL to avoid conflicts
echo "Removing any existing DGL installation..."
$PIP_CMD uninstall -y dgl 2>/dev/null || true

# Install dependencies from requirements.txt
echo "Installing dependencies..."
$PIP_CMD install -r requirements.txt

# Install the package in editable mode
echo "Installing dbinfer-relbench-adapter..."
$PIP_CMD install -e .

echo ""
echo "✓ Installation complete!"
echo ""
echo "You can now use the package:"
echo "  python -c 'from dbinfer_relbench_adapter import load_dbinfer_data; print(\"Success!\")'"
