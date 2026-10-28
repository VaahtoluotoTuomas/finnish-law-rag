"""Command-line interface: python -m lakirag <command>."""

import argparse
from pathlib import Path

from lakirag import __version__, fetch, parse, retrieve

RAW_DIR = Path("data/raw")
PASSAGES_PATH = Path("data/passages.jsonl")
EMBEDDINGS_PATH = Path("data/embeddings.npz")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lakirag", description=__doc__)
    parser.add_argument("--version", action="version", version=f"lakirag {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("fetch", help="download the statutes from Finlex into data/raw/")
    subparsers.add_parser("build", help="parse data/raw/ into data/passages.jsonl")
    search = subparsers.add_parser("search", help="find the sections that best match a question")
    search.add_argument("query")
    search.add_argument("--method", choices=[*retrieve.METHODS, "all"], default="hybrid")
    search.add_argument("-k", type=int, default=5, help="number of results (default 5)")
    return parser


def search(query: str, method: str, k: int) -> None:
    methods = retrieve.METHODS if method == "all" else (method,)
    vectors = any(m in ("vector", "hybrid") for m in methods)
    retriever = retrieve.from_files(PASSAGES_PATH, EMBEDDINGS_PATH, vectors=vectors)
    for m in methods:
        print(f"\n{m}:")
        for rank, (passage, score) in enumerate(retriever.search(query, m, k), start=1):
            label = passage["title"] or passage["text"][:60] + "..."
            print(f"{rank:>3}. {passage['id']:<12} {score:8.4f}  {label}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "fetch":
        for path in fetch.fetch_all(RAW_DIR):
            print(f"Saved {path}")
    elif args.command == "build":
        count = parse.build(RAW_DIR, PASSAGES_PATH)
        print(f"Wrote {count} passages to {PASSAGES_PATH}")
    elif args.command == "search":
        search(args.query, args.method, args.k)
    else:
        parser.print_help()
    return 0
