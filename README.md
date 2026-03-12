# medyan — Python bindings for MEDYAN 5.4.0

[![MEDYAN](https://img.shields.io/badge/MEDYAN-5.4.0-blue)](http://medyan.org)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)

Python wrapper for **MEDYAN** (Mechanochemical Dynamics of Active Networks),
a simulation package for cytoskeletal filament network dynamics.

The C++ backend is compiled automatically during `pip install` — **no
separate build step is needed**.  vcpkg and all C++ dependencies are
downloaded and compiled on first install.

---

## Requirements

| Tool | Minimum version |
|------|----------------|
| Python | 3.9 |
| CMake  | 3.15 |
| C++ compiler | GCC ≥ 7 / Clang ≥ 5 / MSVC 2017+ |
| git | 2.7 (used to bootstrap vcpkg) |

---

## Installation

### From GitHub (recommended)

```bash
pip install git+https://github.com/john-wang1015/medyan_python_wrapper.git
```

That's it. CMake will automatically clone and bootstrap vcpkg, then
compile all C++ dependencies.  First install takes ~10–20 minutes
depending on your machine; subsequent installs reuse the cached build.

### Faster installs with a pre-existing vcpkg

If you already have vcpkg, point to it and the first-install step is skipped:

```bash
export VCPKG_ROOT=/path/to/vcpkg
pip install git+https://github.com/john-wang1015/medyan_python_wrapper.git
```

### Local (clone + install)

```bash
git clone https://github.com/john-wang1015/medyan_python_wrapper.git
cd medyan-python
pip install .
```

---

## Quick Start

```python
import medyan

result = medyan.run_simulation(
    input_file = medyan.get_examples_dir() / "actin_only/systeminput.txt",
    output_dir = "/tmp/medyan_out",
    runtime    = 100.0,   # override RUNTIME (optional)
    seed       = 42,      # reproducible run (optional)
)

print(f"Filaments : {result['num_filaments']}")
print(f"Cylinders : {result['num_cylinders']}")
print(f"Beads     : {result['num_beads']}")

# (x, y, z) of every bead in filament 0
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
    runtime:     float | None = None,       # overrides RUNTIME in file
    seed:        int   | None = None,
    num_threads: int          = -1,
) -> dict
```

Return dict keys:

| Key | Type | Description |
|-----|------|-------------|
| `"num_filaments"` | `int` | Filaments at end of simulation |
| `"num_cylinders"` | `int` | Total cylinders |
| `"num_beads"` | `int` | Total beads |
| `"filament_coords"` | `list[list[tuple]]` | `[filament][bead] → (x, y, z)` nm |

### `medyan.read_trajectory(snapshot_file)`

Pure-Python parser for MEDYAN's `snapshot.traj` output:

```python
frames = medyan.read_trajectory("/tmp/medyan_out/snapshot.traj")
print(frames[0]["time"])                          # float
print(frames[0]["filaments"][0]["beads"][0])      # (x, y, z)
```

### `medyan.get_examples_dir()`

Returns a `Path` to the bundled example input files.

---

## Example Input Files

Included under `medyan_src/examples/`:

| Directory | Description |
|-----------|-------------|
| `actin_only/` | Pure actin polymerisation |
| `2filaments/` | Two-filament mechanical test |
| `50filaments_motor_linker/` | Motors + crosslinkers |
| `branch_actin/` | Branched actin (Arp2/3) |
| `nucleation_actin/` | Actin nucleation |

---

## Notes

- GUI is **disabled** in this package (no OpenGL required).
- Units: length = **nm**, time = **s**, force = **pN**.
- First install compiles ~8 vcpkg packages (~500 MB, cached after that).

---

## License

MEDYAN © 2015–2024 Papoian Lab, University of Maryland.  See `license.txt`.
