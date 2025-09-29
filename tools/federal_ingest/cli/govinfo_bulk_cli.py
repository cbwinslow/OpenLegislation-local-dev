"""CLI for GovInfo bulk data discovery and downloads."""

from __future__ import annotations

import argparse
import json

from ..clients.govinfo_bulk_client import GovInfoBulkClient
from ..common import upsert_to_postgres, write_json_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GovInfo bulk data helper")
    parser.add_argument("collection", help="Collection identifier (e.g., BILLS, STATUTE)")
    parser.add_argument("--year", help="Optional year to scope the collection")
    parser.add_argument("--download-dir", help="Directory to download ZIP archives")
    parser.add_argument("--output-dir", help="Directory to write normalized JSON output")
    parser.add_argument("--upsert", action="store_true", help="Upsert inventory rows into PostgreSQL")
    parser.add_argument("--table", help="Target table for PostgreSQL upsert")
    parser.add_argument(
        "--conflict-columns",
        type=lambda s: [c.strip() for c in s.split(",") if c.strip()],
        default=["record_id"],
        help="Comma-separated list of conflict columns for upsert",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Flag indicating downloads should be performed when download-dir is provided",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = GovInfoBulkClient()
    packages = client.list_packages(args.collection, year=args.year)

    if args.output_dir:
        write_json_records(packages, args.output_dir, prefix=f"govinfo_bulk_{args.collection.lower()}")

    if args.upsert:
        if not args.table:
            raise SystemExit("--table is required when --upsert is set")
        upsert_to_postgres(args.table, packages, args.conflict_columns)

    if args.download and args.download_dir:
        for package in packages:
            path = package.get("path")
            if not path:
                continue
            client.download_package(path, args.download_dir)

    if not args.output_dir and not args.upsert:
        print(json.dumps(packages, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
