#!/usr/bin/env python3
"""Generic member data ingestion script.

Reads JSON payloads describing person/member/session-member records and persists
them using the shared SQLAlchemy models.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional

import ijson

from base_ingestion_process import BaseIngestionProcess
from settings import settings

from govinfo.models import GovInfoMemberRecord, GovInfoMemberSession
from govinfo.persistence import persist_member_record
from db.session import session_scope

logger = logging.getLogger(__name__)


class MemberDataIngestor(BaseIngestionProcess):
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
            json_dir = [getattr(settings, "member_json_dir", "staging/members")]
        elif isinstance(json_dir, str):  # type: ignore[arg-type]
            json_dir = [json_dir]
        self.json_dirs = [Path(p) for p in json_dir]  # type: ignore[assignment]
        self.patterns = list(patterns or ["MEMBERS-*.json"])
        self.extra_files = [Path(f) for f in files] if files else []
        self.recursive = recursive

        for directory in self.json_dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def get_data_source(self) -> str:
        return "member_data"

    def get_target_table(self) -> str:
        return "public.session_member"

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
        logger.info("Discovered %d member files", len(records))
        return records

    def process_record(self, record: Dict[str, str]) -> bool:
        path = Path(record["path"])
        logger.info("Processing member file %s", path)
        try:
            with session_scope() as session:
                for entry in self._stream_entries(path):
                    record = self._parse_member(entry)
                    persist_member_record(session, record)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to ingest member file %s: %s", path, exc)
            return False

    @staticmethod
    def _parse_member(data: Dict[str, object]) -> GovInfoMemberRecord:
        person = data.get("person", {})
        member = data.get("member", {})
        sessions = data.get("sessions", [])

        record = GovInfoMemberRecord(
            person_id=int(person.get("id")),
            full_name=str(person.get("fullName", "")),
            first_name=person.get("firstName"),
            last_name=person.get("lastName"),
            email=person.get("email"),
            member_id=int(member.get("id", person.get("id"))),
            chamber=str(member.get("chamber", "senate")),
            incumbent=bool(member.get("incumbent", True)),
        )

        for session_entry in sessions:
            record.sessions.append(
                GovInfoMemberSession(
                    session_year=int(session_entry.get("sessionYear")),
                    lbdc_short_name=str(session_entry.get("lbdcShortName", "")),
                    district_code=session_entry.get("districtCode"),
                    alternate=bool(session_entry.get("alternate", False)),
                )
            )
        return record

    @staticmethod
    def _stream_entries(path: Path) -> Iterator[Dict[str, object]]:
        # Try structured payload: {"members": [...]}
        with path.open("rb") as fh:
            try:
                for item in ijson.items(fh, "members.item"):
                    yield item
                return
            except ijson.common.JSONError:
                pass

        # Fallback to top-level array
        with path.open("rb") as fh:
            try:
                for item in ijson.items(fh, "item"):
                    yield item
                return
            except ijson.common.JSONError:
                pass

        # Fallback to standard json load for small files
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            for item in payload:
                yield item
        elif isinstance(payload, dict) and "members" in payload:
            for item in payload["members"]:
                yield item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest member JSON payloads")
    parser.add_argument("--json-dir", dest="json_dirs", nargs="*", help="Directories containing member JSON files")
    parser.add_argument("--pattern", dest="patterns", nargs="*", help="Filename patterns (default MEMBERS-*.json)")
    parser.add_argument("--file", dest="files", nargs="*", help="Specific JSON files to ingest")
    parser.add_argument("--recursive", action="store_true", help="Recursively search directories")
    parser.add_argument("--reset", action="store_true", help="Reset ingestion tracker before running")
    parser.add_argument("--limit", type=int, help="Limit number of files processed")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    ingestor = MemberDataIngestor(
        json_dir=args.json_dirs,
        patterns=args.patterns,
        files=args.files,
        recursive=args.recursive,
    )
    ingestor.run(resume=not args.reset, reset=args.reset, limit=args.limit)
