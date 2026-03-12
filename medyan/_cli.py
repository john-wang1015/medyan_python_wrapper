"""
medyan._cli
===========
Entry point for the ``medyan`` command installed by pip.

This thin shim simply passes all arguments straight through to the compiled
MEDYAN binary, so every existing MEDYAN command-line workflow continues to
work without modification after ``pip install``.

Examples
--------
# Run a simulation (same as calling the binary directly)
$ medyan -s systeminput.txt -i ./input -o ./output

# Run the built-in tests
$ medyan test

# Analyse a trajectory
$ medyan -i ./input -o ./output analyze
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    """Replace the current process with the MEDYAN executable.

    All sys.argv arguments (excluding the script name itself) are forwarded
    verbatim to the binary.  We use os.execv so that signals, stdin/stdout,
    and the process exit code are all handled transparently.
    """
    from medyan._core import executable

    try:
        exe = executable()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    # os.execv replaces the current process — no subprocess overhead.
    # argv[0] is the executable path; the rest are forwarded arguments.
    try:
        os.execv(str(exe), [str(exe)] + sys.argv[1:])
    except OSError as exc:
        # execv only returns on failure.
        print(f"Failed to launch MEDYAN: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
