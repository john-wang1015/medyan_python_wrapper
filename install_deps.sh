#!/usr/bin/env bash
# install_deps.sh — install system prerequisite (HDF5) then pip install medyan
set -euo pipefail

echo "[medyan] Checking for HDF5..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! brew list hdf5 &>/dev/null; then
        echo "[medyan] Installing HDF5 via Homebrew..."
        brew install hdf5
    else
        echo "[medyan] HDF5 already installed."
    fi
elif command -v apt-get &>/dev/null; then
    echo "[medyan] Installing HDF5 via apt..."
    sudo apt-get install -y libhdf5-dev
elif command -v conda &>/dev/null; then
    echo "[medyan] Installing HDF5 via conda..."
    conda install -y -c conda-forge hdf5
else
    echo "[medyan] WARNING: cannot auto-install HDF5. Please install it manually."
    echo "  Ubuntu: sudo apt install libhdf5-dev"
    echo "  conda : conda install -c conda-forge hdf5"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "[medyan] Running pip install..."
pip install "${1:-.}" "${SCRIPT_DIR}"

echo ""
echo "✓ MEDYAN installed. Test: python -c \"import medyan; print(medyan.__version__)\""
