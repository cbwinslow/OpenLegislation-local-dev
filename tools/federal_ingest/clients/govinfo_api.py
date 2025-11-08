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
        """
        Iterate packages from a GovInfo collection, yielding normalized records or raw package objects.
        
        Parameters:
            collection (str): GovInfo collection identifier to list packages from.
            page_size (int): Number of packages to request per page.
            normalized (bool): If `True`, yield `NormalizedRecord` objects produced from each package; if `False`, yield the original `GovInfoPackage`.
        
        Returns:
            Iterator[NormalizedRecord | GovInfoPackage]: `NormalizedRecord` if `normalized` is True, otherwise `GovInfoPackage`.
        """
        packages: Iterable[GovInfoPackage] = super().list_packages(collection=collection, page_size=page_size)
        for package in packages:
            yield govinfo_package_to_record(package) if normalized else package

    def iter_downloads(
        self,
        package_id: str,
        *,
        normalized: bool = True,
    ) -> Iterator[NormalizedRecord | GovInfoDownload]:
        """
        Yield downloads for a GovInfo package, optionally converted to normalized records.
        
        Parameters:
            package_id (str): GovInfo package identifier whose downloads will be listed.
            normalized (bool): If `True`, yield `NormalizedRecord` objects produced from each download;
                if `False`, yield the original `GovInfoDownload` objects.
        
        Returns:
            Iterator[NormalizedRecord | GovInfoDownload]: An iterator that yields normalized records when
            `normalized` is `True`, otherwise raw `GovInfoDownload` instances.
        """
        downloads: Iterable[GovInfoDownload] = super().list_downloads(package_id)
        for download in downloads:
            yield govinfo_download_to_record(download) if normalized else download


__all__ = ["GovInfoApiIngestClient"]