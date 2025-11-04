"""Client factories for federal ingestion."""

from .congress import CongressGovIngestClient
from .govinfo_api import GovInfoApiIngestClient
from .govinfo_bulk import GovInfoBulkClient

__all__ = [
    "CongressGovIngestClient",
    "GovInfoApiIngestClient",
    "GovInfoBulkClient",
]
