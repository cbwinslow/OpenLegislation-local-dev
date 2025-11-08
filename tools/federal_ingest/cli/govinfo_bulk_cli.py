"""Command line interface for GovInfo bulk data ingestion."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from ..cli.common import configure_logging, handle_records
from ..clients import GovInfoBulkClient
from ..normalization import NormalizedRecord
from ..storage import download_resource


def build_parser() -> argparse.ArgumentParser:
    """
    Create an ArgumentParser configured for ingesting GovInfo bulkdata and common CLI options.
    
    The parser includes the following options:
    - --collection (required): GovInfo collection code (e.g., BILLS, BILLSTATUS)
    - --congress: optional congress filter (e.g., 118)
    - --export: optional Path to write JSONL export
    - --download-dir: optional Path to download bulk resources
    - --upsert: flag to persist results into PostgreSQL
    - --database-url: override database connection string
    - --verbose: enable debug logging
    
    Returns:
        argparse.ArgumentParser: Parser configured with the CLI options described above.
    """
    parser = argparse.ArgumentParser(description="Crawl bulkdata.govinfo.gov resources")
    parser.add_argument("--collection", required=True, help="GovInfo collection code (e.g., BILLS, BILLSTATUS)")
    parser.add_argument("--congress", help="Optional congress filter (e.g., 118)")
    parser.add_argument("--export", type=Path, help="Optional JSONL export path")
    parser.add_argument("--download-dir", type=Path, help="Directory to download bulk resources")
    parser.add_argument("--upsert", action="store_true", help="Persist results into PostgreSQL")
    parser.add_argument(
        "--database-url",
        help="Override database connection string (defaults to FEDERAL_INGEST_DATABASE_URL or db_config)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: list[str] | None = None) -> None:
    """
    Entrypoint for the GovInfo bulk ingestion CLI.
    
    Parses CLI arguments, configures logging, streams GovInfo bulk resources for the requested collection and optional congress, optionally downloads each resource to a specified directory, and then exports/upserts the collected records according to the provided options.
    
    Parameters:
        argv (list[str] | None): Command-line arguments to parse. If `None`, the parser reads arguments from the process's argv.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    with GovInfoBulkClient() as client:
        records_iter = client.iter_resources(collection=args.collection, congress=args.congress)
        records: List[NormalizedRecord] = list(records_iter)

    if args.download_dir:
        for record in records:
            url = record["data"].get("download_url")
            if url:
                download_resource(url, args.download_dir)

    handle_records(
        records,
        export_path=args.export,
        upsert=args.upsert,
        database_url=args.database_url,
    )


if __name__ == "__main__":
    main()