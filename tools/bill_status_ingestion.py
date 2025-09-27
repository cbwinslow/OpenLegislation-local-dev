#!/usr/bin/env python3
"""Bill status/milestone ingestion script."""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

import ijson

from base_ingestion_process import BaseIngestionProcess
from settings import settings

from govinfo.models import GovInfoBillStatusRecord, GovInfoBillMilestone
from govinfo.persistence import persist_bill_status_record
from db.session import session_scope

logger = logging.getLogger(__name__)


class BillStatusIngestor(BaseIngestionProcess):
    def __init__(
        self,
        json_dir: Optional[Iterable[str]] = None,
        patterns: Optional[Iterable[str]] = None,
        files: Optional[Iterable[str]] = None,
        recursive: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if json_dir is None:
            json_dir = [getattr(settings, "bill_status_json_dir", "staging/govinfo/status")]
        elif isinstance(json_dir, str):  # type: ignore[arg-type]
            json_dir = [json_dir]
        self.json_dirs = [Path(p) for p in json_dir]  # type: ignore[assignment]
        self.patterns = list(patterns or ["STATUS-*.json"])
        self.extra_files = [Path(f) for f in files] if files else []
        self.recursive = recursive

        for directory in self.json_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def get_data_source(self) -> str:
        return "bill_status"

    def get_target_table(self) -> str:
        return "master.bill_milestone"

    def get_record_id_column(self) -> List[str]:
        return ["record_id"]

    def discover_records(self) -> List[Dict[str, str]]:
        files: List[Path] = []
        for directory in self.json_dirs:
            for pattern in self.patterns:
                iterator = directory.rglob(pattern) if self.recursive else directory.glob(pattern)
                files.extend(iterator)
        files.extend(self.extra_files)

        records = []
        for path in files:
            if path.is_file():
                records.append({"record_id": str(path), "path": str(path)})
        logger.info("Discovered %d status files", len(records))
        return records

    def process_record(self, record: Dict[str, str]) -> bool:
        path = Path(record["path"])
        logger.info("Processing status file %s", path)
        try:
            with session_scope() as session:
                for entry in self._stream_statuses(path):
                    status_record = self._parse_status(entry)
                    persist_bill_status_record(session, status_record)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to ingest status file %s: %s", path, exc)
            return False

    @staticmethod
    def _parse_status(data: Dict[str, object]) -> GovInfoBillStatusRecord:
        record = GovInfoBillStatusRecord(
            bill_print_no=str(data.get("billPrintNo")),
            bill_session_year=int(data.get("billSessionYear")),
        )
        for milestone in data.get("milestones", []):
            record.milestones.append(
                GovInfoBillMilestone(
                    status=str(milestone.get("status", "")),
                    rank=int(milestone.get("rank", 0)),
                    action_sequence_no=int(milestone.get("actionSequenceNo", 0)),
                    date=_parse_date(milestone.get("date")),
                    committee_name=milestone.get("committeeName"),
                    committee_chamber=milestone.get("committeeChamber"),
                    cal_no=milestone.get("calendarNo"),
                )
            )
        return record

    @staticmethod
    def _stream_statuses(path: Path) -> Iterator[Dict[str, object]]:
        with path.open("rb") as fh:
            try:
                for item in ijson.items(fh, "statuses.item"):
                    yield item
                return
            except ijson.common.JSONError:
                pass

        with path.open("rb") as fh:
            try:
                for item in ijson.items(fh, "item"):
                    yield item
                return
            except ijson.common.JSONError:
                pass

        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            for item in payload:
                yield item
        elif isinstance(payload, dict) and "statuses" in payload:
            for item in payload["statuses"]:
                yield item


def _parse_date(value: Optional[object]) -> datetime:
    if value is None:
        raise ValueError("Milestone date is required")
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse milestone date '{value}'")


@staticmethod
def _stream_statuses(path: Path) -> Iterator[Dict[str, object]]:
    with path.open("rb") as fh:
        try:
            for item in ijson.items(fh, "statuses.item"):
                yield item
            return
        except ijson.common.JSONError:
            pass

    with path.open("rb") as fh:
        try:
            for item in ijson.items(fh, "item"):
                yield item
            return
        except ijson.common.JSONError:
            pass

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        for item in payload:
            yield item
    elif isinstance(payload, dict) and "statuses" in payload:
        for item in payload["statuses"]:
            yield item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest bill status/milestone JSON payloads")
    parser.add_argument("--json-dir", dest="json_dirs", nargs="*", help="Directories containing status JSON files")
    parser.add_argument("--pattern", dest="patterns", nargs="*", help="Filename patterns (default STATUS-*.json)")
    parser.add_argument("--file", dest="files", nargs="*", help="Specific JSON files to ingest")
    parser.add_argument("--recursive", action="store_true", help="Recursively search directories")
    parser.add_argument("--reset", action="store_true", help="Reset ingestion tracker before running")
    parser.add_argument("--limit", type=int, help="Limit number of files processed")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    ingestor = BillStatusIngestor(
        json_dir=args.json_dirs,
        patterns=args.patterns,
        files=args.files,
        recursive=args.recursive,
    )
    ingestor.run(resume=not args.reset, reset=args.reset, limit=args.limit)
