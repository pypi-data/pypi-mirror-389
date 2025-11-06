"""Command line entry-point for Zephyr."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> None:
    """Dispatch Zephyr CLI commands."""
    parser = argparse.ArgumentParser(prog="zephyr", description="Zephyr orchestration CLI")
    parser.add_argument("--version", action="store_true", help="Show Zephyr package version and exit")

    args = parser.parse_args(argv)

    if args.version:
        from . import __version__

        print(f"Zephyr {__version__}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
