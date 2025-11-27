"""Command-line interface for MCP ingestion servers."""

import argparse
import json
from typing import Any, Dict, List

from .congress import CongressServer
from .govinfo import GovInfoServer
from .openstates import OpenStatesServer


def summarize_counts(counts: Dict[str, int]) -> str:
    return ", ".join(f"{name}: {count}" for name, count in counts.items())


def run_congress(args: argparse.Namespace) -> None:
    server = CongressServer(api_key=args.api_key)
    if args.list:
        print(json.dumps(server.list_endpoints(), indent=2))
        return
    try:
        start_offsets = json.loads(args.start_offsets) if args.start_offsets else {}
        page_sizes = json.loads(args.page_sizes) if args.page_sizes else {}
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}")
        return

    for endpoint in server.endpoints:
        for page in server.fetch_paginated(
            endpoint,
            start=start_offsets.get(endpoint.name),
            page_size=page_sizes.get(endpoint.name),
        ):
            for record in page.get("results", []):
                print(json.dumps(record))


def run_govinfo(args: argparse.Namespace) -> None:
    server = GovInfoServer(api_key=args.api_key)
    if args.list:
        print(json.dumps(server.list_endpoints(), indent=2))
        return
    try:
        start_offsets = json.loads(args.start_offsets) if args.start_offsets else None
        page_sizes = json.loads(args.page_sizes) if args.page_sizes else None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}")
        return
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_offsets, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


def run_openstates(args: argparse.Namespace) -> None:
    server = OpenStatesServer(api_key=args.api_key)
    if args.list:
        print(json.dumps(server.list_endpoints(), indent=2))
        return
    if args.scrape:
        result = server.run_scrapers(states=args.states)
        print(result.stdout)
        print(result.stderr)
        return
    try:
        start_pages = json.loads(args.start_offsets) if args.start_offsets else None
        page_sizes = json.loads(args.page_sizes) if args.page_sizes else None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}")
        return
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_pages, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MCP ingestion servers for legislative APIs")
    subparsers = parser.add_subparsers(dest="provider", required=True)

    def add_shared(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--api-key", dest="api_key", help="API key for the provider")
        subparser.add_argument("--list", action="store_true", help="List configured endpoints and exit")
        subparser.add_argument("--start-offsets", help="JSON map of starting offsets/pages per endpoint")
        subparser.add_argument("--page-sizes", help="JSON map of page sizes per endpoint")

    congress_parser = subparsers.add_parser("congress", help="Ingest from Congress.gov")
    add_shared(congress_parser)
    congress_parser.set_defaults(func=run_congress)

    govinfo_parser = subparsers.add_parser("govinfo", help="Ingest from GovInfo.gov")
    add_shared(govinfo_parser)
    govinfo_parser.set_defaults(func=run_govinfo)

    openstates_parser = subparsers.add_parser("openstates", help="Ingest from OpenStates API or scrapers")
    add_shared(openstates_parser)
    openstates_parser.add_argument("--scrape", action="store_true", help="Run openstates-scrapers instead of API pulls")
    openstates_parser.add_argument("--states", nargs="*", help="Limit scraper runs to specific states")
    openstates_parser.set_defaults(func=run_openstates)

    return parser


def main(argv: List[str] | None = None) -> Any:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    main()
