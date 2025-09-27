#!/usr/bin/env python3
"""Bill vote ingestion script.

Consumes JSON payloads describing vote metadata and roll entries, persisting them
into `bill_amendment_vote_info` and `bill_amendment_vote_roll` tables.
"""
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

from govinfo.models import GovInfoVoteRecord, GovInfoVoteRollEntry
from govinfo.persistence import persist_vote_record
from db.session import session_scope

logger = logging.getLogger(__name__)


class BillVoteIngestor(BaseIngestionProcess):
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
            json_dir = [getattr(settings, "vote_json_dir", "staging/govinfo/votes")]
        elif isinstance(json_dir, str):  # type: ignore[arg-type]
            json_dir = [json_dir]
        self.json_dirs = [Path(p) for p in json_dir]  # type: ignore[assignment]
        self.patterns = list(patterns or ["VOTES-*.json"])
        self.extra_files = [Path(f) for f in files] if files else []
        self.recursive = recursive

        for directory in self.json_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def get_data_source(self) -> str:
        return "bill_votes"

    def get_target_table(self) -> str:
        return "master.bill_amendment_vote_info"

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
        logger.info("Discovered %d vote files", len(records))
        return records

    def process_record(self, record: Dict[str, str]) -> bool:
        path = Path(record["path"])
        logger.info("Processing vote file %s", path)
        try:
            with session_scope() as session:
                for entry in self._stream_votes(path):
                    vote_record = self._parse_vote(entry)
                    persist_vote_record(session, vote_record)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to ingest vote file %s: %s", path, exc)
            return False

    @staticmethod
    def _parse_vote(data: Dict[str, object]) -> GovInfoVoteRecord:
        vote = GovInfoVoteRecord(
            bill_print_no=str(data.get("billPrintNo")),
            bill_session_year=int(data.get("billSessionYear")),
            bill_amend_version=str(data.get("billAmendVersion", "")),
            vote_date=_parse_datetime(data.get("voteDate")),
            vote_type=str(data.get("voteType", "floor")),
            sequence_no=data.get("sequenceNo"),
            committee_name=data.get("committeeName"),
            committee_chamber=data.get("committeeChamber"),
        )

        for roll in data.get("roll", []):
            vote.roll.append(
                GovInfoVoteRollEntry(
                    session_member_id=int(roll.get("sessionMemberId")),
                    session_year=int(roll.get("sessionYear")),
                    member_short_name=str(roll.get("memberShortName", "")),
                    vote_code=str(roll.get("voteCode", "aye")).lower(),
                )
            )

        return vote

    @staticmethod
    def _stream_votes(path: Path) -> Iterator[Dict[str, object]]:
        with path.open("rb") as fh:
            try:
                for item in ijson.items(fh, "votes.item"):
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
        elif isinstance(payload, dict) and "votes" in payload:
            for item in payload["votes"]:
                yield item


def _parse_datetime(value: Optional[object]) -> datetime:
    if value is None:
        raise ValueError("voteDate is required")
    text = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(text.replace("Z", ""), fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse voteDate '{value}'")


def _stream_votes(path: Path) -> Iterator[Dict[str, object]]:
    with path.open("rb") as fh:
        try:
            for item in ijson.items(fh, "votes.item"):
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
    elif isinstance(payload, dict) and "votes" in payload:
        for item in payload["votes"]:
            yield item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest bill vote JSON payloads")
    parser.add_argument("--json-dir", dest="json_dirs", nargs="*", help="Directories containing vote JSON files")
    parser.add_argument("--pattern", dest="patterns", nargs="*", help="Filename patterns (default VOTES-*.json)")
    parser.add_argument("--file", dest="files", nargs="*", help="Specific JSON files to ingest")
    parser.add_argument("--recursive", action="store_true", help="Recursively search directories")
    parser.add_argument("--reset", action="store_true", help="Reset ingestion tracker before running")
    parser.add_argument("--limit", type=int, help="Limit number of files processed")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    ingestor = BillVoteIngestor(
        json_dir=args.json_dirs,
        patterns=args.patterns,
        files=args.files,
        recursive=args.recursive,
    )
    ingestor.run(resume=not args.reset, reset=args.reset, limit=args.limit)
