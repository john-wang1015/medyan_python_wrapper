# MEDYAN Python Package

Python wrapper for **MEDYAN** (Mechanochemical Dynamics of Active Networks) v5.4.0.

`pip install .` automatically compiles the C++ simulation engine. You do **not**
need to run cmake or make yourself.

---

## Requirements

- Linux or macOS (Windows support is experimental)
- conda / mamba environment (recommended)
- C++17-capable compiler: **GCC ≥ 9** or **Clang ≥ 10**
- CMake ≥ 3.15
- Python ≥ 3.8

---

## Step 1 — Create a conda environment and install C++ dependencies

All required C++ libraries are available on **conda-forge**.

```bash
# Create and activate the environment
conda create -n medyan python=3.11
conda activate medyan

# C++ build tools
conda install -c conda-forge cmake ninja cxx-compiler

# Required C++ libraries
conda install -c conda-forge \
    boost-cpp \
    eigen \
    fmt \
    spdlog \
    hdf5 \
    highfive \
    spectra \
    xtensor \
    xtensor-blas \
    catch2
```

> **Note for Linux users:** if `cxx-compiler` does not pull in a recent enough
> GCC, install it explicitly: `conda install -c conda-forge gcc gxx`

---

## Step 2 — Install the Python package

```bash
# Activate the conda environment first
conda activate medyan

# Install (compiles C++ automatically)
cd /path/to/medyan-python
pip install .
```

`pip` invokes `scikit-build-core`, which runs CMake and the compiler for you.
The compiled `medyan` binary ends up inside the Python package at
`<site-packages>/medyan/bin/medyan`.

For development / editable installs use:
```bash
pip install --no-build-isolation -e .
```

---

## Usage

### Python API

```python
import medyan

# ── Run a simulation ──────────────────────────────────────────────
medyan.run(
    system_file="examples/actin_only/systeminput.txt",
    output_dir="./output",
)

# Fix the RNG seed for reproducibility
medyan.run(
    system_file="systeminput.txt",
    input_dir="./input",
    output_dir="./output",
    threads=8,
    seed=42,
)

# ── Analyse an existing trajectory ───────────────────────────────
medyan.analyze(
    input_dir="./input",
    output_dir="./output",
)

# ── Run the built-in test suite ───────────────────────────────────
medyan.test()

# ── Find the compiled binary ──────────────────────────────────────
print(medyan.executable())
```

### Command-line (same as the native binary)

After installation a `medyan` command is added to your PATH.
All native MEDYAN arguments work unchanged:

```bash
# Run a simulation
medyan -s systeminput.txt -i ./input -o ./output

# Use multiple threads with a fixed seed
medyan -s systeminput.txt -i ./input -o ./output -t 8 --seed-fixed 42

# Analyse a trajectory
medyan -i ./input -o ./output analyze

# Run internal tests
medyan test

# Print help
medyan --help
```

---

## Python API reference

| Function | Description |
|---|---|
| `medyan.run(system_file, input_dir, output_dir, *, threads, seed)` | Run a simulation |
| `medyan.analyze(input_dir, output_dir, *, bond_frame, frame_interval)` | Analyse a trajectory |
| `medyan.test()` | Run MEDYAN's internal tests |
| `medyan.config(input_file)` | Interactive configuration / normalisation |
| `medyan.executable()` | Return `Path` to the compiled binary |
| `medyan.version()` | Return MEDYAN version header string |

All functions accept `capture_output=True` to capture stdout/stderr as strings
instead of printing them.

---

## Troubleshooting

### `cmake` cannot find a library

Make sure the conda environment is activated **before** running `pip install .`
so that CMake picks up the conda-installed headers and libraries.

If cmake still can't find a package, set the CMake prefix path explicitly:

```bash
pip install . --config-settings="cmake.args=-DCMAKE_PREFIX_PATH=$CONDA_PREFIX"
```

### `stdc++fs` linker error (GCC < 9)

Upgrade GCC: `conda install -c conda-forge gcc=12 gxx=12`

### `HighFive` not found

```bash
conda install -c conda-forge highfive
```

### Compilation takes a long time

Pass `-j` to use parallel compilation:

```bash
pip install . --config-settings="cmake.args=-j8"
```

---

## License

See `license.txt`. MEDYAN is developed by the Papoian Laboratory, University
of Maryland. http://www.medyan.org
