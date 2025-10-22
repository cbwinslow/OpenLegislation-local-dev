"""Client for GovInfo bulk data downloads (bulkdata.govinfo.gov)."""

from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional

import requests

from tools.settings import settings


class GovInfoBulkClient:
    """Fetches metadata and downloads bulk ZIP archives from GovInfo."""

    DEFAULT_BASE_URL = "https://www.govinfo.gov/bulkdata"

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")

    def list_packages(self, collection: str, year: Optional[str] = None) -> List[Dict[str, str]]:
        """List available packages for a collection (optionally by year)."""

        url_parts = [self.base_url, collection]
        if year:
            url_parts.append(str(year))
        url = "/".join(part.strip("/") for part in url_parts)
        index_url = f"{url}/index.json"
        response = requests.get(index_url, timeout=settings.request_timeout)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("files", [])
        packages: List[Dict[str, str]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            packages.append(
                {
                    "source": "govinfo.bulk",
                    "collection": collection,
                    "record_id": item.get("title"),
                    "title": item.get("title"),
                    "path": item.get("url"),
                    "size": item.get("size"),
                    "lastModified": item.get("lastModified"),
                }
            )
        return packages

    def download_package(self, package_path: str, output_dir: str) -> str:
        """Download a ZIP package to the specified directory."""

        os.makedirs(output_dir, exist_ok=True)
        download_url = package_path
        if not download_url.startswith("http"):
            download_url = f"{self.base_url}/{package_path.lstrip('/')}"
        local_path = os.path.join(output_dir, os.path.basename(download_url))
        with requests.get(download_url, stream=True, timeout=settings.request_timeout) as response:
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        return local_path
