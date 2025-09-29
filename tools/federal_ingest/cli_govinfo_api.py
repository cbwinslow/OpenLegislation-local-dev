"""Command line interface for the govinfo.gov REST API."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List

from .base import PostgresUpserter, RecordExporter, ResourceDownloader
from .govinfo_api import GovinfoAPIClient

LOGGER = logging.getLogger("federal_ingest.govinfo_api")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest data from api.govinfo.gov")
    parser.add_argument("collection", help="GovInfo collection identifier, e.g. 'BILLSTATUS'")
    parser.add_argument("--api-key", dest="api_key", help="Override the GOVINFO_API_KEY environment variable")
    parser.add_argument("--limit", type=int, help="Maximum number of records to fetch")
    parser.add_argument("--page-size", dest="page_size", type=int, default=100, help="Number of items per page (<=100)")
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Additional filter parameter supported by api.govinfo.gov",
    )
    parser.add_argument("--output-dir", type=Path, help="Directory for JSON exports")
    parser.add_argument("--download-dir", type=Path, help="Directory for asset downloads")
    parser.add_argument("--table", help="PostgreSQL table for upserts (omit to skip DB writes)")
    parser.add_argument("--db-url", dest="db_url", help="Database connection string (defaults to FEDERAL_DB_URL/DB_URL)")
    parser.add_argument("--log-level", default="INFO", help="Python logging level")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print summary without side effects")
    return parser


def parse_filters(pairs: Iterable[str]) -> Dict[str, str]:
    params: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"Filters must be KEY=VALUE pairs: {pair}")
        key, value = pair.split("=", 1)
        params[key] = value
    return params


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(name)s: %(message)s")

    client = GovinfoAPIClient(api_key=args.api_key)
    filters = parse_filters(args.filter)
    records = list(client.iter_collection(args.collection, limit=args.limit, page_size=args.page_size, **filters))
    LOGGER.info("Fetched %s records from api.govinfo.gov", len(records))

    if args.dry_run:
        print(json.dumps([record.to_row() for record in records], indent=2))
        return 0

    if args.output_dir:
        exporter = RecordExporter(args.output_dir)
        exporter.write_records(records)

    if args.download_dir:
        downloader = ResourceDownloader()
        for record in records:
            downloader.download(record.resources, args.download_dir)

    if args.table:
        upserter = PostgresUpserter(dsn=args.db_url, table=args.table)
        upserter.upsert(records)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

