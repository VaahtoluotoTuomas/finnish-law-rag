"""Command-line interface: python -m lakirag <command>."""

import argparse

from lakirag import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lakirag", description=__doc__)
    parser.add_argument("--version", action="version", version=f"lakirag {__version__}")
    parser.add_subparsers(dest="command")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
    return 0
