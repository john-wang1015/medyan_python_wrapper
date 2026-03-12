"""
medyan
======
Python interface to MEDYAN (Mechanochemical Dynamics of Active Networks).

Quickstart
----------
>>> import medyan
>>> result = medyan.run_simulation(
...     input_file = "examples/actin_only/systeminput.txt",
...     output_dir = "/tmp/medyan_out",
... )
>>> print(f"Simulation finished with {result['num_filaments']} filaments.")

For full parameter control, use :func:`run_simulation`.
To inspect trajectory files written to disk, use :func:`read_trajectory`.
"""

from __future__ import annotations

import os
import pathlib
from typing import Optional, Union

# The compiled C++ extension
from medyan import _core

__version__: str = _core.__version__
__all__ = [
    "run_simulation",
    "read_trajectory",
    "get_examples_dir",
    "__version__",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_simulation(
    input_file: Union[str, os.PathLike],
    input_dir:  Optional[Union[str, os.PathLike]] = None,
    output_dir: Optional[Union[str, os.PathLike]] = None,
    *,
    runtime:     Optional[float] = None,
    seed:        Optional[int]   = None,
    num_threads: int = -1,
) -> dict:
    """
    Run a MEDYAN simulation from a system input file.

    Parameters
    ----------
    input_file : str or Path
        Path to the system input file (e.g. ``systeminput.txt``).
        The chemistry file referenced inside it must exist in the same
        directory (or in *input_dir* if given).
    input_dir : str or Path, optional
        Directory that contains the chemistry input file and any other
        auxiliary input files.  Defaults to the parent directory of
        *input_file*.
    output_dir : str or Path, optional
        Directory where MEDYAN writes snapshot and log files.
        Will be created if it does not exist.
        Defaults to the current working directory.
    runtime : float, optional
        Simulation run time in seconds (MEDYAN units).  If given, overrides
        the ``RUNTIME`` field in the system input file.
    seed : int, optional
        Fix the random-number-generator seed for reproducibility.
    num_threads : int, optional
        Number of worker threads.  ``-1`` (default) lets MEDYAN choose.

    Returns
    -------
    dict
        ``"num_filaments"``   – number of filaments at end of simulation

        ``"num_cylinders"``   – total number of cylinders

        ``"num_beads"``       – total number of beads

        ``"filament_coords"`` – ``list[list[tuple[float, float, float]]]``
        where ``filament_coords[i][j] = (x, y, z)`` is the position of
        bead *j* in filament *i*, in nanometres.

    Examples
    --------
    >>> import medyan
    >>> result = medyan.run_simulation(
    ...     input_file  = "examples/actin_only/systeminput.txt",
    ...     output_dir  = "/tmp/my_run",
    ...     runtime     = 100.0,
    ...     seed        = 42,
    ... )
    >>> coords = result["filament_coords"]
    >>> print(f"{result['num_filaments']} filaments, "
    ...       f"{result['num_beads']} beads total")
    """
    input_file = pathlib.Path(input_file).resolve()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    _input_dir = str(input_dir) if input_dir is not None else ""
    _output_dir = str(output_dir) if output_dir is not None else ""

    return _core.run_simulation(
        input_file  = str(input_file),
        input_dir   = _input_dir,
        output_dir  = _output_dir,
        runtime     = runtime,
        seed        = seed,
        num_threads = num_threads,
    )


def read_trajectory(snapshot_file: Union[str, os.PathLike]) -> list:
    """
    Parse a MEDYAN ``snapshot.traj`` file into a list of frames.

    Each frame is a dict with keys:

    * ``"time"``          – simulation time of this snapshot (float)
    * ``"filaments"``     – list of filament dicts, each with:
        * ``"id"``        – filament id
        * ``"beads"``     – list of ``(x, y, z)`` tuples

    Parameters
    ----------
    snapshot_file : str or Path
        Path to the ``snapshot.traj`` file produced by MEDYAN.

    Returns
    -------
    list[dict]
        List of frame dicts (see above).

    Notes
    -----
    This is a pure-Python parser for MEDYAN's plain-text trajectory format.
    It does *not* require the C++ extension.
    """
    frames: list = []
    snapshot_file = pathlib.Path(snapshot_file)
    if not snapshot_file.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")

    current_frame: Optional[dict] = None
    current_filament: Optional[dict] = None

    with open(snapshot_file) as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # Frame header: "SNAPSHOT <time>"
            if line.startswith("SNAPSHOT"):
                if current_frame is not None:
                    if current_filament is not None:
                        current_frame["filaments"].append(current_filament)
                        current_filament = None
                    frames.append(current_frame)
                parts = line.split()
                t = float(parts[1]) if len(parts) > 1 else 0.0
                current_frame = {"time": t, "filaments": []}
                continue

            # Filament header: "FILAMENT <id> ..."
            if line.startswith("FILAMENT"):
                if current_filament is not None and current_frame is not None:
                    current_frame["filaments"].append(current_filament)
                parts = line.split()
                fid = int(parts[1]) if len(parts) > 1 else -1
                current_filament = {"id": fid, "beads": []}
                continue

            # Bead coordinate line: "BEAD <x> <y> <z>" or just "<x> <y> <z>"
            if current_filament is not None:
                parts = line.split()
                # skip non-numeric lines
                try:
                    if parts[0].upper() == "BEAD":
                        parts = parts[1:]
                    if len(parts) >= 3:
                        xyz = (float(parts[0]), float(parts[1]), float(parts[2]))
                        current_filament["beads"].append(xyz)
                except (ValueError, IndexError):
                    pass

    # flush last frame
    if current_frame is not None:
        if current_filament is not None:
            current_frame["filaments"].append(current_filament)
        frames.append(current_frame)

    return frames


def get_examples_dir() -> pathlib.Path:
    """
    Return the path to the bundled MEDYAN example input files.

    Examples
    --------
    >>> import medyan
    >>> ex = medyan.get_examples_dir()
    >>> result = medyan.run_simulation(ex / "actin_only" / "systeminput.txt",
    ...                                output_dir="/tmp/test")
    """
    return pathlib.Path(__file__).parent.parent / "medyan_src" / "examples"
