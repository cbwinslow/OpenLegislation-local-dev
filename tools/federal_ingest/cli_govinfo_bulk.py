"""Command line interface for the govinfo.gov bulk data index."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import List

from .base import PostgresUpserter, RecordExporter, ResourceDownloader
from .govinfo_bulk import GovinfoBulkClient

LOGGER = logging.getLogger("federal_ingest.govinfo_bulk")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enumerate and ingest govinfo bulk data")
    parser.add_argument("collection", help="Bulk collection identifier, e.g. 'BILLSTATUS'")
    parser.add_argument("--congress", help="Optional congress/session component for the bulk path")
    parser.add_argument("--doc-class", dest="doc_class", help="Optional document class for the bulk path")
    parser.add_argument("--output-dir", type=Path, help="Directory for JSON exports")
    parser.add_argument("--download-dir", type=Path, help="Directory for ZIP downloads")
    parser.add_argument("--table", help="PostgreSQL table for upserts (omit to skip DB writes)")
    parser.add_argument("--db-url", dest="db_url", help="Database connection string (defaults to FEDERAL_DB_URL/DB_URL)")
    parser.add_argument("--log-level", default="INFO", help="Python logging level")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print summary without side effects")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(name)s: %(message)s")

    client = GovinfoBulkClient()
    records = list(client.iter_collection(args.collection, congress=args.congress, doc_class=args.doc_class))
    LOGGER.info("Indexed %s packages from govinfo bulk data", len(records))

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

