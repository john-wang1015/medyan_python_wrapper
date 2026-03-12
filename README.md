 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index d8742e0429b570157c8b5210a3cd40ff4d141d6d..55eba35810c9a909b2a244a43066de469cb0f5b8 100644
--- a/README.md
+++ b/README.md
@@ -13,67 +13,96 @@ downloaded and compiled on first install.
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
 
+### macOS (Apple Silicon) note
+
+If you hit a `boost-thread:arm64-osx` build failure during `pip install`, remove the previous build cache and retry so a fresh (current) vcpkg checkout is used:
+
+```bash
+rm -rf build/ _skbuild/
+pip install --no-cache-dir .
+```
+
+You can also point to your own up-to-date vcpkg checkout via `VCPKG_ROOT`.
+
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
 
+---
+### Conda environment (recommended setup)
+
+When building inside a conda env, install build tools first and force a clean build:
+
+```bash
+conda install -c conda-forge cmake ninja compilers pkg-config
+rm -rf build/ _skbuild/
+pip install --no-cache-dir .
+```
+
+If you already have a working vcpkg checkout, reuse it:
+
+```bash
+export VCPKG_ROOT=/path/to/vcpkg
+pip install --no-cache-dir .
+```
+
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
 
 
EOF
)