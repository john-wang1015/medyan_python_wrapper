# medyan — Python bindings for MEDYAN 5.4.0

[![MEDYAN](https://img.shields.io/badge/MEDYAN-5.4.0-blue)](http://medyan.org)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)

Python wrapper for **MEDYAN** (Mechanochemical Dynamics of Active Networks),
a simulation package for cytoskeletal filament network dynamics.

The C++ backend is compiled automatically during `pip install`.
All dependencies except HDF5 are downloaded automatically by CMake.

---

## Prerequisites

Only **HDF5** needs to be installed on your system before `pip install`:

| Platform | Command |
|----------|---------|
| macOS    | `brew install hdf5` |
| Ubuntu/Debian | `sudo apt install libhdf5-dev` |
| conda (any) | `conda install -c conda-forge hdf5` |
| HPC / module | `module load hdf5` |

You also need: **Python ≥ 3.9**, **CMake ≥ 3.15**, and a **C++17 compiler**
(GCC ≥ 7, Clang ≥ 5, or MSVC 2017+).

All other C++ dependencies (Boost headers, Eigen3, fmt, spdlog, Spectra,
xtensor, HighFive, pybind11) are fetched automatically during the build.

---

## Installation

```bash
# 1. Install HDF5 (once)
brew install hdf5          # macOS
# sudo apt install libhdf5-dev   # Ubuntu

# 2. Install the Python package
pip install git+https://github.com/john-wang1015/medyan_python_wrapper.git
```

First install takes ~5–10 minutes (downloads and compiles deps).
Subsequent installs reuse scikit-build-core's cache.

### Local install

```bash
git clone https://github.com/john-wang1015/medyan_python_wrapper.git
cd medyan_python_wrapper
pip install .
```

---

## Quick Start

```python
import medyan

result = medyan.run_simulation(
    input_file = medyan.get_examples_dir() / "actin_only/systeminput.txt",
    output_dir = "/tmp/medyan_out",
    runtime    = 100.0,   # override RUNTIME in input file (optional)
    seed       = 42,      # reproducible run (optional)
)

print(f"Filaments : {result['num_filaments']}")
print(f"Cylinders : {result['num_cylinders']}")
print(f"Beads     : {result['num_beads']}")

# (x, y, z) coordinates of every bead in filament 0
for bead in result["filament_coords"][0]:
    print(bead)
```

---

## API

### `medyan.run_simulation(...)`

```python
medyan.run_simulation(
    input_file:  str | Path,
    input_dir:   str | Path | None = None,  # default: dir of input_file
    output_dir:  str | Path | None = None,  # default: cwd
    *,
    runtime:     float | None = None,       # overrides RUNTIME in input file
    seed:        int   | None = None,
    num_threads: int          = -1,
) -> dict
```

| Return key | Type | Description |
|------------|------|-------------|
| `"num_filaments"` | `int` | Filaments at end of simulation |
| `"num_cylinders"` | `int` | Total cylinders |
| `"num_beads"` | `int` | Total beads |
| `"filament_coords"` | `list[list[tuple]]` | `[filament][bead] → (x, y, z)` in nm |

### `medyan.read_trajectory(snapshot_file)`

Pure-Python parser for MEDYAN's `snapshot.traj` output:

```python
frames = medyan.read_trajectory("/tmp/medyan_out/snapshot.traj")
print(frames[0]["time"])                       # simulation time (float)
print(frames[0]["filaments"][0]["beads"][0])   # (x, y, z)
```

### `medyan.get_examples_dir()`

Returns a `Path` to the bundled example input files.

---

## Example Input Files

| Directory | Description |
|-----------|-------------|
| `actin_only/` | Pure actin polymerisation |
| `2filaments/` | Two-filament mechanical test |
| `50filaments_motor_linker/` | Motors + crosslinkers |
| `branch_actin/` | Branched actin (Arp2/3) |
| `nucleation_actin/` | Actin nucleation |

---

## Notes

- GUI is **disabled** — no OpenGL/GLFW required.
- Units: length = **nm**, time = **s**, force = **pN**.
- No vcpkg required — deps are fetched by CMake directly from GitHub.

---

## License

MEDYAN © 2015–2024 Papoian Lab, University of Maryland. See `license.txt`.
