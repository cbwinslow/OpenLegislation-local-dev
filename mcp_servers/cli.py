"""Command-line interface for MCP ingestion servers.


"""

import argparse
import json
import sys


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

    print(f"Ingested: {summarize_counts(counts)}")



def openstates_scrape(args: argparse.Namespace) -> None:
    """Execute openstates-scrapers for specified states."""
    server = OpenStatesServer(api_key=args.api_key)
    result = server.run_scrapers(states=args.states)


    openstates_scrape_parser.set_defaults(func=openstates_scrape)

    return parser


def main(argv: List[str] | None = None) -> Any:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    main()
