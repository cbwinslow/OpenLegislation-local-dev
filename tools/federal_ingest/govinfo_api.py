"""Client and helpers for the govinfo.gov REST API."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterator, Mapping, Optional

from .base import NormalizedRecord, Resource, build_retrying_session, safe_get

LOGGER = logging.getLogger(__name__)

API_ROOT = "https://api.govinfo.gov"
DEFAULT_PAGE_SIZE = 100


class GovinfoAPIClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GOVINFO_API_KEY")
        if not self.api_key:
            raise ValueError("A GOVINFO_API_KEY environment variable or --api-key argument is required")
        self.session = build_retrying_session()

    def iter_collection(
        self,
        collection: str,
        *,
        limit: Optional[int] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        **filters: Any,
    ) -> Iterator[NormalizedRecord]:
        page_size = min(page_size, DEFAULT_PAGE_SIZE)
        params: Dict[str, Any] = {
            "api_key": self.api_key,
            "pageSize": page_size,
        }
        params.update(filters)

        url = f"{API_ROOT}/collections/{collection}/documents"
        count = 0
        while url:
            LOGGER.debug("Fetching %s", url)
            response = self.session.get(url, params=params if params else None, timeout=60)
            response.raise_for_status()
            payload = response.json()
            for document in payload.get("documents", []):
                if limit is not None and count >= limit:
                    return
                record = normalise_document(collection, document)
                if record is None:
                    continue
                yield record
                count += 1
            if limit is not None and count >= limit:
                return
            next_url = payload.get("nextPage")
            if not next_url:
                break
            url = next_url
            params = None


def normalise_document(collection: str, document: Mapping[str, Any]) -> Optional[NormalizedRecord]:
    package_id = document.get("packageId") or document.get("documentId")
    if not package_id:
        LOGGER.debug("Skipping govinfo document without packageId: %s", document)
        return None

    title = document.get("title")
    summary = document.get("summary") or safe_get(document, "congressionalRecord", "title")
    document_date = document.get("dateIssued") or document.get("date")

    resources = []
    pdf_url = document.get("pdfLink") or safe_get(document, "download", "pdf")
    if pdf_url:
        resources.append(Resource(url=pdf_url, filename=f"{package_id}.pdf", media_type="application/pdf"))
    xml_url = document.get("modsLink") or safe_get(document, "download", "mods")
    if xml_url:
        resources.append(Resource(url=xml_url, filename=f"{package_id}.xml", media_type="application/xml"))

    return NormalizedRecord(
        source="govinfo.api",
        collection=collection,
        external_id=str(package_id),
        title=title,
        summary=summary,
        document_date=document_date,
        data=document,
        resources=tuple(resources),
    )

