#!/usr/bin/env python3
"""Coordinated bulk data downloader for Congress.gov and GovInfo XML feeds.

The goal of this module is to provide a single entry point that can pull raw XML
records from the Library of Congress and GovInfo bulk data endpoints and persist
them locally.  The resulting XML can then be processed by the existing Java based
parsers and DAO layer to populate the relational schema defined by the Flyway
migrations.

The script is intentionally defensive: it throttles requests, records progress on
stdout, and can optionally assemble every downloaded XML document into a single
``aggregate.xml`` file for downstream tooling that prefers a consolidated data
set.  Because the official APIs gate access behind API keys and rate limits the
keys are expected to be supplied via environment variables or command-line
arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import logging
import xml.etree.ElementTree as ET

import requests

from govinfo_ingest import (
    DEFAULT_PAGE_SIZE as GOVINFO_DEFAULT_PAGE_SIZE,
    GovInfoClient,
    download_bulk as download_govinfo_bulk,
)

DEFAULT_CONGRESS_API_BASE = "https://api.congress.gov/v3"
DEFAULT_GOVINFO_API_BASE = "https://api.govinfo.gov"

CONGRESS_API_KEY_ENV = "CONGRESS_GOV_API_KEY"
GOVINFO_API_KEY_ENV = "GOVINFO_API_KEY"

REQUEST_TIMEOUT = 30
REQUEST_RETRY_SLEEP = 2.0
MAX_RETRIES = 5

logger = logging.getLogger(__name__)


@dataclass
class DownloadedDocument:
    source: str
    identifier: str
    file_path: Path


@dataclass
class IngestionTask:
    source: str
    description: str
    parameters: Dict[str, Any]

    def to_json(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "description": self.description,
            "parameters": self.parameters,
        }


class HttpClient:
    """Thin wrapper around :mod:`requests` with retry/backoff support."""

    def __init__(self, base_url: str, default_params: Optional[Dict[str, str]] = None, user_agent: str = "OpenLegislationIngest/1.0") -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.default_params = default_params or {}

    def request(self, method: str, path: str, *, params: Optional[Dict[str, str]] = None) -> requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/') }"
        merged_params = {**self.default_params, **(params or {})}
        for attempt in range(1, MAX_RETRIES + 1):
            response = self.session.request(method, url, params=merged_params, timeout=REQUEST_TIMEOUT)
            if response.status_code >= 500:
                logger.warning("%s %s returned %s. retrying (%s/%s)", method, url, response.status_code, attempt, MAX_RETRIES)
                time.sleep(REQUEST_RETRY_SLEEP * attempt)
                continue
            if response.status_code >= 400:
                response.raise_for_status()
            return response
        raise RuntimeError(f"Failed to retrieve {url} after {MAX_RETRIES} attempts")

    def get(self, path: str, *, params: Optional[Dict[str, str]] = None) -> requests.Response:
        return self.request("GET", path, params=params)


class CongressGovDownloader:
    """Interact with the Congress.gov v3 API to download bill XML payloads."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_CONGRESS_API_BASE,
        *,
        default_page_size: int = 250,
        throttle_seconds: float = 0.0,
    ) -> None:
        if not api_key:
            raise ValueError("Congress.gov API key must be provided")
        self.client = HttpClient(base_url, default_params={"api_key": api_key})
        self.default_page_size = default_page_size
        self.throttle_seconds = throttle_seconds

    def fetch_bill_page(self, congress: int, page: int, page_size: Optional[int] = None) -> Dict[str, Any]:
        params = {"format": "json", "page": page, "pageSize": page_size or self.default_page_size}
        response = self.client.get(f"bill/{congress}", params=params)
        return response.json()

    def iter_bill_pages(
        self,
        congress: int,
        *,
        page_size: Optional[int] = None,
        start_page: int = 1,
        end_page: Optional[int] = None,
        throttle_seconds: Optional[float] = None,
    ) -> Iterable[Tuple[int, List[Dict[str, Any]]]]:
        page = start_page
        throttle = self.throttle_seconds if throttle_seconds is None else throttle_seconds
        while True:
            payload = self.fetch_bill_page(congress, page, page_size)
            bills = payload.get("bills") or payload.get("results") or []
            if not bills:
                break
            yield page, bills
            pagination = payload.get("pagination", {})
            if end_page and page >= end_page:
                break
            if page >= pagination.get("pages", page):
                break
            page += 1
            if throttle:
                time.sleep(throttle)

    def plan_bill_page_ranges(
        self,
        congress: int,
        *,
        page_size: Optional[int] = None,
        chunk_size: int = 10,
    ) -> Tuple[int, List[Tuple[int, int]]]:
        page_size = page_size or self.default_page_size
        payload = self.fetch_bill_page(congress, 1, page_size)
        pagination = payload.get("pagination", {})
        bills = payload.get("bills") or payload.get("results") or []
        total_pages = int(pagination.get("pages") or (1 if bills else 0))
        ranges: List[Tuple[int, int]] = []
        page = 1
        while page <= total_pages:
            end_page = min(page + chunk_size - 1, total_pages)
            ranges.append((page, end_page))
            page = end_page + 1
        return total_pages, ranges

    def download_bill_xml(self, congress: int, bill_type: str, bill_number: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        response = self.client.get(f"bill/{congress}/{bill_type}/{bill_number}", params={"format": "xml"})
        destination.write_bytes(response.content)
        return destination

    def download_page_range(
        self,
        congress: int,
        output_dir: Path,
        *,
        page_size: Optional[int] = None,
        start_page: int = 1,
        end_page: Optional[int] = None,
        throttle_seconds: Optional[float] = None,
    ) -> List[DownloadedDocument]:
        documents: List[DownloadedDocument] = []
        for _, bills in self.iter_bill_pages(
            congress,
            page_size=page_size,
            start_page=start_page,
            end_page=end_page,
            throttle_seconds=throttle_seconds,
        ):
            for bill in bills:
                bill_type = (bill.get("type") or bill.get("billType") or "").lower()
                bill_number = str(bill.get("number") or bill.get("billNumber") or "").lower()
                if not bill_type or not bill_number:
                    logger.warning("Skipping bill entry missing type or number: %s", bill)
                    continue
                identifier = f"{congress}-{bill_type}{bill_number}"
                destination = output_dir / "congress_gov" / str(congress) / bill_type / f"{identifier}.xml"
                logger.debug("Downloading %s", identifier)
                self.download_bill_xml(congress, bill_type, bill_number, destination)
                documents.append(DownloadedDocument(source="congress.gov", identifier=identifier, file_path=destination))
        return documents

    def download_bulk(
        self,
        congresses: Sequence[int],
        output_dir: Path,
        *,
        page_size: Optional[int] = None,
        start_page: int = 1,
        end_page: Optional[int] = None,
        throttle_seconds: Optional[float] = None,
    ) -> List[DownloadedDocument]:
        documents: List[DownloadedDocument] = []
        for congress in congresses:
            logger.info(
                "Fetching bill index for congress %s (pages %s-%s)",
                congress,
                start_page,
                end_page or "end",
            )
            documents.extend(
                self.download_page_range(
                    congress,
                    output_dir,
                    page_size=page_size,
                    start_page=start_page,
                    end_page=end_page,
                    throttle_seconds=throttle_seconds,
                )
            )
        return documents


class GovInfoDownloader:
    """Interact with the GovInfo API to download XML packages and bulk dumps."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_GOVINFO_API_BASE,
        *,
        default_page_size: int = GOVINFO_DEFAULT_PAGE_SIZE,
        throttle_seconds: float = 0.0,
    ) -> None:
        if not api_key:
            raise ValueError("GovInfo API key must be provided")
        self.client = GovInfoClient(api_key, base_url=base_url)
        self.default_page_size = default_page_size
        self.throttle_seconds = throttle_seconds

    def _build_filters(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        congress: Optional[str] = None,
    ) -> Dict[str, str]:
        filters: Dict[str, str] = {}
        if start_date:
            filters["startDate"] = start_date
        if end_date:
            filters["endDate"] = end_date
        if congress:
            filters["congress"] = congress
        return filters

    def iter_collection_pages(
        self,
        collection: str,
        *,
        page_size: Optional[int] = None,
        start_page: int = 1,
        end_page: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        congress: Optional[str] = None,
        throttle_seconds: Optional[float] = None,
    ) -> Iterable[Tuple[int, List[Dict[str, Any]]]]:
        page = start_page
        throttle = self.throttle_seconds if throttle_seconds is None else throttle_seconds
        filters = self._build_filters(start_date=start_date, end_date=end_date, congress=congress)
        while True:
            payload = self.client.fetch_collection_page(
                collection,
                page=page,
                page_size=page_size or self.default_page_size,
                filters=filters or None,
            )
            results = payload.get("results", [])
            if not results:
                break
            yield page, results
            pagination = payload.get("pagination", {})
            if end_page and page >= end_page:
                break
            if page >= pagination.get("pages", page):
                break
            page += 1
            if throttle:
                time.sleep(throttle)

    def plan_collection_page_ranges(
        self,
        collection: str,
        *,
        page_size: Optional[int] = None,
        chunk_size: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        congress: Optional[str] = None,
    ) -> Tuple[int, List[Tuple[int, int]]]:
        filters = self._build_filters(start_date=start_date, end_date=end_date, congress=congress)
        payload = self.client.fetch_collection_page(
            collection,
            page=1,
            page_size=page_size or self.default_page_size,
            filters=filters or None,
        )
        pagination = payload.get("pagination", {})
        results = payload.get("results") or []
        total_pages = int(pagination.get("pages") or (1 if results else 0))
        ranges: List[Tuple[int, int]] = []
        page = 1
        while page <= total_pages:
            end_page = min(page + chunk_size - 1, total_pages)
            ranges.append((page, end_page))
            page = end_page + 1
        return total_pages, ranges

    def download_package_zip(self, package_id: str, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_package(package_id, destination)
        return destination

    def download_collection_range(
        self,
        collection: str,
        output_dir: Path,
        *,
        page_size: Optional[int] = None,
        start_page: int = 1,
        end_page: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        congress: Optional[str] = None,
        throttle_seconds: Optional[float] = None,
    ) -> List[DownloadedDocument]:
        documents: List[DownloadedDocument] = []
        for _, packages in self.iter_collection_pages(
            collection,
            page_size=page_size,
            start_page=start_page,
            end_page=end_page,
            start_date=start_date,
            end_date=end_date,
            congress=congress,
            throttle_seconds=throttle_seconds,
        ):
            for package in packages:
                package_id = package.get("packageId") or package.get("package_id")
                if not package_id:
                    logger.warning("Skipping package without id: %s", package)
                    continue
                destination = output_dir / "govinfo" / collection.lower() / f"{package_id}.zip"
                logger.debug("Downloading GovInfo package %s", package_id)
                self.download_package_zip(package_id, destination)
                documents.append(DownloadedDocument(source="govinfo", identifier=package_id, file_path=destination))
        return documents

    def download_bulk_archives(
        self,
        collection: str,
        output_dir: Path,
        *,
        bulk_year: Optional[int] = None,
    ) -> List[DownloadedDocument]:
        documents: List[DownloadedDocument] = []
        logger.info("Downloading GovInfo bulkdata for %s (%s)", collection, bulk_year or "all")
        for file_path in download_govinfo_bulk(collection, bulk_year, output_dir / "govinfo" / collection.lower() / "bulk"):
            documents.append(DownloadedDocument(source="govinfo-bulk", identifier=file_path.stem, file_path=file_path))
        return documents

    def download_bulk(
        self,
        collections: Sequence[str],
        output_dir: Path,
        *,
        page_size: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        congress: Optional[str] = None,
        start_page: int = 1,
        end_page: Optional[int] = None,
        throttle_seconds: Optional[float] = None,
        bulk_year: Optional[int] = None,
    ) -> List[DownloadedDocument]:
        documents: List[DownloadedDocument] = []
        for collection in collections:
            logger.info(
                "Enumerating GovInfo collection %s (pages %s-%s)",
                collection,
                start_page,
                end_page or "end",
            )
            documents.extend(
                self.download_collection_range(
                    collection,
                    output_dir,
                    page_size=page_size,
                    start_page=start_page,
                    end_page=end_page,
                    start_date=start_date,
                    end_date=end_date,
                    congress=congress,
                    throttle_seconds=throttle_seconds,
                )
            )
            if bulk_year is not None:
                documents.extend(self.download_bulk_archives(collection, output_dir, bulk_year=bulk_year))
        return documents


def aggregate_documents(documents: Sequence[DownloadedDocument], output_path: Path) -> None:
    """Combine individual XML documents into a single aggregate XML file."""

    root = ET.Element("bulkDataAggregate")
    for doc in documents:
        if doc.file_path.suffix.lower() != ".xml":
            logger.debug("Skipping non-XML document during aggregation: %s", doc.file_path)
            continue
        try:
            content = doc.file_path.read_bytes()
            fragment_root = ET.fromstring(content)
        except Exception as exc:  # noqa: BLE001 - broad catch to continue aggregation
            logger.error("Failed to aggregate %s: %s", doc.file_path, exc)
            continue
        container = ET.SubElement(root, "document", source=doc.source, identifier=doc.identifier)
        container.append(fragment_root)
    tree = ET.ElementTree(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    logger.info("Aggregate XML written to %s", output_path)


def build_congress_tasks(
    downloader: CongressGovDownloader,
    congresses: Sequence[int],
    *,
    page_size: int,
    chunk_pages: int,
    throttle_seconds: float,
) -> List[IngestionTask]:
    tasks: List[IngestionTask] = []
    for congress in congresses:
        _, ranges = downloader.plan_bill_page_ranges(
            congress, page_size=page_size, chunk_size=chunk_pages
        )
        for start_page, end_page in ranges:
            tasks.append(
                IngestionTask(
                    source="congress.gov",
                    description=f"Congress {congress} pages {start_page}-{end_page}",
                    parameters={
                        "congress": congress,
                        "page_size": page_size,
                        "start_page": start_page,
                        "end_page": end_page,
                        "throttle_seconds": throttle_seconds,
                    },
                )
            )
    return tasks


def build_govinfo_tasks(
    downloader: GovInfoDownloader,
    collections: Sequence[str],
    *,
    page_size: int,
    chunk_pages: int,
    throttle_seconds: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    congress: Optional[str] = None,
    bulk_year: Optional[int] = None,
) -> List[IngestionTask]:
    tasks: List[IngestionTask] = []
    for collection in collections:
        _, ranges = downloader.plan_collection_page_ranges(
            collection,
            page_size=page_size,
            chunk_size=chunk_pages,
            start_date=start_date,
            end_date=end_date,
            congress=congress,
        )
        for start_page, end_page in ranges:
            tasks.append(
                IngestionTask(
                    source="govinfo.api",
                    description=f"GovInfo {collection} pages {start_page}-{end_page}",
                    parameters={
                        "collection": collection,
                        "page_size": page_size,
                        "start_page": start_page,
                        "end_page": end_page,
                        "start_date": start_date,
                        "end_date": end_date,
                        "congress": congress,
                        "throttle_seconds": throttle_seconds,
                    },
                )
            )
        if bulk_year is not None:
            tasks.append(
                IngestionTask(
                    source="govinfo.bulk",
                    description=f"GovInfo {collection} bulk year {bulk_year}",
                    parameters={
                        "collection": collection,
                        "bulk_year": bulk_year,
                    },
                )
            )
    return tasks


def write_plan(plan_path: Path, tasks: Sequence[IngestionTask]) -> None:
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "task_count": len(tasks),
        "tasks": [task.to_json() for task in tasks],
    }
    plan_path.write_text(json.dumps(payload, indent=2))
    logger.info("Wrote ingestion plan with %s tasks to %s", len(tasks), plan_path)


def load_plan(plan_path: Path) -> List[IngestionTask]:
    payload = json.loads(plan_path.read_text())
    tasks: List[IngestionTask] = []
    for task in payload.get("tasks", []):
        tasks.append(
            IngestionTask(
                source=task["source"],
                description=task.get("description", ""),
                parameters=task.get("parameters", {}),
            )
        )
    return tasks


def execute_tasks(
    tasks: Sequence[IngestionTask],
    congress_downloader: CongressGovDownloader,
    govinfo_downloader: GovInfoDownloader,
    output_dir: Path,
) -> List[DownloadedDocument]:
    documents: List[DownloadedDocument] = []
    for task in tasks:
        logger.info("Executing task: %s", task.description or task.source)
        if task.source == "congress.gov":
            documents.extend(
                congress_downloader.download_page_range(
                    task.parameters["congress"],
                    output_dir,
                    page_size=task.parameters.get("page_size"),
                    start_page=task.parameters.get("start_page", 1),
                    end_page=task.parameters.get("end_page"),
                    throttle_seconds=task.parameters.get("throttle_seconds"),
                )
            )
        elif task.source == "govinfo.api":
            documents.extend(
                govinfo_downloader.download_collection_range(
                    task.parameters["collection"],
                    output_dir,
                    page_size=task.parameters.get("page_size"),
                    start_page=task.parameters.get("start_page", 1),
                    end_page=task.parameters.get("end_page"),
                    start_date=task.parameters.get("start_date"),
                    end_date=task.parameters.get("end_date"),
                    congress=task.parameters.get("congress"),
                    throttle_seconds=task.parameters.get("throttle_seconds"),
                )
            )
        elif task.source == "govinfo.bulk":
            documents.extend(
                govinfo_downloader.download_bulk_archives(
                    task.parameters["collection"],
                    output_dir,
                    bulk_year=task.parameters.get("bulk_year"),
                )
            )
        else:
            raise ValueError(f"Unknown task source: {task.source}")
    return documents


def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download XML datasets from Congress.gov and GovInfo bulk APIs")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory to store downloaded XML files")
    parser.add_argument("--congress", nargs="*", type=int, default=[118], help="Congress numbers to download")
    parser.add_argument("--govinfo-collections", nargs="*", default=["BILLS"], help="GovInfo collection identifiers (e.g. BILLS, BILLSTATUS)")
    parser.add_argument("--govinfo-from", default=None, help="ISO start date filter (YYYY-MM-DD) for GovInfo packages")
    parser.add_argument("--govinfo-to", default=None, help="ISO end date filter (YYYY-MM-DD) for GovInfo packages")
    parser.add_argument("--govinfo-congress", default=None, help="Filter GovInfo packages by congress number")
    parser.add_argument("--govinfo-bulk-year", type=int, default=None, help="Download bulkdata XML for the specified year in addition to API packages")
    parser.add_argument("--congress-page-size", type=int, default=250, help="Number of bills to request per Congress.gov API page")
    parser.add_argument("--congress-start-page", type=int, default=1, help="Starting page for direct Congress.gov downloads")
    parser.add_argument("--congress-end-page", type=int, default=None, help="Final page (inclusive) for direct Congress.gov downloads")
    parser.add_argument("--congress-chunk-pages", type=int, default=25, help="Number of Congress.gov pages per queued task when generating a plan")
    parser.add_argument("--congress-throttle", type=float, default=0.0, help="Seconds to sleep between Congress.gov page fetches")
    parser.add_argument("--govinfo-page-size", type=int, default=GOVINFO_DEFAULT_PAGE_SIZE, help="Number of packages to request per GovInfo API page")
    parser.add_argument("--govinfo-start-page", type=int, default=1, help="Starting page for direct GovInfo downloads")
    parser.add_argument("--govinfo-end-page", type=int, default=None, help="Final page (inclusive) for direct GovInfo downloads")
    parser.add_argument("--govinfo-chunk-pages", type=int, default=25, help="Number of GovInfo pages per queued task when generating a plan")
    parser.add_argument("--govinfo-throttle", type=float, default=0.0, help="Seconds to sleep between GovInfo page fetches")
    parser.add_argument("--aggregate", action="store_true", help="Combine downloaded XML into aggregate.xml")
    parser.add_argument("--aggregate-path", type=Path, default=None, help="Custom path for aggregate XML output")
    parser.add_argument("--congress-api-key", default=os.getenv(CONGRESS_API_KEY_ENV), help="Congress.gov API key (default: env {CONGRESS_GOV_API_KEY})")
    parser.add_argument("--govinfo-api-key", default=os.getenv(GOVINFO_API_KEY_ENV), help="GovInfo API key (default: env {GOVINFO_API_KEY})")
    parser.add_argument("--plan-output", type=Path, help="Write a queued ingestion plan to this JSON file and exit")
    parser.add_argument("--plan-input", type=Path, help="Execute ingestion tasks from the provided JSON plan")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    configure_logging(args.verbose)

    if not args.congress_api_key:
        logger.error("Congress.gov API key is required (set %s or pass --congress-api-key)", CONGRESS_API_KEY_ENV)
        sys.exit(1)
    if not args.govinfo_api_key:
        logger.error("GovInfo API key is required (set %s or pass --govinfo-api-key)", GOVINFO_API_KEY_ENV)
        sys.exit(1)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    congress_downloader = CongressGovDownloader(
        args.congress_api_key,
        default_page_size=args.congress_page_size,
        throttle_seconds=args.congress_throttle,
    )
    govinfo_downloader = GovInfoDownloader(
        args.govinfo_api_key,
        default_page_size=args.govinfo_page_size,
        throttle_seconds=args.govinfo_throttle,
    )

    plan_tasks: Optional[List[IngestionTask]] = None
    if args.plan_output:
        plan_tasks = []
        plan_tasks.extend(
            build_congress_tasks(
                congress_downloader,
                args.congress,
                page_size=args.congress_page_size,
                chunk_pages=args.congress_chunk_pages,
                throttle_seconds=args.congress_throttle,
            )
        )
        plan_tasks.extend(
            build_govinfo_tasks(
                govinfo_downloader,
                args.govinfo_collections,
                page_size=args.govinfo_page_size,
                chunk_pages=args.govinfo_chunk_pages,
                throttle_seconds=args.govinfo_throttle,
                start_date=args.govinfo_from,
                end_date=args.govinfo_to,
                congress=args.govinfo_congress,
                bulk_year=args.govinfo_bulk_year,
            )
        )
        write_plan(args.plan_output, plan_tasks)
        if not args.plan_input:
            return

    documents: List[DownloadedDocument] = []
    if args.plan_input:
        tasks = load_plan(args.plan_input)
        documents.extend(execute_tasks(tasks, congress_downloader, govinfo_downloader, output_dir))
    else:
        documents.extend(
            congress_downloader.download_bulk(
                args.congress,
                output_dir,
                page_size=args.congress_page_size,
                start_page=args.congress_start_page,
                end_page=args.congress_end_page,
                throttle_seconds=args.congress_throttle,
            )
        )
        documents.extend(
            govinfo_downloader.download_bulk(
                args.govinfo_collections,
                output_dir,
                page_size=args.govinfo_page_size,
                start_date=args.govinfo_from,
                end_date=args.govinfo_to,
                congress=args.govinfo_congress,
                start_page=args.govinfo_start_page,
                end_page=args.govinfo_end_page,
                throttle_seconds=args.govinfo_throttle,
                bulk_year=args.govinfo_bulk_year,
            )
        )

    if args.aggregate:
        aggregate_path = args.aggregate_path or output_dir / "aggregate.xml"
        aggregate_documents(documents, aggregate_path)


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
