#!/usr/bin/env bash
# install_deps.sh
# ─────────────────────────────────────────────────────────────────────────────
# One-shot script that:
#   1. Clones & bootstraps vcpkg (if not already present)
#   2. Sets VCPKG_ROOT so scikit-build-core can find the toolchain
#   3. Runs `pip install .` (or `pip install -e .` for editable/dev install)
#
# Usage:
#   chmod +x install_deps.sh
#   ./install_deps.sh            # normal install
#   ./install_deps.sh --editable # editable install (development)
#   VCPKG_ROOT=/opt/vcpkg ./install_deps.sh   # use existing vcpkg
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VCPKG_DEFAULT_DIR="${SCRIPT_DIR}/.vcpkg"
EDITABLE=""

for arg in "$@"; do
    case "$arg" in
        --editable|-e) EDITABLE="-e" ;;
    esac
done

# ── 1. Ensure vcpkg is available ──────────────────────────────────────────────
if [[ -z "${VCPKG_ROOT:-}" ]]; then
    export VCPKG_ROOT="${VCPKG_DEFAULT_DIR}"
fi

if [[ ! -f "${VCPKG_ROOT}/vcpkg" && ! -f "${VCPKG_ROOT}/vcpkg.exe" ]]; then
    echo "[medyan-install] vcpkg not found at ${VCPKG_ROOT}. Cloning..."
    git clone https://github.com/microsoft/vcpkg.git "${VCPKG_ROOT}"
    # Pin to a known-good commit (same one MEDYAN's own bootstrap uses)
    (cd "${VCPKG_ROOT}" && git checkout c9e786d81a890ef6b3932779925f11e696dc9541)
    echo "[medyan-install] Bootstrapping vcpkg..."
    "${VCPKG_ROOT}/bootstrap-vcpkg.sh" -disableMetrics
else
    echo "[medyan-install] Using existing vcpkg at ${VCPKG_ROOT}"
fi

# ── 2. Export variables scikit-build-core needs ───────────────────────────────
export CMAKE_TOOLCHAIN_FILE="${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
export VCPKG_ROOT

echo "[medyan-install] VCPKG_ROOT=${VCPKG_ROOT}"
echo "[medyan-install] CMAKE_TOOLCHAIN_FILE=${CMAKE_TOOLCHAIN_FILE}"

# ── 3. Install the Python package ─────────────────────────────────────────────
echo "[medyan-install] Running pip install..."
pip install ${EDITABLE} "${SCRIPT_DIR}" \
    --no-build-isolation \
    -C cmake.define.CMAKE_TOOLCHAIN_FILE="${CMAKE_TOOLCHAIN_FILE}" \
    -C cmake.define.MEDYAN_NO_GUI=true \
    -v

echo ""
echo "✓  MEDYAN Python package installed successfully."
echo "   Test it with:  python -c \"import medyan; print(medyan.__version__)\""
