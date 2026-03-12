"""
medyan — Python wrapper for the MEDYAN C++ simulation engine.

MEDYAN (Mechanochemical Dynamics of Active Networks) simulates growth dynamics
of actin-based filamentous networks in vitro and in vivo.

Basic usage
-----------
>>> import medyan
>>> result = medyan.run(
...     system_file="systeminput.txt",
...     input_dir="./input",
...     output_dir="./output",
... )

>>> # Analyse a completed trajectory
>>> medyan.analyze(input_dir="./input", output_dir="./output")

>>> # Get the path to the compiled executable
>>> print(medyan.executable())
"""

from medyan._core import (
    run,
    analyze,
    test,
    config,
    executable,
    MedyanError,
)

__version__ = "5.4.0"
__all__ = [
    "run",
    "analyze",
    "test",
    "config",
    "executable",
    "MedyanError",
    "__version__",
]
