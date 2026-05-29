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
from biblioflow.reporting import ReportProject, generate_report
from biblioflow.sources import from_pubmed, from_pubmed_central


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


def _cmd_search(args: argparse.Namespace) -> int:
    """
    title: Run an API-backed search command.
    parameters:
      args:
        type: argparse.Namespace
        description: Parsed command arguments.
    returns:
      type: int
    """
    if args.source == "pubmed":
        dataset = from_pubmed(
            query=args.query,
            limit=args.limit,
            tool=args.tool,
            email=args.email,
            api_key=args.api_key,
        )
    else:
        dataset = from_pubmed_central(
            query=args.query,
            limit=args.limit,
            tool=args.tool,
            email=args.email,
            api_key=args.api_key,
        )
    export(dataset, args.output, format=args.to)
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    """
    title: Run the report command.
    parameters:
      args:
        type: argparse.Namespace
        description: Parsed command arguments.
    returns:
      type: int
    """
    input_path = Path(args.input)
    if args.manifest or input_path.suffix.casefold() in {".yaml", ".yml"}:
        project = ReportProject.from_manifest(input_path)
        if args.title:
            project.title = args.title
    else:
        dataset = load(args.input, provider=args.provider, format=args.format)
        if args.deduplicate:
            dataset = deduplicate(dataset)
        project = ReportProject.from_records(
            dataset,
            title=args.title or input_path.stem.replace("-", " ").replace("_", " "),
            subtitle=args.subtitle,
            authors=args.author or [],
            organization=args.organization,
        )
    result = generate_report(
        project,
        output=args.output,
        template=args.template,
        completeness=args.completeness,
        top_n=args.top_n,
        render=not args.no_render,
        keep_qmd=args.keep_qmd or args.no_render,
        keep_context=args.keep_context or args.no_render,
    )
    print(json.dumps(result.to_dict(), indent=2, default=str))
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

    search_parser = subparsers.add_parser("search", help="Search remote sources")
    search_subparsers = search_parser.add_subparsers(dest="source")
    for source, help_text in (
        ("pubmed", "Search PubMed"),
        ("pmc", "Search PubMed Central"),
    ):
        source_parser = search_subparsers.add_parser(source, help=help_text)
        source_parser.add_argument("--query", required=True, help="Search query")
        source_parser.add_argument("--email", help="NCBI contact email")
        source_parser.add_argument("--api-key", help="NCBI API key")
        source_parser.add_argument(
            "--tool", default="biblioflow", help="NCBI tool name"
        )
        source_parser.add_argument("--limit", type=int, default=100)
        source_parser.add_argument("-o", "--output", required=True)
        source_parser.add_argument(
            "--to", choices=["json", "csv", "yaml"], default="json"
        )
        source_parser.set_defaults(func=_cmd_search, source=source)

    report_parser = subparsers.add_parser(
        "report", help="Generate a professional Quarto/Typst project PDF report"
    )
    report_parser.add_argument("input", help="Input bibliographic file or project YAML")
    report_parser.add_argument("-o", "--output", required=True, help="Output PDF path")
    report_parser.add_argument("--provider", default="auto", help="Semantic provider")
    report_parser.add_argument("--format", default="auto", help="Input format")
    report_parser.add_argument("--title", help="Report title")
    report_parser.add_argument("--subtitle", help="Report subtitle")
    report_parser.add_argument("--author", action="append", help="Report author")
    report_parser.add_argument("--organization", help="Organization or lab name")
    report_parser.add_argument("--template", default="modern")
    report_parser.add_argument(
        "--completeness",
        choices=["summary", "standard", "complete"],
        default="standard",
    )
    report_parser.add_argument("--top-n", type=int, default=20)
    report_parser.add_argument("--deduplicate", action="store_true")
    report_parser.add_argument(
        "--manifest",
        action="store_true",
        help="Treat input as a report project manifest",
    )
    report_parser.add_argument(
        "--no-render",
        action="store_true",
        help="Write QMD/context/assets but do not invoke Quarto",
    )
    report_parser.add_argument(
        "--keep-qmd",
        action="store_true",
        help="Keep the generated Quarto QMD file",
    )
    report_parser.add_argument(
        "--keep-context",
        action="store_true",
        help="Keep the generated JSON context file",
    )
    report_parser.set_defaults(func=_cmd_report)

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
