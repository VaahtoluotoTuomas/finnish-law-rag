"""Command-line interface: python -m lakirag <command>."""

import argparse
from pathlib import Path

from lakirag import __version__, fetch

RAW_DIR = Path("data/raw")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lakirag", description=__doc__)
    parser.add_argument("--version", action="version", version=f"lakirag {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("fetch", help="download the statutes from Finlex into data/raw/")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "fetch":
        for path in fetch.fetch_all(RAW_DIR):
            print(f"Saved {path}")
    else:
        parser.print_help()
    return 0
