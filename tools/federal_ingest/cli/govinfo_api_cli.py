"""CLI for GovInfo REST API ingestion operations."""

from __future__ import annotations

import argparse
import json

from ..clients.govinfo_api_client import GovInfoAPIClient
from ..common import upsert_to_postgres, write_json_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GovInfo API ingestion helper")
    parser.add_argument("collection", help="GovInfo collection identifier (e.g., BILLS, FR)")
    parser.add_argument("--offset", type=int, default=0, help="Pagination offset")
    parser.add_argument("--page-size", type=int, default=100, help="Page size for API results")
    parser.add_argument(
        "--filters",
        type=json.loads,
        default="{}",
        help="JSON object of additional query parameters",
    )
    parser.add_argument("--package-id", help="Fetch a single package instead of listing")
    parser.add_argument("--output-dir", help="Directory to write normalized JSON output")
    parser.add_argument("--upsert", action="store_true", help="Upsert results into PostgreSQL")
    parser.add_argument("--table", help="Target table for PostgreSQL upsert")
    parser.add_argument(
        "--conflict-columns",
        type=lambda s: [c.strip() for c in s.split(",") if c.strip()],
        default=["record_id"],
        help="Comma-separated list of conflict columns for upsert",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = GovInfoAPIClient()

    if args.package_id:
        payload = client.get_package(args.package_id)
        normalized = [client.normalize_package_detail(payload)]
    else:
        payload = client.list_packages(
            args.collection,
            offset=args.offset,
            page_size=args.page_size,
            **args.filters,
        )
        normalized = client.normalize_packages(args.collection, payload)

    if args.output_dir:
        prefix = f"govinfo_api_{args.collection.lower()}"
        write_json_records(normalized, args.output_dir, prefix=prefix)

    if args.upsert:
        if not args.table:
            raise SystemExit("--table is required when --upsert is set")
        upsert_to_postgres(args.table, normalized, args.conflict_columns)

    if not args.output_dir and not args.upsert:
        print(json.dumps(normalized, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
