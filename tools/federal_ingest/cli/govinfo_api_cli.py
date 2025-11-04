"""Command line interface for GovInfo REST API ingestion."""
from __future__ import annotations

import argparse
from pathlib import Path

from ..clients import GovInfoApiIngestClient
from ..cli.common import configure_logging, handle_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest data from api.govinfo.gov")
    parser.add_argument("command", choices=["packages", "downloads"], help="Resource to fetch")
    parser.add_argument("--collection", help="GovInfo collection code for package listing")
    parser.add_argument("--package-id", help="Package identifier for downloads")
    parser.add_argument("--page-size", type=int, default=100, help="Number of items to request per page")
    parser.add_argument("--export", type=Path, help="Optional JSONL export path")
    parser.add_argument("--upsert", action="store_true", help="Persist results into PostgreSQL")
    parser.add_argument(
        "--database-url",
        help="Override database connection string (defaults to FEDERAL_INGEST_DATABASE_URL or db_config)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    with GovInfoApiIngestClient() as client:
        if args.command == "packages":
            if not args.collection:
                parser.error("--collection is required for package listing")
            records = client.iter_packages(collection=args.collection, page_size=args.page_size)
        else:
            if not args.package_id:
                parser.error("--package-id is required for downloads")
            records = client.iter_downloads(args.package_id)

        handle_records(
            records,
            export_path=args.export,
            upsert=args.upsert,
            database_url=args.database_url,
        )


if __name__ == "__main__":
    main()
