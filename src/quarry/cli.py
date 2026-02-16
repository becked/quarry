"""CLI argument parsing for quarry."""

import argparse
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="quarry",
        description="Extract Old World game data to structured JSON.",
    )
    parser.add_argument(
        "--game-path",
        type=Path,
        required=True,
        help="Path to Old World installation directory",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en-US",
        help="Language code for localization (default: en-US)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./output"),
        help="Directory to write JSON output files (default: ./output)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Game version string to embed in output metadata",
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="*",
        default=None,
        help="Specific categories to extract (default: all)",
    )
    return parser.parse_args(argv)
