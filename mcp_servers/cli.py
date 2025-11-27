"""Command-line interface for MCP ingestion servers.

The CLI uses a two-level subcommand structure:
    python -m mcp_servers.cli <provider> <action>

Where provider is one of: congress, govinfo, openstates
And action is one of: list, ingest (or scrape for openstates)

This structure maps directly to the MCP tool definitions:
    - congress_list_endpoints  -> congress list
    - congress_bulk_ingest     -> congress ingest
    - govinfo_list_endpoints   -> govinfo list
    - govinfo_bulk_ingest      -> govinfo ingest
    - openstates_list_endpoints -> openstates list
    - openstates_bulk_ingest   -> openstates ingest
    - openstates_run_scrapers  -> openstates scrape
"""

import argparse
import json
import sys
from typing import Any, Dict, List

from .congress import CongressServer
from .govinfo import GovInfoServer
from .openstates import OpenStatesServer


def summarize_counts(counts: Dict[str, int]) -> str:
    return ", ".join(f"{name}: {count}" for name, count in counts.items())


def _parse_json_arg(value: str | None, arg_name: str) -> Dict[str, Any] | None:
    """Parse a JSON argument with error handling."""
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON for {arg_name}: {e}", file=sys.stderr)
        sys.exit(1)


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
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_offsets, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


# OpenStates commands
def openstates_list(args: argparse.Namespace) -> None:
    """List OpenStates API endpoints and pagination info."""
    server = OpenStatesServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def openstates_ingest(args: argparse.Namespace) -> None:
    """Ingest OpenStates API data with optional start pages and page sizes."""
    server = OpenStatesServer(api_key=args.api_key)
    start_pages = _parse_json_arg(args.start_pages, "--start-pages")
    page_sizes = _parse_json_arg(args.page_sizes, "--page-sizes")
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_pages, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


def openstates_scrape(args: argparse.Namespace) -> None:
    """Execute openstates-scrapers for specified states."""
    server = OpenStatesServer(api_key=args.api_key)
    result = server.run_scrapers(states=args.states)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MCP ingestion servers for legislative APIs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m mcp_servers.cli congress list
    python -m mcp_servers.cli congress ingest --start-offsets '{"bills": 100}'
    python -m mcp_servers.cli govinfo list
    python -m mcp_servers.cli govinfo ingest --page-sizes '{"collections": 50}'
    python -m mcp_servers.cli openstates list
    python -m mcp_servers.cli openstates ingest --start-pages '{"bills": 2}'
    python -m mcp_servers.cli openstates scrape --states NY CA
""",
    )
    provider_subparsers = parser.add_subparsers(dest="provider", required=True, help="Data provider")

    # Congress subcommand
    congress_parser = provider_subparsers.add_parser("congress", help="Congress.gov data")
    congress_subparsers = congress_parser.add_subparsers(dest="action", required=True, help="Action to perform")

    congress_list_parser = congress_subparsers.add_parser("list", help="List endpoints and pagination info")
    congress_list_parser.add_argument("--api-key", dest="api_key", help="API key for Congress.gov")
    congress_list_parser.set_defaults(func=congress_list)

    congress_ingest_parser = congress_subparsers.add_parser("ingest", help="Ingest data from all endpoints")
    congress_ingest_parser.add_argument("--api-key", dest="api_key", help="API key for Congress.gov")
    congress_ingest_parser.add_argument("--start-offsets", help="JSON map of starting offsets per endpoint")
    congress_ingest_parser.add_argument("--page-sizes", help="JSON map of page sizes per endpoint")
    congress_ingest_parser.set_defaults(func=congress_ingest)

    # GovInfo subcommand
    govinfo_parser = provider_subparsers.add_parser("govinfo", help="GovInfo.gov data")
    govinfo_subparsers = govinfo_parser.add_subparsers(dest="action", required=True, help="Action to perform")

    govinfo_list_parser = govinfo_subparsers.add_parser("list", help="List endpoints and pagination info")
    govinfo_list_parser.add_argument("--api-key", dest="api_key", help="API key for GovInfo.gov")
    govinfo_list_parser.set_defaults(func=govinfo_list)

    govinfo_ingest_parser = govinfo_subparsers.add_parser("ingest", help="Ingest data from all endpoints")
    govinfo_ingest_parser.add_argument("--api-key", dest="api_key", help="API key for GovInfo.gov")
    govinfo_ingest_parser.add_argument("--start-offsets", help="JSON map of starting offsets per endpoint")
    govinfo_ingest_parser.add_argument("--page-sizes", help="JSON map of page sizes per endpoint")
    govinfo_ingest_parser.set_defaults(func=govinfo_ingest)

    # OpenStates subcommand
    openstates_parser = provider_subparsers.add_parser("openstates", help="OpenStates API data")
    openstates_subparsers = openstates_parser.add_subparsers(dest="action", required=True, help="Action to perform")

    openstates_list_parser = openstates_subparsers.add_parser("list", help="List endpoints and pagination info")
    openstates_list_parser.add_argument("--api-key", dest="api_key", help="API key for OpenStates")
    openstates_list_parser.set_defaults(func=openstates_list)

    openstates_ingest_parser = openstates_subparsers.add_parser("ingest", help="Ingest data from all endpoints")
    openstates_ingest_parser.add_argument("--api-key", dest="api_key", help="API key for OpenStates")
    openstates_ingest_parser.add_argument("--start-pages", help="JSON map of starting pages per endpoint")
    openstates_ingest_parser.add_argument("--page-sizes", help="JSON map of page sizes per endpoint")
    openstates_ingest_parser.set_defaults(func=openstates_ingest)

    openstates_scrape_parser = openstates_subparsers.add_parser("scrape", help="Run openstates-scrapers")
    openstates_scrape_parser.add_argument("--api-key", dest="api_key", help="API key for OpenStates")
    openstates_scrape_parser.add_argument("--states", nargs="*", help="State abbreviations to scrape")
    openstates_scrape_parser.set_defaults(func=openstates_scrape)

    return parser


def main(argv: List[str] | None = None) -> Any:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    main()
