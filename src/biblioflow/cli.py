"""Command-line interface for biblioflow."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from biblioflow import __version__
from biblioflow.analysis import analyze
from biblioflow.export import export
from biblioflow.load import load


def _add_load_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", help="Input bibliographic file")
    parser.add_argument("--provider", default="auto", help="Semantic provider")
    parser.add_argument("--format", default="auto", help="Input format")


def _cmd_convert(args: argparse.Namespace) -> int:
    dataset = load(args.input, provider=args.provider, format=args.format)
    export(dataset, args.output, format=args.to)
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    dataset = load(args.input, provider=args.provider, format=args.format)
    summary = analyze(dataset, top_n=args.top_n)
    text = json.dumps(summary.to_dict(), indent=2, default=str)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(prog="biblioflow")
    parser.add_argument(
        "--version", action="version", version=f"biblioflow {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command")

    convert = subparsers.add_parser("convert", help="Convert records to JSON or CSV")
    _add_load_options(convert)
    convert.add_argument("-o", "--output", required=True, help="Output path")
    convert.add_argument("--to", choices=["json", "csv"], default="json")
    convert.set_defaults(func=_cmd_convert)

    analyze_parser = subparsers.add_parser("analyze", help="Print descriptive summary")
    _add_load_options(analyze_parser)
    analyze_parser.add_argument("-o", "--output", help="Optional JSON output path")
    analyze_parser.add_argument("--top-n", type=int, default=20)
    analyze_parser.set_defaults(func=_cmd_analyze)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the biblioflow command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
