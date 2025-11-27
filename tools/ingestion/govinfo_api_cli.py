"""CLI for ingesting GovInfo API resources with incremental pagination support."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

from tools.config.settings import settings
from tools.ingestion.core.api_ingestion_cli import APIIngestionConfig, PaginatedAPIIngestor


DEFAULT_STATE = Path("tools/ingestion/state/govinfo_state.json")
DEFAULT_OUTPUT = Path("tools/ingestion/output/govinfo.ndjson")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("GOVINFO_API_BASE", "https://api.govinfo.gov"))
    parser.add_argument("--endpoint", default=os.getenv("GOVINFO_API_ENDPOINT", "collections/BILLS"))
    parser.add_argument("--api-key", default=os.getenv("GOVINFO_API_KEY", settings.govinfo_api_key))
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--rate-limit", type=float, default=4.0)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--records-key", default="packages")
    parser.add_argument("--id-field", default="packageId")
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
        name="govinfo",
        base_url=args.base_url,
        endpoint=args.endpoint,
        api_key=args.api_key,
        page_size=args.page_size,
        records_key=args.records_key,
        id_field=args.id_field,
        offset_param="offset",
        limit_param="pageSize",
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
