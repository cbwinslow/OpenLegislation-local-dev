"""Command line interface for interacting with the Congress.gov API."""

from __future__ import annotations

import argparse
import json

from ..clients.congress_api_client import CongressGovClient
from ..common import upsert_to_postgres, write_json_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Congress.gov ingestion utilities")
    parser.add_argument("resource", help="Resource type (e.g., bills, members, committees)")
    parser.add_argument("--limit", type=int, default=20, help="Number of records per page")
    parser.add_argument("--offset", type=int, default=0, help="Pagination offset")
    parser.add_argument(
        "--filters",
        type=json.loads,
        default="{}",
        help="JSON object of additional query parameters",
    )
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
    client = CongressGovClient()
    payload = client.list_resources(args.resource, limit=args.limit, offset=args.offset, **args.filters)
    normalized = client.normalize_items(args.resource, payload)

    if args.output_dir:
        write_json_records(normalized, args.output_dir, prefix=f"congress_{args.resource}")

    if args.upsert:
        if not args.table:
            raise SystemExit("--table is required when --upsert is set")
        upsert_to_postgres(args.table, normalized, args.conflict_columns)

    if not args.output_dir and not args.upsert:
        print(json.dumps(normalized, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
