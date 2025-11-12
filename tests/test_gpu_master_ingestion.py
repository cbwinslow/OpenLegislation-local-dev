
import pathlib
import sys
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
    return "asyncio"


@pytest.mark.anyio
async def test_congress_ingestion_deduplication_and_completion_criteria(monkeypatch):
    adapter = InMemoryAdapter()

    async def fake_fetch(self, congress_num, api_key=None):
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
    adapter = InMemoryAdapter()
    members: List[Dict[str, Any]] = [
        {
            "bioguide_id": f"A{i:03d}",
            "first_name": "Test",
            "last_name": f"Member{i}",
            "full_name": f"Test Member {i}",
        }
        for i in range(25)
    ]

    async def fake_fetch(self, congress=None, api_key=None):
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
