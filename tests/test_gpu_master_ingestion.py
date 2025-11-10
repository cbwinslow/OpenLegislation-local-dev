import asyncio
from typing import List, Dict

from typing import Dict, List
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from tools.ingestion.core.ingestion_engine import (
    IngestionEngine,
    InMemoryAdapter,
    FetchResponse,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():  # pragma: no cover - force asyncio backend
    """
    Select the AnyIO backend to use for asynchronous tests.
    
    Returns:
        backend (str): The name of the AnyIO backend to use; `"asyncio"`.
    """
    return "asyncio"


@pytest.mark.anyio
async def test_congress_ingestion_deduplication_and_completion_criteria(monkeypatch):
    adapter = InMemoryAdapter()

    async def fake_fetch(self, congress_num, api_key=None):
        """
        Provide a fake fetch implementation that returns a single mock bill record for the given congress number.
        
        Parameters:
            congress_num (int): Congress number used to populate the record's `bill_session_year`.
            api_key (str | None): Optional API key (not used).
        
        Returns:
            FetchResponse: A response containing one bill record, `api_calls` set to 1, and `source` set to "test".
        """
        records = [
            {
                "bill_print_no": "HR1",
                "bill_session_year": 118,
                "title": "Test Bill",
                "short_title": "Test",
            }
        ]
        return FetchResponse(records=records, api_calls=1, source="test")

    monkeypatch.setattr(IngestionEngine, "_fetch_congress_bills", fake_fetch)

    async with IngestionEngine(enable_parallel=False, enable_gpu=False, db_adapter=adapter) as engine:
        first = await engine.ingest_congress_data(start_congress=118, end_congress=118)
        assert first.records_processed == 1
        assert first.data_quality_metrics["duplicates_skipped"] == 0
        assert first.data_quality_metrics["completion_criteria"]["mandatory"]["segments_completed"]

        second = await engine.ingest_congress_data(start_congress=118, end_congress=118)
        assert second.records_processed == 0
        assert second.data_quality_metrics["duplicates_skipped"] == 1
        assert second.data_quality_metrics["completion_criteria"]["mandatory"]["segments_completed"]


@pytest.mark.anyio
async def test_members_ingestion_parallel_processing(monkeypatch):
    """
    Validates parallel ingestion of federal members, completion metrics, and duplicate handling on re-run.
    
    Mocks the engine's member fetch to return 25 synthetic members, runs ingest_federal_members with parallel processing and a batch size of 10, and asserts:
    - all members are processed and the mandatory unique_members_processed completion criterion is satisfied,
    - optional chunks_processed equals 3,
    - a subsequent run processes 0 records and reports all 25 members as duplicates_skipped.
    """
    adapter = InMemoryAdapter()
    members: List[Dict[str, str]] = [
        {
            "bioguide_id": f"A{i:03d}",
            "first_name": "Test",
            "last_name": f"Member{i}",
            "full_name": f"Test Member {i}",
        }
        for i in range(25)
    ]

    async def fake_fetch(self, congress=None, api_key=None):
        """
        Return a canned FetchResponse containing the test members list.
        
        Parameters:
            congress (Optional[int]): Ignored; accepted for signature compatibility.
            api_key (Optional[str]): Ignored; accepted for signature compatibility.
        
        Returns:
            FetchResponse: A response with `records` set to the module-level `members` list, `api_calls` set to 2, and `source` set to "test".
        """
        return FetchResponse(records=members, api_calls=2, source="test")

    monkeypatch.setattr(IngestionEngine, "_fetch_federal_members", fake_fetch)

    async with IngestionEngine(enable_parallel=True, enable_gpu=False, batch_size=10, db_adapter=adapter) as engine:
        result = await engine.ingest_federal_members()
        assert result.records_processed == len(members)
        completion = result.data_quality_metrics["completion_criteria"]
        assert completion["mandatory"]["unique_members_processed"]
        assert completion["optional"]["chunks_processed"] == 3

        # Run again to ensure duplicates are detected and skipped
        second = await engine.ingest_federal_members()
        assert second.records_processed == 0
        assert second.data_quality_metrics["duplicates_skipped"] == len(members)


@pytest.mark.anyio
async def test_govinfo_ingestion_duplicate_handling(monkeypatch, caplog):
    adapter = InMemoryAdapter()
    packages = [
        {
            "package_id": "pkg-1",
            "congress": 118,
            "bill_number": "HR1",
            "title": "Package",
            "collection_code": "BILLS",
        },
        {
            "package_id": "pkg-1",
            "congress": 118,
            "bill_number": "HR1",
            "title": "Package",
            "collection_code": "BILLS",
        },
    ]

    async def fake_fetch(self, collection, api_key=None, start_date=None, end_date=None):
        """
        Provide a mocked FetchResponse for govinfo packages using the provided collection and optional date range.
        
        Parameters:
            collection (str): Collection code to include in the response metadata (e.g., "BILLS").
            api_key (str | None): Optional API key (unused by the fake implementation).
            start_date (str | None): Optional start date filter for the fetch (unused by the fake implementation).
            end_date (str | None): Optional end date filter for the fetch (unused by the fake implementation).
        
        Returns:
            FetchResponse: A response containing the predefined `packages` records, `api_calls` set to 3, `source` set to "test", and `metadata` including the provided `collection`.
        """
        return FetchResponse(records=packages, api_calls=3, source="test", metadata={"collection": collection})

    monkeypatch.setattr(IngestionEngine, "_fetch_govinfo_bills", fake_fetch)

    async with IngestionEngine(enable_parallel=False, enable_gpu=False, db_adapter=adapter) as engine:
        caplog.set_level("INFO")
        result = await engine.ingest_govinfo_bills(collection="BILLS")
        assert result.records_processed == 1
        assert result.data_quality_metrics["duplicates_skipped"] == 1
        completion = result.data_quality_metrics["completion_criteria"]
        assert completion["mandatory"]["collection_provided"]
        assert completion["optional"]["time_window_applied"] is False

    duplicate_logs = [record for record in caplog.records if "duplicate" in record.getMessage().lower()]
    assert duplicate_logs, "Expected duplicate handling logs to be emitted"