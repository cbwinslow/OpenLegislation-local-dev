"""Helpers for working with the govinfo.gov bulk data service."""

from __future__ import annotations

import logging
from typing import Iterator, Mapping, Optional

from .base import NormalizedRecord, Resource, build_retrying_session

LOGGER = logging.getLogger(__name__)

BULK_ROOT = "https://www.govinfo.gov/bulkdata"
INDEX_SUFFIX = "index.json"


class GovinfoBulkClient:
    def __init__(self) -> None:
        self.session = build_retrying_session()

    def iter_collection(
        self,
        collection: str,
        *,
        congress: Optional[str] = None,
        doc_class: Optional[str] = None,
    ) -> Iterator[NormalizedRecord]:
        """Yield records for the specified bulk collection."""

        url = build_index_url(collection, congress=congress, doc_class=doc_class)
        LOGGER.debug("Fetching %s", url)
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        payload = response.json()
        packages = payload.get("packages") or payload.get("records") or []
        for package in packages:
            record = normalise_package(collection, package)
            if record:
                yield record


def build_index_url(collection: str, *, congress: Optional[str], doc_class: Optional[str]) -> str:
    parts = [BULK_ROOT, collection]
    if congress:
        parts.append(str(congress))
    if doc_class:
        parts.append(doc_class)
    return "/".join(parts + [INDEX_SUFFIX])


def normalise_package(collection: str, package: Mapping[str, Any]) -> Optional[NormalizedRecord]:
    package_id = package.get("packageId") or package.get("package_id") or package.get("title")
    if not package_id:
        LOGGER.debug("Skipping govinfo bulk package without identifier: %s", package)
        return None

    title = package.get("title") or package_id
    summary = package.get("summary")
    document_date = package.get("dateIssued") or package.get("date")
    download = package.get("download") or package.get("link")
    if isinstance(download, Mapping):
        download_url = download.get("zip") or download.get("pdf") or next(iter(download.values()), None)
    else:
        download_url = download

    resources = []
    if download_url:
        filename = f"{package_id}.zip"
        resources.append(Resource(url=str(download_url), filename=filename, media_type="application/zip"))

    return NormalizedRecord(
        source="govinfo.bulk",
        collection=collection,
        external_id=str(package_id),
        title=title,
        summary=summary,
        document_date=document_date,
        data=package,
        resources=tuple(resources),
    )

