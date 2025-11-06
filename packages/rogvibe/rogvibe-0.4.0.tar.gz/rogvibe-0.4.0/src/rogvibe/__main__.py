"""Command-line interface for rogvibe."""

from __future__ import annotations

import sys
from typing import Sequence

from .app import run, run_slot_machine


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint invoked via `python -m rogvibe` or project scripts."""
    args = list(argv) if argv is not None else sys.argv[1:]

    # Check if --slot mode is requested
    if args and args[0] == "--slot":
        run_slot_machine()
    else:
        run(args or None)


if __name__ == "__main__":
    main()
