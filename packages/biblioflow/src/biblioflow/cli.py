"""
title: Command-line interface for biblioflow.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from biblioflow import __version__
from biblioflow.analysis import analyze
from biblioflow.export import export
from biblioflow.load import load
from biblioflow.matrices import matrix
from biblioflow.networks import network
from biblioflow.normalize.deduplicate import deduplicate


def _add_load_options(parser: argparse.ArgumentParser) -> None:
    """
    title: Add load options.
    parameters:
      parser:
        type: argparse.ArgumentParser
        description: Parser value.
    """
    parser.add_argument("input", help="Input bibliographic file")
    parser.add_argument("--provider", default="auto", help="Semantic provider")
    parser.add_argument("--format", default="auto", help="Input format")


def _cmd_convert(args: argparse.Namespace) -> int:
    """
    title: Run the convert command.
    parameters:
      args:
        type: argparse.Namespace
        description: Parsed command arguments.
    returns:
      type: int
    """
    dataset = load(args.input, provider=args.provider, format=args.format)
    if args.deduplicate:
        dataset = deduplicate(dataset)
    export(dataset, args.output, format=args.to)
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    """
    title: Run the validate command.
    parameters:
      args:
        type: argparse.Namespace
        description: Parsed command arguments.
    returns:
      type: int
    """
    dataset = load(args.input, provider=args.provider, format=args.format)
    payload = {
        "records": len(dataset),
        "warnings": dataset.warning_dicts(),
        "errors": dataset.errors,
        "metadata": dataset.metadata,
    }
    print(json.dumps(payload, indent=2, default=str))
    return 1 if dataset.errors else 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    """
    title: Run the analyze command.
    parameters:
      args:
        type: argparse.Namespace
        description: Parsed command arguments.
    returns:
      type: int
    """
    dataset = load(args.input, provider=args.provider, format=args.format)
    if args.deduplicate:
        dataset = deduplicate(dataset)
    summary = analyze(dataset, top_n=args.top_n)
    text = json.dumps(summary.to_dict(), indent=2, default=str)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def _cmd_network(args: argparse.Namespace) -> int:
    """
    title: Run the network command.
    parameters:
      args:
        type: argparse.Namespace
        description: Parsed command arguments.
    returns:
      type: int
    """
    dataset = load(args.input, provider=args.provider, format=args.format)
    if args.deduplicate:
        dataset = deduplicate(dataset)
    net = network(
        dataset,
        kind=args.kind,
        unit=args.unit,
        normalize=args.normalize,
        min_occurrences=args.min_occurrences,
    )
    export(net, args.output, format=args.to)
    return 0


def _cmd_matrix(args: argparse.Namespace) -> int:
    """
    title: Run the matrix command.
    parameters:
      args:
        type: argparse.Namespace
        description: Parsed command arguments.
    returns:
      type: int
    """
    dataset = load(args.input, provider=args.provider, format=args.format)
    mat = matrix(
        dataset,
        kind=args.kind,
        unit=args.unit,
        normalize=args.normalize,
        min_occurrences=args.min_occurrences,
    )
    export(mat, args.output, format=args.to)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """
    title: Build the command-line parser.
    returns:
      type: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(prog="biblioflow")
    parser.add_argument(
        "--version", action="version", version=f"biblioflow {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command")

    convert = subparsers.add_parser("convert", help="Convert records to JSON or CSV")
    _add_load_options(convert)
    convert.add_argument("-o", "--output", required=True, help="Output path")
    convert.add_argument("--to", choices=["json", "csv", "yaml"], default="json")
    convert.add_argument("--deduplicate", action="store_true")
    convert.set_defaults(func=_cmd_convert)

    validate_parser = subparsers.add_parser("validate", help="Validate input records")
    _add_load_options(validate_parser)
    validate_parser.set_defaults(func=_cmd_validate)

    analyze_parser = subparsers.add_parser("analyze", help="Print descriptive summary")
    _add_load_options(analyze_parser)
    analyze_parser.add_argument("-o", "--output", help="Optional JSON output path")
    analyze_parser.add_argument("--top-n", type=int, default=20)
    analyze_parser.add_argument("--deduplicate", action="store_true")
    analyze_parser.set_defaults(func=_cmd_analyze)

    matrix_parser = subparsers.add_parser("matrix", help="Build a matrix")
    _add_load_options(matrix_parser)
    matrix_parser.add_argument("-o", "--output", required=True)
    matrix_parser.add_argument("--to", choices=["json", "csv"], default="csv")
    matrix_parser.add_argument("--kind", default="co_occurrence")
    matrix_parser.add_argument("--unit", default="keywords_all")
    matrix_parser.add_argument("--normalize", default=None)
    matrix_parser.add_argument("--min-occurrences", type=int, default=1)
    matrix_parser.set_defaults(func=_cmd_matrix)

    network_parser = subparsers.add_parser("network", help="Build and export a network")
    _add_load_options(network_parser)
    network_parser.add_argument("-o", "--output", required=True)
    network_parser.add_argument(
        "--to",
        choices=["json", "graphml", "gexf", "pajek", "net", "vosviewer", "txt"],
        default="json",
    )
    network_parser.add_argument("--kind", default="co_occurrence")
    network_parser.add_argument("--unit", default="keywords_all")
    network_parser.add_argument("--normalize", default=None)
    network_parser.add_argument("--min-occurrences", type=int, default=1)
    network_parser.add_argument("--deduplicate", action="store_true")
    network_parser.set_defaults(func=_cmd_network)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    title: Run the biblioflow command-line interface.
    parameters:
      argv:
        type: Sequence[str] | None
        description: Command-line argument list.
    returns:
      type: int
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
