#!/usr/bin/env python3
"""GovInfo bulk ingestion entry point.

This script discovers packages via the GovInfo REST API, downloads the
associated files (USLM XML, MODS metadata, PDF, etc.), and writes them to a
local staging directory. Metadata manifests are persisted alongside the
downloaded files so they can be handed off to downstream parsers.

It does **not** perform database inserts directly; use
`tools/govinfo_bill_ingestion.py` or similar processors to load staged files
into PostgreSQL once parsing is implemented.

Usage:
    python tools/bulk_ingest_govinfo.py \
        --api-key $GOVINFO_KEY \
        --collections BILLS BILLSTATUS \
        --congress 118 \
        --start-date 2023-01-01T00:00:00Z \
        --end-date 2023-12-31T23:59:59Z \
        --output-dir staging/federal
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from requests.exceptions import HTTPError

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from govinfo_api import GovInfoAPIClient, GovInfoError

logger = logging.getLogger(__name__)

MANIFEST_NAME = "manifest.json"
DEFAULT_COLLECTIONS = ["BILLS"]


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download GovInfo bulk packages")
    parser.add_argument("--api-key", dest="api_key", default=os.getenv("GOVINFO_API_KEY"))
    parser.add_argument("--collections", nargs="+", default=DEFAULT_COLLECTIONS)
    parser.add_argument("--congress", type=int, required=False, help="Congress number (e.g., 118)")
    parser.add_argument("--start-date", dest="start_date", required=False, help="ISO8601 start date")
    parser.add_argument("--end-date", dest="end_date", required=False, help="ISO8601 end date")
    parser.add_argument("--output-dir", default="staging/govinfo")
    parser.add_argument("--limit", type=int, help="Stop after downloading N packages per collection")
    parser.add_argument("--force", action="store_true", help="Re-download files even if they exist")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(list(argv) if argv is not None else None)


def ensure_api_key(api_key: Optional[str]) -> str:
    if not api_key:
        raise SystemExit("GovInfo API key must be provided via --api-key or GOVINFO_API_KEY env var")
    return api_key


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    temp.replace(path)


def download_package_files(
    client: GovInfoAPIClient,
    package_id: str,
    output_dir: Path,
    *,
    force: bool = False,
) -> List[Path]:
    metadata = client.get_package(package_id)
    download = metadata.get("download") or {}
    saved: List[Path] = []

    if isinstance(download, dict):
        items = download.items()
    else:
        items = []

    for label, url in items:
        if not isinstance(url, str) or not url:
            continue
        extension = Path(url).suffix or ""
        target = output_dir / f"{package_id}.{label}{extension}"
        if target.exists() and not force:
            logger.debug("Skipping existing file %s", target)
            saved.append(target)
            continue
        logger.info("Downloading %s (%s)", package_id, label)
        with target.open("wb") as fh:
            for chunk in client.download_file(url):
                fh.write(chunk)
        saved.append(target)

    summary_path = output_dir / f"{package_id}.summary.json"
    try:
        summary_payload = client.get_package_summary(package_id)
        write_json(summary_path, summary_payload)
        saved.append(summary_path)
    except GovInfoError as exc:
        logger.warning("No summary available for %s: %s", package_id, exc)
    except HTTPError as exc:  # requests raises HTTPError for 404
        logger.warning("Summary request failed for %s: %s", package_id, exc)

    metadata_path = output_dir / f"{package_id}.metadata.json"
    write_json(metadata_path, metadata)
    saved.append(metadata_path)

    return saved


def update_manifest(manifest_path: Path, package_id: str, files: List[Path]) -> None:
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[package_id] = [str(path.name) for path in files]
    write_json(manifest_path, manifest)


def ingest_collection(
    client: GovInfoAPIClient,
    collection: str,
    params: argparse.Namespace,
    output_dir: Path,
) -> None:
    logger.info("Discovering %s packages...", collection)
    count = 0
    manifest_path = output_dir / MANIFEST_NAME
    ensure_dir(output_dir)

    for package in client.iter_packages(
        collection,
        congress=params.congress,
        start_date=params.start_date,
        end_date=params.end_date,
    ):
        if params.limit and count >= params.limit:
            logger.info("Collection %s limit (%d) reached", collection, params.limit)
            break
        try:
            files = download_package_files(
                client,
                package.package_id,
                output_dir,
                force=params.force,
            )
            update_manifest(manifest_path, package.package_id, files)
            count += 1
        except (GovInfoError, HTTPError) as exc:
            logger.error("Failed to download package %s: %s", package.package_id, exc)
    logger.info("Downloaded %d package(s) for %s", count, collection)


def main(argv: Optional[Iterable[str]] = None) -> int:
    params = parse_args(argv)
    configure_logging(params.verbose)
    api_key = ensure_api_key(params.api_key)
    client = GovInfoAPIClient(api_key=api_key)

    output_dir = Path(params.output_dir)
    ensure_dir(output_dir)

    for collection in params.collections:
        collection_dir = output_dir / collection.lower()
        ingest_collection(client, collection, params, collection_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
