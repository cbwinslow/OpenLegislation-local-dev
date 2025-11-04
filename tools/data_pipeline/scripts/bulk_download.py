"""Utility script to download bulk data archives to local storage."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Iterable

import requests

from ..clients import GovInfoClient, OpenLegislationClient
from ..models import GovInfoDownload, GovInfoPackage, OpenLegislationBill
from .config import get_settings
from .utils import chunked

logger = logging.getLogger(__name__)


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Downloading %s -> %s", url, destination)
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)


def download_govinfo(collection: str, output_dir: Path, batch_size: int) -> None:
    settings = get_settings()
    with GovInfoClient(api_key=settings.govinfo_api_key) as client:
        packages: Iterable[GovInfoPackage] = client.list_packages(collection=collection)
        for batch in chunked(packages, batch_size):
            for package in batch:
                downloads: Iterable[GovInfoDownload] = client.list_downloads(package.package_id)
                for download in downloads:
                    filename = f"{package.package_id}.{download.format.lower()}"
                    destination = output_dir / "govinfo" / filename
                    download_file(download.url, destination)


def download_openlegislation(session: str, output_dir: Path, batch_size: int) -> None:
    settings = get_settings()
    with OpenLegislationClient(api_key=settings.ny_openleg_api_key) as client:
        bills: Iterable[OpenLegislationBill] = client.list_bills(session=session)
        for batch in chunked(bills, batch_size):
            for bill in batch:
                if bill.raw_payload and isinstance(bill.raw_payload, dict):
                    destination = output_dir / "openlegislation" / f"{bill.print_no}.json"
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(json.dumps(bill.raw_payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download bulk legislative data for offline ingestion")
    parser.add_argument("source", choices=["govinfo", "openlegislation"])
    parser.add_argument("--collection", help="GovInfo collection code (e.g., BILLS)")
    parser.add_argument("--session", help="OpenLegislation session year")
    parser.add_argument("--output", type=Path, default=Path("bulkdata"), help="Directory to store downloads")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.verbose)

    if args.source == "govinfo":
        if not args.collection:
            raise ValueError("--collection is required for GovInfo downloads")
        download_govinfo(args.collection, args.output, args.batch_size)
    elif args.source == "openlegislation":
        if not args.session:
            raise ValueError("--session is required for OpenLegislation downloads")
        download_openlegislation(args.session, args.output, args.batch_size)
    else:
        parser.error(f"Unsupported source {args.source}")


if __name__ == "__main__":
    main()

