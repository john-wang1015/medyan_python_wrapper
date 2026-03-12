"""
medyan._core
============
Low-level wrapper around the MEDYAN compiled executable.

All public functions subprocess-call the ``medyan`` binary that was compiled
and installed alongside this Python package.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence, Union


# ---------------------------------------------------------------------------
# Locate the compiled executable
# ---------------------------------------------------------------------------

def executable() -> Path:
    """Return the absolute path to the compiled ``medyan`` binary.

    The binary is installed at ``<package_root>/bin/medyan[.exe]``.

    Raises
    ------
    FileNotFoundError
        If the binary cannot be found (e.g. package was not properly installed).
    """
    # The executable is installed into <package>/bin/ by the CMake install rule.
    pkg_root = Path(__file__).parent
    exe_name = "medyan.exe" if sys.platform == "win32" else "medyan"

    candidate = pkg_root / "bin" / exe_name
    if candidate.is_file():
        return candidate

    # Fall back: check PATH (useful during development / editable installs).
    found = shutil.which("medyan")
    if found:
        return Path(found)

    raise FileNotFoundError(
        f"MEDYAN executable not found.\n"
        f"Expected location: {candidate}\n"
        "Make sure the package was installed with 'pip install .' from the "
        "medyan-python directory so that the C++ code was compiled."
    )


# ---------------------------------------------------------------------------
# Exception type
# ---------------------------------------------------------------------------

class MedyanError(RuntimeError):
    """Raised when the MEDYAN executable exits with a non-zero return code."""

    def __init__(self, returncode: int, cmd: Sequence[str], stderr: str = ""):
        self.returncode = returncode
        self.cmd = cmd
        self.stderr = stderr
        super().__init__(
            f"MEDYAN exited with code {returncode}.\n"
            f"Command: {' '.join(str(c) for c in cmd)}\n"
            + (f"stderr:\n{stderr}" if stderr.strip() else "")
        )


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _run_medyan(
    args: Sequence[Union[str, Path]],
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run the MEDYAN executable with *args* and return the CompletedProcess.

    Parameters
    ----------
    args:
        Command-line arguments passed *after* the executable name.
    capture_output:
        If ``True`` stdout/stderr are captured and available on the returned
        object; otherwise they are inherited from the parent process (printed
        to the terminal in real time).
    check:
        If ``True`` (default) a :class:`MedyanError` is raised on non-zero
        exit.
    """
    exe = executable()
    cmd = [str(exe)] + [str(a) for a in args]

    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
    )

    if check and result.returncode != 0:
        raise MedyanError(
            returncode=result.returncode,
            cmd=cmd,
            stderr=result.stderr if capture_output else "",
        )

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(
    system_file: Union[str, Path],
    input_dir: Optional[Union[str, Path]] = None,
    output_dir: Union[str, Path] = "./output",
    *,
    threads: int = 0,
    seed: Optional[int] = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    """Run a MEDYAN simulation.

    Parameters
    ----------
    system_file:
        Path to the system input file (``systeminput.txt``).  This is passed
        as the ``-s`` argument.  The ``input_dir`` is inferred from this
        file's parent directory if not supplied.
    input_dir:
        Path to the input directory (``-i``).  Defaults to the directory
        containing *system_file*.
    output_dir:
        Path to the output directory (``-o``).  Created if it does not exist.
        Defaults to ``./output``.
    threads:
        Number of threads to use (``-t``).  ``0`` means auto-detect (default).
    seed:
        If provided, the random number generator seed is fixed to this value
        (``--seed-fixed``), making the run reproducible.
    capture_output:
        If ``True``, stdout/stderr are captured and returned on the result
        object instead of being printed.

    Returns
    -------
    subprocess.CompletedProcess

    Raises
    ------
    MedyanError
        If MEDYAN exits with a non-zero return code.

    Examples
    --------
    >>> import medyan
    >>> medyan.run(
    ...     system_file="examples/actin_only/systeminput.txt",
    ...     output_dir="./my_output",
    ...     threads=4,
    ...     seed=42,
    ... )
    """
    system_file = Path(system_file).resolve()

    if input_dir is None:
        input_dir = system_file.parent
    input_dir = Path(input_dir).resolve()

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    args: list[Union[str, Path]] = [
        "-s", system_file,
        "-i", input_dir,
        "-o", output_dir,
        "-t", str(threads),
    ]

    if seed is not None:
        args += ["--seed-fixed", str(seed)]

    return _run_medyan(args, capture_output=capture_output)


def analyze(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    *,
    bond_frame: Optional[Union[int, str]] = None,
    frame_interval: Optional[int] = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    """Run MEDYAN's built-in analysis on an existing trajectory.

    Parameters
    ----------
    input_dir:
        Directory containing the ``snapshot.traj`` file.
    output_dir:
        Output directory for analysis results.
    bond_frame:
        Frame index (int) or ``"all"`` for membrane topology analysis.
    frame_interval:
        Process every N-th frame only.
    capture_output:
        Capture stdout/stderr instead of printing.

    Returns
    -------
    subprocess.CompletedProcess
    """
    args: list[Union[str, Path]] = [
        "-i", Path(input_dir).resolve(),
        "-o", Path(output_dir).resolve(),
        "analyze",
    ]

    if bond_frame is not None:
        args += ["--bond-frame", str(bond_frame)]
    if frame_interval is not None:
        args += ["--frame-interval", str(frame_interval)]

    return _run_medyan(args, capture_output=capture_output)


def test(capture_output: bool = False) -> subprocess.CompletedProcess:
    """Run the MEDYAN internal test suite.

    Parameters
    ----------
    capture_output:
        Capture stdout/stderr instead of printing.

    Returns
    -------
    subprocess.CompletedProcess
    """
    return _run_medyan(["test"], capture_output=capture_output)


def config(
    input_file: Optional[Union[str, Path]] = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess:
    """Launch MEDYAN's interactive configuration / normalization mode.

    Parameters
    ----------
    input_file:
        Optional existing configuration file to normalise.
    capture_output:
        Capture stdout/stderr instead of printing.

    Returns
    -------
    subprocess.CompletedProcess
    """
    args: list[Union[str, Path]] = ["config"]
    if input_file is not None:
        args += ["-s", Path(input_file).resolve()]

    return _run_medyan(args, capture_output=capture_output)


def version(capture_output: bool = True) -> str:
    """Return the MEDYAN version string printed by the executable.

    Returns
    -------
    str
        The first few lines of MEDYAN's header output.
    """
    exe = executable()
    result = subprocess.run(
        [str(exe), "--help"],
        capture_output=capture_output,
        text=True,
    )
    # MEDYAN prints a header even on --help; grab the first 3 lines.
    lines = (result.stdout or result.stderr or "").splitlines()
    return "\n".join(lines[:5])
