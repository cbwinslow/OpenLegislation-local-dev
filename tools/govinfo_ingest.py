#!/usr/bin/env python3
"""Flexible GovInfo ingestion script covering API and bulkdata endpoints."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Iterator, List, Optional

import requests

DEFAULT_API_BASE = "https://api.govinfo.gov"
DEFAULT_BULKDATA_BASE = "https://www.govinfo.gov/bulkdata"
GOVINFO_API_KEY_ENV = "GOVINFO_API_KEY"
DEFAULT_PAGE_SIZE = 100

logger = logging.getLogger(__name__)


class GovInfoClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_API_BASE) -> None:
        if not api_key:
            raise ValueError("A GovInfo API key is required. Register at https://api.govinfo.gov/docs/")
        self.session = requests.Session()
        self.session.params.update({"api_key": api_key})
        self.base_url = base_url.rstrip("/")

    def get(self, path: str, *, params: Optional[Dict[str, str]] = None) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=params or {}, timeout=30)
        response.raise_for_status()
        return response

    def fetch_collection_page(
        self,
        collection: str,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        params = {"pageSize": page_size, "page": page, **(filters or {})}
        return self.get(f"collections/{collection}", params=params).json()

    def iter_collection(
        self,
        collection: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        start_page: int = 1,
        filters: Optional[Dict[str, str]] = None,
    ) -> Iterator[Dict[str, str]]:
        page = start_page
        while True:
            payload = self.fetch_collection_page(
                collection, page=page, page_size=page_size, filters=filters
            )
            results = payload.get("results", [])
            if not results:
                break
            for result in results:
                yield result
            pagination = payload.get("pagination", {})
            if page >= pagination.get("pages", page):
                break
            page += 1

    def download_package(self, package_id: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        response = self.get(f"packages/{package_id}", params={"download": "zip"})
        destination.write_bytes(response.content)
        return destination


def download_bulk(collection: str, year: Optional[int], output_dir: Path) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"/{year}" if year else ""
    url = f"{DEFAULT_BULKDATA_BASE}/{collection}{suffix}"
    logger.info("Downloading bulk archive listing from %s", url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    files: List[Path] = []
    for line in response.text.splitlines():
        line = line.strip()
        if not line or not line.endswith(".xml"):
            continue
        file_url = f"{url}/{line}"
        target = output_dir / line
        logger.info("Fetching %s", file_url)
        content = requests.get(file_url, timeout=60)
        content.raise_for_status()
        target.write_bytes(content.content)
        files.append(target)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("collection", help="GovInfo collection identifier (e.g. BILLS, STATUTE, FR)")
    parser.add_argument("--package", help="Specific package id to download")
    parser.add_argument("--start-date", help="Filter API results by start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Filter API results by end date (YYYY-MM-DD)")
    parser.add_argument("--congress", help="Filter API results by congress number")
    parser.add_argument("--bulk-year", type=int, help="Download bulkdata XML for a specific year")
    parser.add_argument("--output", type=Path, default=Path("downloads/govinfo"), help="Destination directory")
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="Number of records to request per API page when enumerating collections",
    )
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s %(message)s")

    api_key = os.getenv(GOVINFO_API_KEY_ENV, "")
    if args.package or any([args.start_date, args.end_date, args.congress]):
        client = GovInfoClient(api_key, base_url=args.api_base)
        if args.package:
            destination = args.output / f"{args.package}.zip"
            logger.info("Downloading GovInfo package %s", args.package)
            client.download_package(args.package, destination)
        else:
            filters = {k.replace("_", ""): v for k, v in {
                "start_date": args.start_date,
                "end_date": args.end_date,
                "congress": args.congress,
            }.items() if v}
            for record in client.iter_collection(
                args.collection, page_size=args.page_size, filters=filters or None
            ):
                package_id = record.get("packageId")
                if not package_id:
                    continue
                destination = args.output / f"{package_id}.zip"
                logger.info("Downloading package %s", package_id)
                client.download_package(package_id, destination)
    if args.bulk_year or (not args.package and not any([args.start_date, args.end_date, args.congress])):
        logger.info("Falling back to bulkdata downloads")
        download_bulk(args.collection, args.bulk_year, args.output)


if __name__ == "__main__":  # pragma: no cover
    main()
