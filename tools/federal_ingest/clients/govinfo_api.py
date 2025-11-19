"""GovInfo REST API ingestion client with normalization helpers."""
from __future__ import annotations

from typing import Iterable, Iterator

from tools.data_pipeline.clients.govinfo import GovInfoClient as _BaseGovInfoClient
from tools.data_pipeline.models import GovInfoDownload, GovInfoPackage

from ..normalization import (
    govinfo_download_to_record,
    govinfo_package_to_record,
    NormalizedRecord,
)


class GovInfoApiIngestClient(_BaseGovInfoClient):
    """High-level client exposing normalized package and download streams."""

    def iter_packages(
        self,
        *,
        collection: str,
        page_size: int = 100,
        normalized: bool = True,
    ) -> Iterator[NormalizedRecord | GovInfoPackage]:
        packages: Iterable[GovInfoPackage] = super().list_packages(collection=collection, page_size=page_size)
        for package in packages:
            yield govinfo_package_to_record(package) if normalized else package

    def iter_downloads(
        self,
        package_id: str,
        *,
        normalized: bool = True,
    ) -> Iterator[NormalizedRecord | GovInfoDownload]:
        downloads: Iterable[GovInfoDownload] = super().list_downloads(package_id)
        for download in downloads:
            yield govinfo_download_to_record(download) if normalized else download


__all__ = ["GovInfoApiIngestClient"]
