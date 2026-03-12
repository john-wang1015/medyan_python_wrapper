# medyan — Python bindings for MEDYAN 5.4.0

[![MEDYAN](https://img.shields.io/badge/MEDYAN-5.4.0-blue)](http://medyan.org)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)

Python wrapper for **MEDYAN** (Mechanochemical Dynamics of Active Networks),
a simulation package for cytoskeletal filament network dynamics.

> The C++ backend is compiled during `pip install` — no separate build step
> is needed.

---

## Requirements

| Tool | Version |
|------|---------|
| Python | ≥ 3.9 |
| CMake | ≥ 3.15 |
| C++ compiler | GCC ≥ 7 / Clang ≥ 5 / MSVC 2017+ |
| git | ≥ 2.7 (for vcpkg bootstrap) |

---

## Installation

### Option A — Automatic (recommended)

The helper script clones vcpkg, installs all C++ dependencies, and runs
`pip install` in one step:

```bash
chmod +x install_deps.sh
./install_deps.sh
```

For an **editable / development** install:

```bash
./install_deps.sh --editable
```

### Option B — Manual (if you already have vcpkg)

```bash
export VCPKG_ROOT=/path/to/vcpkg
export CMAKE_TOOLCHAIN_FILE="${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"

pip install . \
    -C cmake.define.CMAKE_TOOLCHAIN_FILE="${CMAKE_TOOLCHAIN_FILE}" \
    -C cmake.define.MEDYAN_NO_GUI=true
```

### Option C — Install directly from GitHub

```bash
VCPKG_ROOT=~/.vcpkg pip install git+https://github.com/<your-org>/medyan-python.git \
    -C cmake.define.CMAKE_TOOLCHAIN_FILE="$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake" \
    -C cmake.define.MEDYAN_NO_GUI=true
```

---

## Quick Start

```python
import medyan

# Run a simulation from a MEDYAN system input file
result = medyan.run_simulation(
    input_file = "medyan_src/examples/actin_only/systeminput.txt",
    output_dir = "/tmp/medyan_out",
    runtime    = 100.0,   # override RUNTIME in the input file (optional)
    seed       = 42,      # reproducible run (optional)
)

print(f"Filaments : {result['num_filaments']}")
print(f"Cylinders : {result['num_cylinders']}")
print(f"Beads     : {result['num_beads']}")

# Bead coordinates for each filament
for i, fil in enumerate(result["filament_coords"]):
    print(f"Filament {i}: {len(fil)} beads, first bead = {fil[0]}")
```

---

## API Reference

### `medyan.run_simulation(...)`

```python
medyan.run_simulation(
    input_file:  str | Path,
    input_dir:   str | Path | None = None,
    output_dir:  str | Path | None = None,
    *,
    runtime:     float | None = None,
    seed:        int   | None = None,
    num_threads: int          = -1,
) -> dict
```

| Key | Type | Description |
|-----|------|-------------|
| `"num_filaments"` | `int` | Number of filaments at end of run |
| `"num_cylinders"` | `int` | Total cylinders |
| `"num_beads"` | `int` | Total beads |
| `"filament_coords"` | `list[list[tuple]]` | `[filament][bead] → (x, y, z)` in nm |

---

### `medyan.read_trajectory(snapshot_file)`

Pure-Python parser for MEDYAN's `snapshot.traj` output file.

```python
frames = medyan.read_trajectory("/tmp/medyan_out/snapshot.traj")
# frames[0]["time"]                → float (simulation time)
# frames[0]["filaments"][i]["beads"] → list of (x,y,z) tuples
```

---

### `medyan.get_examples_dir()`

Returns the path to the bundled example input files:

```python
import medyan
ex = medyan.get_examples_dir()
result = medyan.run_simulation(ex / "actin_only" / "systeminput.txt",
                               output_dir="/tmp/test")
```

---

## Example Input Files

The following examples from MEDYAN are included under `medyan_src/examples/`:

| Directory | Description |
|-----------|-------------|
| `actin_only/` | Pure actin polymerisation |
| `2filaments/` | Two-filament mechanical test |
| `50filaments_motor_linker/` | Motors + crosslinkers |
| `branch_actin/` | Branched actin with Arp2/3 |
| `nucleation_actin/` | Actin nucleation |

---

## Notes

* GUI features are **disabled** in this package (no OpenGL dependency).
* All length units are **nanometres (nm)**; time units are **seconds (s)**;
  force units are **picoNewtons (pN)**.
* The C++ compilation downloads and builds ~8 vcpkg packages
  (~500 MB, one-time only).

---

## License

MEDYAN is © 2015–2024 Papoian Lab, University of Maryland.
See `license.txt` for details.
