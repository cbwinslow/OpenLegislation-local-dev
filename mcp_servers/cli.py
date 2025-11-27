"""Command-line interface for MCP ingestion servers.


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



def congress_list(args: argparse.Namespace) -> None:
    """List Congress.gov endpoints and pagination info."""
    server = CongressServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def congress_ingest(args: argparse.Namespace) -> None:
    """Ingest Congress.gov data with optional start offsets and page sizes."""
    server = CongressServer(api_key=args.api_key)


    for endpoint in server.endpoints:
        for page in server.fetch_paginated(
            endpoint,
            start=start_offsets.get(endpoint.name),
            page_size=page_sizes.get(endpoint.name),
        ):
            for record in page.get("results", []):
                print(json.dumps(record))



def govinfo_list(args: argparse.Namespace) -> None:
    """List GovInfo.gov endpoints and pagination info."""
    server = GovInfoServer(api_key=args.api_key)
    print(json.dumps(server.list_endpoints(), indent=2))


def govinfo_ingest(args: argparse.Namespace) -> None:
    """Ingest GovInfo.gov data with optional start offsets and page sizes."""
    server = GovInfoServer(api_key=args.api_key)

    print(f"Ingested: {summarize_counts(counts)}")


def openstates_scrape(args: argparse.Namespace) -> None:
    """Execute openstates-scrapers for specified states."""
    server = OpenStatesServer(api_key=args.api_key)
    result = server.run_scrapers(states=args.states)



def _add_ingest_args(parser: argparse.ArgumentParser) -> None:

    _add_api_key_arg(parser)
    parser.add_argument("--start-offsets", help="JSON map of starting offsets/pages per endpoint")
    parser.add_argument("--page-sizes", help="JSON map of page sizes per endpoint")


def build_parser() -> argparse.ArgumentParser:

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
