"""Command-line interface for MCP ingestion servers."""

import argparse
import json
from typing import Any, Dict, List

from .congress import CongressServer
from .govinfo import GovInfoServer
from .openstates import OpenStatesServer


def summarize_counts(counts: Dict[str, int]) -> str:
    """
    Create a human-readable comma-separated list of provider counts.
    
    Args:
        counts (Dict[str, int]): Mapping of provider name to its associated count.
    
    Returns:
        str: Comma-separated string of "name: count" pairs in the mapping's iteration order; an empty string if `counts` is empty.
    """
    return ", ".join(f"{name}: {count}" for name, count in counts.items())


def run_congress(args: argparse.Namespace) -> None:
    """
    Run the Congress ingestion flow or output the server's endpoint list based on parsed CLI arguments.
    
    Args:
        args (argparse.Namespace): Parsed CLI arguments. Expected attributes:
            - api_key (str | None): API key used to construct the CongressServer.
            - list (bool): If true, prints the server's endpoint list as JSON and exits.
            - start_offsets (str | None): JSON string mapping endpoint names to start offsets; parsed when provided.
            - page_sizes (str | None): JSON string mapping endpoint names to page size overrides; parsed when provided.
    
    Raises:
        json.JSONDecodeError: If `start_offsets` or `page_sizes` contains invalid JSON.
        Exception: Propagates exceptions raised by CongressServer construction or its methods (e.g., network or ingestion errors).
    
    Side effects:
        - Prints JSON-formatted endpoint list to stdout when `args.list` is true.
        - Otherwise, performs ingestion via the CongressServer and prints an "Ingested: ..." summary line to stdout.
    """
    server = CongressServer(api_key=args.api_key)
    if args.list:
        print(json.dumps(server.list_endpoints(), indent=2))
        return
    start_offsets = json.loads(args.start_offsets) if args.start_offsets else None
    page_sizes = json.loads(args.page_sizes) if args.page_sizes else None
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_offsets, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


def run_govinfo(args: argparse.Namespace) -> None:
    """
    Run GovInfo ingestion or list available endpoints according to CLI arguments.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments. Expected attributes:
            api_key (str | None): API key passed to GovInfoServer.
            list (bool): If true, print the server's endpoint list as formatted JSON and exit.
            start_offsets (str | None): JSON string mapping endpoint names to start offsets/pages; parsed with json.loads when provided.
            page_sizes (str | None): JSON string mapping endpoint names to page size overrides; parsed with json.loads when provided.
    
    Side effects:
        - Instantiates a GovInfoServer and may perform network operations.
        - If `args.list` is true, prints the server's endpoints as JSON.
        - Otherwise, triggers ingestion via the server and prints a summary line like "Ingested: ...".
    """
    server = GovInfoServer(api_key=args.api_key)
    if args.list:
        print(json.dumps(server.list_endpoints(), indent=2))
        return
    start_offsets = json.loads(args.start_offsets) if args.start_offsets else None
    page_sizes = json.loads(args.page_sizes) if args.page_sizes else None
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_offsets, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


def run_openstates(args: argparse.Namespace) -> None:
    """
    Run the OpenStates ingestion workflow according to parsed CLI arguments.
    
    Depending on args, this will either print the server's endpoint list, execute scrapers and print their stdout/stderr, or ingest API endpoints with optional paging overrides and print an ingestion summary.
    
    Args:
        args (argparse.Namespace): Parsed command-line arguments with the following relevant attributes:
            - api_key: API key string used to instantiate the OpenStatesServer.
            - list (bool): If true, print the server's endpoint list as JSON and exit.
            - scrape (bool): If true, run scrapers for the states specified and exit.
            - states (Optional[Sequence[str]]): States to pass to the scraper when --scrape is used.
            - start_offsets (Optional[str]): JSON string mapping endpoint names to start page numbers; parsed when present.
            - page_sizes (Optional[str]): JSON string mapping endpoint names to page size overrides; parsed when present.
    
    Returns:
        None
    
    Side effects:
        - Prints JSON endpoint listings, scraper stdout/stderr, or a one-line ingestion summary to stdout.
        - Instantiates and calls methods on OpenStatesServer which perform network I/O and data ingestion.
    """
    server = OpenStatesServer(api_key=args.api_key)
    if args.list:
        print(json.dumps(server.list_endpoints(), indent=2))
        return
    if args.scrape:
        result = server.run_scrapers(states=args.states)
        print(result.stdout)
        print(result.stderr)
        return
    start_pages = json.loads(args.start_offsets) if args.start_offsets else None
    page_sizes = json.loads(args.page_sizes) if args.page_sizes else None
    counts = server.ingest_endpoints(server.endpoints, start_offsets=start_pages, page_size_overrides=page_sizes)
    print(f"Ingested: {summarize_counts(counts)}")


def build_parser() -> argparse.ArgumentParser:
    """
    Constructs and returns the top-level argument parser for the MCP ingestion CLI.
    
    The parser provides required subcommands for the supported providers: "congress",
    "govinfo", and "openstates". Each provider subparser exposes shared options:
    --api-key, --list, --start-offsets, and --page-sizes. The "openstates"
    subcommand also supports --scrape and --states.
    
    Returns:
        argparse.ArgumentParser: An ArgumentParser configured with provider
        subparsers. When parsed, the resulting Namespace includes a required
        `provider` attribute and a `func` attribute bound to the handler for the
        chosen subcommand.
    
    Side effects / notes:
        - The provider subcommand is required; invoking the CLI without a subcommand
          will display usage and exit.
        - Subparsers set a `func` default so callers can dispatch via `args.func(args)`.
    """
    parser = argparse.ArgumentParser(description="MCP ingestion servers for legislative APIs")
    subparsers = parser.add_subparsers(dest="provider", required=True)

    def add_shared(subparser: argparse.ArgumentParser) -> None:
        """
        Add common CLI arguments to a provider subparser.
        
        Args:
            subparser (argparse.ArgumentParser): The subparser to which shared options are added. Expected to be a subparser for a provider command (e.g., "congress", "govinfo", "openstates").
        
        Returns:
            None
        
        Side effects:
            Mutates the provided subparser by adding the following command-line options:
              --api-key: string, stored as `api_key`
              --list: boolean flag to list configured endpoints and exit
              --start-offsets: JSON string mapping endpoint names to starting offsets/pages
              --page-sizes: JSON string mapping endpoint names to page size overrides
        """
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
    """
    Parse command-line arguments and invoke the selected subcommand handler.
    
    Args:
        argv (list[str] | None): Sequence of command-line arguments to parse (excluding program name).
            If None, uses the system argv.
    
    Returns:
        Any: The value returned by the subcommand function bound to the parsed arguments.
    
    Raises:
        SystemExit: If argument parsing fails or a subcommand triggers process exit.
        Exception: Any exception raised by the invoked subcommand is propagated.
    
    Side effects:
        Calls the selected subcommand function (args.func), which may perform I/O, network requests,
        or other actions that affect process state.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    main()