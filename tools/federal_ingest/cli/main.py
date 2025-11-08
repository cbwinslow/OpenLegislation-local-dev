"""Unified entrypoint for federal ingestion CLIs."""
from __future__ import annotations

import argparse
from typing import List

from . import congress_cli, govinfo_api_cli, govinfo_bulk_cli


def build_parser() -> argparse.ArgumentParser:
    """
    Create an ArgumentParser configured for the federal ingestion toolkit.
    
    The parser defines a required positional `source` (choices: "congress", "govinfo-api", "govinfo-bulk")
    and a positional `args` that captures all remaining arguments to forward to the chosen sub-CLI.
    
    Returns:
        argparse.ArgumentParser: Parser configured with the `source` and `args` positional arguments.
    """
    parser = argparse.ArgumentParser(description="Federal ingestion toolkit")
    parser.add_argument(
        "source",
        choices=["congress", "govinfo-api", "govinfo-bulk"],
        help="Which upstream source to interact with",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the specific source CLI",
    )
    return parser


def main(argv: List[str] | None = None) -> None:
    """
    Parse top-level CLI arguments and dispatch execution to the selected federal ingestion sub-CLI.
    
    Parameters:
        argv (List[str] | None): Command-line arguments to parse. If `None`, the function parses the process command-line.
        
    Description:
        Selects one of the sub-CLIs ("congress", "govinfo-api", or "govinfo-bulk") based on the parsed `source` value and forwards the remaining arguments to that sub-CLI's `main` function.
    """
    parser = build_parser()
    parsed = parser.parse_args(argv)
    remaining = parsed.args
    if parsed.source == "congress":
        congress_cli.main(remaining)
    elif parsed.source == "govinfo-api":
        govinfo_api_cli.main(remaining)
    else:
        govinfo_bulk_cli.main(remaining)


if __name__ == "__main__":
    main()