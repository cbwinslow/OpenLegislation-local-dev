"""Command-line interface for MCP ingestion servers.

This CLI is designed to align with MCP tool schemas defined in mcp_integration.py.
Each provider (congress, govinfo, openstates) has explicit subcommands:

  - `<provider> list`: List configured endpoints and pagination info
  - `<provider> ingest`: Bulk ingest data from the provider's API

This structure directly maps to MCP tools like:
  - congress_list_endpoints -> `python -m mcp_servers.cli congress list`
  - congress_bulk_ingest -> `python -m mcp_servers.cli congress ingest [options]`

For OpenStates, an additional `scrape` subcommand is available:
  - openstates_run_scrapers -> `python -m mcp_servers.cli openstates scrape [--states ...]`
"""

import argparse
import json
from typing import Any, Dict, List

from .congress import CongressServer
from .govinfo import GovInfoServer
from .openstates import OpenStatesServer


def summarize_counts(counts: Dict[str, int]) -> str:
    return ", ".join(f"{name}: {count}" for name, count in counts.items())


# --- Congress subcommands ---


def congress_list(args: argparse.Namespace) -> None:
    """List Congress.gov endpoints and pagination info."""
    server = CongressServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def congress_ingest(args: argparse.Namespace) -> None:
    """Ingest Congress.gov data with optional start offsets and page sizes."""
    server = CongressServer(api_key=args.api_key)
    start_offsets = json.loads(args.start_offsets) if args.start_offsets else {}
    page_sizes = json.loads(args.page_sizes) if args.page_sizes else {}

    for endpoint in server.endpoints:
        for page in server.fetch_paginated(
            endpoint,
            start=start_offsets.get(endpoint.name),
            page_size=page_sizes.get(endpoint.name),
        ):
            for record in page.get("results", []):
                print(json.dumps(record))


# --- GovInfo subcommands ---


def govinfo_list(args: argparse.Namespace) -> None:
    """List GovInfo.gov endpoints and pagination info."""
    server = GovInfoServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def govinfo_ingest(args: argparse.Namespace) -> None:
    """Ingest GovInfo.gov data with optional start offsets and page sizes."""
    server = GovInfoServer(api_key=args.api_key)
    start_offsets = json.loads(args.start_offsets) if args.start_offsets else None
    page_sizes = json.loads(args.page_sizes) if args.page_sizes else None
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_offsets, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


# --- OpenStates subcommands ---


def openstates_list(args: argparse.Namespace) -> None:
    """List OpenStates API endpoints and pagination info."""
    server = OpenStatesServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def openstates_ingest(args: argparse.Namespace) -> None:
    """Ingest OpenStates API data with optional start pages and page sizes."""
    server = OpenStatesServer(api_key=args.api_key)
    start_pages = json.loads(args.start_offsets) if args.start_offsets else None
    page_sizes = json.loads(args.page_sizes) if args.page_sizes else None
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_pages, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


def openstates_scrape(args: argparse.Namespace) -> None:
    """Execute openstates-scrapers for specified states."""
    server = OpenStatesServer(api_key=args.api_key)
    result = server.run_scrapers(states=args.states)
    print(result.stdout)
    print(result.stderr)


def _add_api_key_arg(parser: argparse.ArgumentParser) -> None:
    """Add the common --api-key argument to a parser."""
    parser.add_argument("--api-key", dest="api_key", help="API key for the provider")


def _add_ingest_args(parser: argparse.ArgumentParser) -> None:
    """Add common arguments for ingest subcommands."""
    _add_api_key_arg(parser)
    parser.add_argument("--start-offsets", help="JSON map of starting offsets/pages per endpoint")
    parser.add_argument("--page-sizes", help="JSON map of page sizes per endpoint")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MCP ingestion servers for legislative APIs")
    subparsers = parser.add_subparsers(dest="provider", required=True)

    # --- Congress provider ---
    congress_parser = subparsers.add_parser("congress", help="Interact with Congress.gov API")
    congress_subparsers = congress_parser.add_subparsers(dest="action", required=True)

    congress_list_parser = congress_subparsers.add_parser("list", help="List configured endpoints")
    _add_api_key_arg(congress_list_parser)
    congress_list_parser.set_defaults(func=congress_list)

    congress_ingest_parser = congress_subparsers.add_parser("ingest", help="Bulk ingest data")
    _add_ingest_args(congress_ingest_parser)
    congress_ingest_parser.set_defaults(func=congress_ingest)

    # --- GovInfo provider ---
    govinfo_parser = subparsers.add_parser("govinfo", help="Interact with GovInfo.gov API")
    govinfo_subparsers = govinfo_parser.add_subparsers(dest="action", required=True)

    govinfo_list_parser = govinfo_subparsers.add_parser("list", help="List configured endpoints")
    _add_api_key_arg(govinfo_list_parser)
    govinfo_list_parser.set_defaults(func=govinfo_list)

    govinfo_ingest_parser = govinfo_subparsers.add_parser("ingest", help="Bulk ingest data")
    _add_ingest_args(govinfo_ingest_parser)
    govinfo_ingest_parser.set_defaults(func=govinfo_ingest)

    # --- OpenStates provider ---
    openstates_parser = subparsers.add_parser("openstates", help="Interact with OpenStates API or scrapers")
    openstates_subparsers = openstates_parser.add_subparsers(dest="action", required=True)

    openstates_list_parser = openstates_subparsers.add_parser("list", help="List configured endpoints")
    _add_api_key_arg(openstates_list_parser)
    openstates_list_parser.set_defaults(func=openstates_list)

    openstates_ingest_parser = openstates_subparsers.add_parser("ingest", help="Bulk ingest data")
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
