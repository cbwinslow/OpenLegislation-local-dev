"""Unified entrypoint for federal ingestion CLIs."""
from __future__ import annotations

import argparse
from typing import List

from . import congress_cli, govinfo_api_cli, govinfo_bulk_cli


def build_parser() -> argparse.ArgumentParser:
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
