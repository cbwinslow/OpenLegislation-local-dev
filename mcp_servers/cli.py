"""Command-line interface for MCP ingestion servers.

This CLI exposes explicit subcommands for each tool action to align with MCP tool
definitions. Each provider (congress, govinfo, openstates) has `list` and `ingest`
subcommands, plus `scrape` for openstates.

Examples:
    python -m mcp_servers.cli congress list
    python -m mcp_servers.cli congress ingest --start-offsets '{"bills":0}'
    python -m mcp_servers.cli openstates scrape --states ny ca
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from .congress import CongressServer
from .govinfo import GovInfoServer
from .openstates import OpenStatesServer


def _parse_json_arg(value: Optional[str], arg_name: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON string argument with error handling."""
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format for {arg_name}: {e}", file=sys.stderr)
        sys.exit(1)


def summarize_counts(counts: Dict[str, int]) -> str:
    return ", ".join(f"{name}: {count}" for name, count in counts.items())


# Congress commands
def congress_list(args: argparse.Namespace) -> None:
    """List Congress.gov endpoints and pagination info."""
    server = CongressServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def congress_ingest(args: argparse.Namespace) -> None:
    """Ingest Congress.gov data with optional start offsets and page sizes."""
    server = CongressServer(api_key=args.api_key)
    start_offsets = _parse_json_arg(args.start_offsets, "--start-offsets") or {}
    page_sizes = _parse_json_arg(args.page_sizes, "--page-sizes") or {}

    for endpoint in server.endpoints:
        for page in server.fetch_paginated(
            endpoint,
            start=start_offsets.get(endpoint.name),
            page_size=page_sizes.get(endpoint.name),
        ):
            for record in page.get("results", []):
                print(json.dumps(record))


# GovInfo commands
def govinfo_list(args: argparse.Namespace) -> None:
    """List GovInfo.gov endpoints and pagination info."""
    server = GovInfoServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def govinfo_ingest(args: argparse.Namespace) -> None:
    """Ingest GovInfo.gov data with optional start offsets and page sizes."""
    server = GovInfoServer(api_key=args.api_key)
    start_offsets = _parse_json_arg(args.start_offsets, "--start-offsets")
    page_sizes = _parse_json_arg(args.page_sizes, "--page-sizes")
    counts = server.ingest_endpoints(
        server.endpoints,
        start_offsets=start_offsets,
        page_size_overrides=page_sizes,
    )
    print(f"Ingested: {summarize_counts(counts)}")


# OpenStates commands
def openstates_list(args: argparse.Namespace) -> None:
    """List OpenStates API endpoints and pagination info."""
    server = OpenStatesServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def openstates_ingest(args: argparse.Namespace) -> None:
    """Ingest OpenStates API data with optional start pages and page sizes."""
    server = OpenStatesServer(api_key=args.api_key)
    start_pages = _parse_json_arg(args.start_offsets, "--start-offsets")
    page_sizes = _parse_json_arg(args.page_sizes, "--page-sizes")
    counts = server.ingest_endpoints(
        server.endpoints,
        start_offsets=start_pages,
        page_size_overrides=page_sizes,
    )
    print(f"Ingested: {summarize_counts(counts)}")


def openstates_scrape(args: argparse.Namespace) -> None:
    """Execute openstates-scrapers for specified states."""
    server = OpenStatesServer(api_key=args.api_key)
    result = server.run_scrapers(states=args.states)
    if result.stdout:
        print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)


def _add_api_key_arg(parser: argparse.ArgumentParser) -> None:
    """Add the --api-key argument to a parser."""
    parser.add_argument("--api-key", dest="api_key", help="API key for the provider")


def _add_ingest_args(parser: argparse.ArgumentParser) -> None:
    """Add common ingestion arguments to a parser."""
    _add_api_key_arg(parser)
    parser.add_argument("--start-offsets", help="JSON map of starting offsets/pages per endpoint")
    parser.add_argument("--page-sizes", help="JSON map of page sizes per endpoint")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MCP ingestion servers for legislative APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    provider_subparsers = parser.add_subparsers(dest="provider", required=True)

    # Congress subcommands
    congress_parser = provider_subparsers.add_parser("congress", help="Congress.gov operations")
    congress_subparsers = congress_parser.add_subparsers(dest="action", required=True)

    congress_list_parser = congress_subparsers.add_parser("list", help="List endpoints and pagination info")
    _add_api_key_arg(congress_list_parser)
    congress_list_parser.set_defaults(func=congress_list)

    congress_ingest_parser = congress_subparsers.add_parser("ingest", help="Ingest data from Congress.gov")
    _add_ingest_args(congress_ingest_parser)
    congress_ingest_parser.set_defaults(func=congress_ingest)

    # GovInfo subcommands
    govinfo_parser = provider_subparsers.add_parser("govinfo", help="GovInfo.gov operations")
    govinfo_subparsers = govinfo_parser.add_subparsers(dest="action", required=True)

    govinfo_list_parser = govinfo_subparsers.add_parser("list", help="List endpoints and pagination info")
    _add_api_key_arg(govinfo_list_parser)
    govinfo_list_parser.set_defaults(func=govinfo_list)

    govinfo_ingest_parser = govinfo_subparsers.add_parser("ingest", help="Ingest data from GovInfo.gov")
    _add_ingest_args(govinfo_ingest_parser)
    govinfo_ingest_parser.set_defaults(func=govinfo_ingest)

    # OpenStates subcommands
    openstates_parser = provider_subparsers.add_parser("openstates", help="OpenStates API operations")
    openstates_subparsers = openstates_parser.add_subparsers(dest="action", required=True)

    openstates_list_parser = openstates_subparsers.add_parser("list", help="List endpoints and pagination info")
    _add_api_key_arg(openstates_list_parser)
    openstates_list_parser.set_defaults(func=openstates_list)

    openstates_ingest_parser = openstates_subparsers.add_parser("ingest", help="Ingest data from OpenStates API")
    _add_ingest_args(openstates_ingest_parser)
    openstates_ingest_parser.set_defaults(func=openstates_ingest)

    openstates_scrape_parser = openstates_subparsers.add_parser("scrape", help="Run openstates-scrapers")
    _add_api_key_arg(openstates_scrape_parser)
    openstates_scrape_parser.add_argument("--states", nargs="*", help="Limit scraper runs to specific states")
    openstates_scrape_parser.set_defaults(func=openstates_scrape)

    return parser


def main(argv: List[str] | None = None) -> Any:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    main()
