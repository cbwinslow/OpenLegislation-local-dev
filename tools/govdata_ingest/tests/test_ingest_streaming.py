import itertools
import math
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.govdata_ingest import extract_govdata


class FakeConnection:
    def __init__(self):
        self.commits = 0
        self.closed = False

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


@pytest.fixture
def connection_factory():
    holder = {}

    def factory():
        conn = FakeConnection()
        holder["conn"] = conn
        return conn

    factory.holder = holder
    return factory


def test_ingest_streams_large_dataset(connection_factory):
    total_records = 10_000
    batch_size = 128
    commit_every = 256

    peak_batch = 0
    inserted = 0

    def dataset():
        for idx in range(total_records):
            yield {"id": f"dataset-{idx}", "value": idx}

    def insert_batch(_conn, batch):
        nonlocal peak_batch, inserted
        peak_batch = max(peak_batch, len(batch))
        inserted += len(batch)
        assert len(batch) <= batch_size

    total = extract_govdata.ingest_to_postgres(
        dataset(),
        connection_factory=connection_factory,
        batch_size=batch_size,
        commit_every=commit_every,
        insert_batch=insert_batch,
    )

    conn = connection_factory.holder["conn"]
    assert conn.closed is True
    assert inserted == total_records
    assert total == total_records
    expected_commits = math.ceil(total_records / commit_every)
    assert conn.commits == expected_commits
    assert peak_batch <= batch_size


def test_ingest_accepts_chunked_sequences(connection_factory):
    batches = [
        [{"id": "dataset-1"}, {"id": "dataset-2"}],
        [{"id": "dataset-3"}],
    ]

    seen = []

    def insert_batch(_conn, batch):
        seen.append(tuple(record["id"] for record in batch))

    total = extract_govdata.ingest_to_postgres(
        iter(batches),
        connection_factory=connection_factory,
        batch_size=10,
        commit_every=10,
        insert_batch=insert_batch,
    )

    assert total == 3
    assert seen == [("dataset-1", "dataset-2"), ("dataset-3",)]


def test_main_passes_generator_into_ingest(monkeypatch):
    extracted = itertools.count()

    class DummyExtractor:
        def run(self, limit=None):
            for _ in range(3):
                yield {"id": f"dataset-{next(extracted)}"}

    dummy = DummyExtractor()

    monkeypatch.setattr(extract_govdata, "GovDataExtractor", lambda: dummy)

    ingested_batches = []

    def fake_ingest(records, **kwargs):
        assert not isinstance(records, list)
        iterator = iter(records)
        first = next(iterator)
        ingested_batches.append(first["id"])
        ingested_batches.extend(record["id"] for record in iterator)
        return len(ingested_batches)

    monkeypatch.setattr(extract_govdata, "ingest_to_postgres", fake_ingest)

    result = extract_govdata.main([])

    assert result == 3
    assert ingested_batches == ["dataset-0", "dataset-1", "dataset-2"]
