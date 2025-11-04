"""Command line interface for Congress.gov ingestion."""
from __future__ import annotations

import argparse
from pathlib import Path

from ..clients import CongressGovIngestClient
from ..cli.common import configure_logging, handle_records


def build_parser() -> argparse.ArgumentParser:
    """
    Create an ArgumentParser configured for the Congress.gov ingestion CLI.
    
    Returns:
        argparse.ArgumentParser: Parser with a positional `command` choice of "bills", "members", or "votes", and options `--congress`, `--chamber`, `--limit`, `--export`, `--upsert`, `--database-url`, and `--verbose`.
    """
    parser = argparse.ArgumentParser(description="Ingest data from api.congress.gov")
    parser.add_argument("command", choices=["bills", "members", "votes"], help="Resource to fetch")
    parser.add_argument("--congress", default="118", help="Congress number (e.g., 118)")
    parser.add_argument("--chamber", help="Legislative chamber for member/vote endpoints")
    parser.add_argument("--limit", type=int, default=250, help="Maximum records per request")
    parser.add_argument("--export", type=Path, help="Optional JSONL export path")
    parser.add_argument("--upsert", action="store_true", help="Persist results into PostgreSQL")
    parser.add_argument(
        "--database-url",
        help="Override database connection string (defaults to FEDERAL_INGEST_DATABASE_URL or db_config)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: list[str] | None = None) -> None:
    """
    Parse CLI arguments, fetch the requested Congress.gov resource, and process the resulting records.
    
    Parses the provided argv (or system arguments if None), configures logging according to --verbose, and uses a CongressGovIngestClient to iterate records for the selected command ("bills", "members", or "votes"). The --chamber option is required for "members" and "votes" commands; if omitted the parser will report an error. Fetched records are forwarded to handle_records with export, upsert, and database_url options from the parsed arguments.
    
    Parameters:
        argv (list[str] | None): Optional list of command-line arguments to parse; when None the system arguments are used.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    with CongressGovIngestClient() as client:
        if args.command == "bills":
            records = client.iter_bills(congress=args.congress, limit=args.limit)
        elif args.command == "members":
            if not args.chamber:
                parser.error("--chamber is required for members")
            records = client.iter_members(congress=args.congress, chamber=args.chamber, limit=args.limit)
        else:
            if not args.chamber:
                parser.error("--chamber is required for votes")
            records = client.iter_votes(congress=args.congress, chamber=args.chamber, limit=args.limit)

        handle_records(
            records,
            export_path=args.export,
            upsert=args.upsert,
            database_url=args.database_url,
        )


if __name__ == "__main__":
    main()