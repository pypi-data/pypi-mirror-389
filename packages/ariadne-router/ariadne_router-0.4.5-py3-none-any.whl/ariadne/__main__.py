from __future__ import annotations

import sys


def main() -> int:
    """Package entry point that defers to the unified CLI.

    This enables usage like:
      python -m ariadne install --accelerate
      python -m ariadne benchmark --circuit path/to.qasm
    """
    try:
        # Import here to avoid importing the full CLI on module import
        from .cli.main import main as cli_main
    except Exception:
        # Very small fallback to avoid masking import-time errors
        # if the CLI cannot be imported for some reason.
        print("Ariadne CLI is unavailable. Please install optional dependencies or run `ariadne --help`.")
        return 1

    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
