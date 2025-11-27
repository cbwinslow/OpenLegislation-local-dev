"""CLI for ingesting member data from supported API endpoints with pagination support."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

from tools.config.settings import settings
from tools.ingestion.core.api_ingestion_cli import APIIngestionConfig, PaginatedAPIIngestor


DEFAULT_STATE = Path("tools/ingestion/state/members_state.json")
DEFAULT_OUTPUT = Path("tools/ingestion/output/members.ndjson")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("MEMBERS_API_BASE", "https://api.congress.gov/v3"))
    parser.add_argument("--endpoint", default=os.getenv("MEMBERS_API_ENDPOINT", "member"))
    parser.add_argument("--api-key", default=os.getenv("MEMBERS_API_KEY", settings.congress_api_key))
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--rate-limit", type=float, default=5.0)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--records-key", default="results")
    parser.add_argument("--id-field", default="bioguideId")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--extra", action="append", default=[], help="Extra query params in key=value form")
    return parser


def parse_extra_params(extra_args: list[str]) -> dict:
    params = {}
    for arg in extra_args:
        if "=" not in arg:
            continue
        key, value = arg.split("=", 1)
        params[key] = value
    return params


def main(argv: Optional[list[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    extra_params = parse_extra_params(args.extra)
    config = APIIngestionConfig(
        name="members",
        base_url=args.base_url,
        endpoint=args.endpoint,
        api_key=args.api_key,
        page_size=args.page_size,
        records_key=args.records_key,
        id_field=args.id_field,
        extra_params=extra_params,
    )

    ingestor = PaginatedAPIIngestor(
        config=config,
        state_path=args.state,
        output_path=args.output,
        rate_limit_per_second=args.rate_limit,
        max_workers=args.workers,
    )
    ingestor.ingest(max_pages=args.max_pages)


if __name__ == "__main__":
    main()
