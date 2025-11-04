from pathlib import Path
import sys
from typing import Iterable, Iterator, List, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

from tools.govdata_ingest.extract_govdata import ingest_to_postgres, main


class StreamingIterable:
    def __init__(self, data: Sequence[Mapping[str, object]]):
        self._data = data
        self.iteration_started = False

    def __iter__(self) -> Iterator[Mapping[str, object]]:
        self.iteration_started = True
        yield from self._data


class FakeCursor:
    def __init__(self) -> None:
        self.executed: List[tuple] = []
        self.closed = False

    def execute(self, query: str, params):
        if self.closed:
            raise RuntimeError("cursor already closed")
        self.executed.append((query, params))

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_obj = FakeCursor()
        self.commit_calls = 0
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commit_calls += 1

    def close(self):
        self.closed = True


@pytest.fixture
def large_dataset() -> Iterable[Mapping[str, object]]:
    def iterator():
        for i in range(2500):
            yield {"id": f"dataset-{i}", "index": i}

    return iterator()


def test_ingest_to_postgres_commits_periodically(large_dataset):
    connection = FakeConnection()
    processed = ingest_to_postgres(large_dataset, connection, commit_every=200)

    assert processed == 2500
    assert connection.commit_calls == 13  # 12 chunks of 200, plus final flush
    assert len(connection.cursor_obj.executed) == 2500
    assert connection.cursor_obj.closed


def test_main_passes_streaming_iterable():
    streaming = StreamingIterable([{"id": "dataset-1"}, {"id": "dataset-2"}])

    class DummyExtractor:
        def __init__(self, *_args, **_kwargs):
            pass

        def run(self):
            return streaming

    captured = {}

    def fake_ingest(datasets, connection, *, commit_every):
        captured["type"] = type(datasets)
        captured["commit_every"] = commit_every
        # exhaust iterator to mimic ingestion
        for _ in datasets:
            pass
        return 2

    connection = FakeConnection()

    result = main(
        [],
        extractor_factory=lambda _args: DummyExtractor(),
        connection_factory=lambda _args: connection,
        ingest_fn=fake_ingest,
    )

    assert result == 2
    assert captured["type"] is StreamingIterable
    assert captured["commit_every"] == 500  # default value
    assert streaming.iteration_started
    assert connection.closed
