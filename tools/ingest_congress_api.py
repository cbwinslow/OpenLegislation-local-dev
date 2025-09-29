#!/usr/bin/env python3
"""Utility for ingesting data from congress.gov and api.congress.gov.

The original repository contained a proof-of-concept script that referenced
mapping helpers before they were defined, mixed configuration and behaviour,
and lacked guard rails for dry-runs and automated testing.  The rewrite below
focuses on the following goals:

* Keep the mapping logic testable in isolation by exposing pure functions.
* Allow the ingestion routine to operate in dry-run mode while emitting the
  exact payload that would be persisted to the SQL migrations.
* Support resumable pagination and deterministic logging so the Java services
  can rely on consistent offsets when ingesting federal data.
* Provide a lightweight validation layer that mirrors the expectations of the
  federal data models introduced elsewhere in the code base.

The script is intentionally conservative – it does not attempt to mutate the
database during unit tests and defaults to reading configuration from the same
environment variables used by the Java ingestion pipeline.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional

import psycopg2
from psycopg2.extras import execute_values
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


LOGGER = logging.getLogger("federal_ingestion")

# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def map_congress_member(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalise a congress.gov member response for ``master.federal_member``."""

    member = payload.get("member", {})
    social_media = {
        "twitter": member.get("twitterAccount"),
        "facebook": member.get("facebookAccount"),
        "youtube": member.get("youtubeAccount"),
    }
    mapped = {
        "bioguide_id": member.get("bioguideId"),
        "full_name": member.get("name"),
        "first_name": member.get("firstName"),
        "last_name": member.get("lastName"),
        "party": member.get("party"),
        "state": member.get("state"),
        "chamber": (member.get("chamber") or "").lower() or None,
        "current_member": bool(member.get("currentMember", False)),
        "terms": json.dumps(member.get("terms", [])),
        "committees": json.dumps(member.get("committees", [])),
        "social_media": json.dumps(social_media),
        "source": "federal",
    }
    return mapped


def map_congress_bill(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalise a congress.gov bill response for ``master.bills``."""

    bill = payload.get("bill", {})
    sponsors = bill.get("sponsors", []) or []
    actions = bill.get("actions", []) or []
    mapped = {
        "print_no": f"{bill.get('type', '')}{bill.get('number', '')}",
        "session_year": payload.get("sessionYear") or payload.get("session_year"),
        "title": bill.get("title"),
        "sponsors": json.dumps([{"name": s.get("name")} for s in sponsors]),
        "actions": json.dumps([{"text": a.get("text")} for a in actions]),
        "federal_congress": payload.get("congress"),
        "source": "federal",
    }
    return mapped


def map_openstates_member(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalise an OpenStates legislator response for ``master.federal_member``."""

    committees = payload.get("committees", []) or []
    roles = payload.get("roles", []) or []
    social_media = {
        "twitter": payload.get("twitter_id"),
        "facebook": payload.get("facebook_id"),
        "website": payload.get("url"),
    }
    mapped = {
        "openstates_id": payload.get("id"),
        "full_name": payload.get("name"),
        "first_name": payload.get("given_name"),
        "last_name": payload.get("family_name"),
        "party": payload.get("party"),
        "state": (payload.get("state") or "").upper() or None,
        "chamber": (payload.get("chamber") or "").lower() or None,
        "current_member": bool(payload.get("active", True)),
        "terms": json.dumps([
            {"state": role.get("state"), "type": role.get("type")}
            for role in roles
            if role.get("type") == "member"
        ]),
        "committees": json.dumps(committees),
        "social_media": json.dumps(social_media),
        "source": "state",
    }
    return mapped


def map_openstates_bill(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalise an OpenStates bill response for ``master.bills``."""

    sponsors = payload.get("sponsors", []) or []
    actions = payload.get("actions", []) or []
    mapped = {
        "bill_id": payload.get("id"),
        "print_no": payload.get("bill_id"),
        "session_year": int(payload.get("session")) if payload.get("session") else None,
        "title": payload.get("title"),
        "sponsors": json.dumps([{"name": s.get("name")} for s in sponsors]),
        "actions": json.dumps([{"text": a.get("description")} for a in actions]),
        "source": "state",
    }
    return mapped


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


API_KEYS = {
    "congress": os.getenv("CONGRESS_API_KEY", "DEMO_KEY"),
    "openstates": os.getenv("OPENSTATES_API_KEY", ""),
}

DB_URL = os.getenv("DB_URL", "postgresql://user:pass@localhost:5432/openleg")

DEFAULT_BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))

LOG_FILE = Path("tools/ingestion_log.json")


@dataclass(frozen=True)
class EndpointConfig:
    path: str
    table: str
    pk_col: str
    mapper: Callable[[Mapping[str, Any]], Dict[str, Any]]
    item_key: str


def build_endpoint_config() -> Dict[str, Dict[str, EndpointConfig]]:
    return {
        "congress": {
            "member": EndpointConfig(
                path="/member",
                table="master.federal_member",
                pk_col="bioguide_id",
                mapper=map_congress_member,
                item_key="members",
            ),
            "bill": EndpointConfig(
                path="/bill",
                table="master.bills",
                pk_col="print_no",
                mapper=map_congress_bill,
                item_key="bills",
            ),
        },
        "openstates": {
            "member": EndpointConfig(
                path="/legislators/",
                table="master.federal_member",
                pk_col="openstates_id",
                mapper=map_openstates_member,
                item_key="results",
            ),
            "bill": EndpointConfig(
                path="/bills/",
                table="master.bills",
                pk_col="bill_id",
                mapper=map_openstates_bill,
                item_key="results",
            ),
        },
    }


ENDPOINTS: Dict[str, Dict[str, EndpointConfig]] = build_endpoint_config()

BASE_URLS = {
    "congress": "https://api.congress.gov/v3",
    "openstates": "https://openstates.org/api/v1",
}


# ---------------------------------------------------------------------------
# Core ingester
# ---------------------------------------------------------------------------


class CongressAPIIngester:
    """Stateful helper that orchestrates pagination, mapping, and persistence."""

    def __init__(
        self,
        source: str,
        endpoint: str,
        params: Mapping[str, Any],
        batch_size: int,
        dry_run: bool = False,
        output_file: Optional[Path] = None,
    ) -> None:
        if source not in ENDPOINTS:
            raise ValueError(f"Unsupported source '{source}'.")
        if endpoint not in ENDPOINTS[source]:
            raise ValueError(f"Unsupported endpoint '{endpoint}' for source '{source}'.")

        self.source = source
        self.endpoint_config = ENDPOINTS[source][endpoint]
        self.params = dict(params)
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.output_file = output_file
        self.base_url = BASE_URLS[source]
        self.session = self._build_session()
        self.api_key = API_KEYS[source]
        self.log_state = self._load_log_state()
        self.metrics: Dict[str, Any] = {
            "start": datetime.now().isoformat(),
            "batches": 0,
            "ingested": 0,
            "errors": 0,
            "total": 0,
        }

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_session() -> requests.Session:
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def _load_log_state(self) -> Dict[str, Any]:
        if LOG_FILE.exists():
            try:
                with LOG_FILE.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                    return data.get("sources", {}).get(self.source, {"offset": 0})
            except json.JSONDecodeError:
                LOGGER.warning("ingestion_log.json is malformed. Starting with a clean state.")
        return {"offset": 0}

    def _persist_log_state(self, offset: int) -> None:
        entry = {
            "run_id": datetime.now().isoformat(),
            "source": self.source,
            "endpoint": self.endpoint_config.path,
            "params": self.params,
            "offset": offset,
            "metrics": {k: v for k, v in self.metrics.items() if k != "start"},
        }

        payload = {"runs": [], "sources": {}}
        if LOG_FILE.exists():
            with LOG_FILE.open("r", encoding="utf-8") as handle:
                try:
                    payload = json.load(handle)
                except json.JSONDecodeError:
                    LOGGER.warning("ingestion_log.json is malformed. Recreating file.")

        payload.setdefault("runs", []).append(entry)
        payload.setdefault("sources", {})[self.source] = {"offset": offset}

        with LOG_FILE.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def _pre_count(self) -> Optional[int]:
        return self._count_records("pre")

    def _post_count(self) -> Optional[int]:
        return self._count_records("post")

    def _count_records(self, label: str) -> Optional[int]:
        if self.dry_run:
            LOGGER.debug("Skipping %s-count in dry-run mode.", label)
            return None

        filters = dict(self.params)
        where_clause_parts = [f"{key} = %({key})s" for key in filters]
        where_clause = f" WHERE {' AND '.join(where_clause_parts)}" if where_clause_parts else ""

        query = f"SELECT COUNT(*) FROM {self.endpoint_config.table}{where_clause}"
        try:
            with psycopg2.connect(DB_URL) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, filters)
                    result = cursor.fetchone()
                    return int(result[0]) if result else 0
        except Exception as exc:  # pragma: no cover - exercised in integration
            LOGGER.error("%s-count failed: %s", label.capitalize(), exc)
            self.metrics["errors"] += 1
            return None

    # ------------------------------------------------------------------
    # Upsert helpers
    # ------------------------------------------------------------------

    def _upsert_batch(self, batch: Iterable[Dict[str, Any]]) -> bool:
        rows = [row for row in batch if row.get(self.endpoint_config.pk_col)]
        if not rows:
            LOGGER.info("No valid rows in batch; skipping")
            return True

        if self.dry_run:
            LOGGER.info("Dry-run: %s rows mapped for %s", len(rows), self.endpoint_config.table)
            if self.output_file:
                self._append_to_output(rows)
            return True

        columns = list(rows[0].keys())
        query = f"INSERT INTO {self.endpoint_config.table} ({', '.join(columns)}) VALUES %s "
        query += f"ON CONFLICT ({self.endpoint_config.pk_col}) DO UPDATE SET "
        query += ", ".join(f"{col}=EXCLUDED.{col}" for col in columns if col != self.endpoint_config.pk_col)

        try:
            with psycopg2.connect(DB_URL) as conn:
                with conn.cursor() as cursor:
                    execute_values(cursor, query, [tuple(row[col] for col in columns) for row in rows])
                conn.commit()
            return True
        except Exception as exc:  # pragma: no cover - exercised in integration
            LOGGER.error("Database upsert failed: %s", exc)
            self.metrics["errors"] += len(rows)
            return False

    def _append_to_output(self, rows: Iterable[Dict[str, Any]]) -> None:
        if not self.output_file:
            return
        records: List[Dict[str, Any]] = []
        if self.output_file.exists():
            with self.output_file.open("r", encoding="utf-8") as handle:
                try:
                    records = json.load(handle)
                except json.JSONDecodeError:
                    LOGGER.warning("Output file is malformed. Overwriting with fresh payload.")
        records.extend(rows)
        with self.output_file.open("w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(self) -> None:
        endpoint_url = f"{self.base_url}{self.endpoint_config.path}"
        params = {
            **self.params,
            "api_key": self.api_key,
            "format": "json",
            "limit": self.batch_size,
            "offset": self.log_state.get("offset", 0),
        }

        pre_count = self._pre_count()
        if pre_count is not None:
            LOGGER.info("Existing records: %s", pre_count)

        while True:
            LOGGER.info("Fetching %s batch at offset %s", self.source, params["offset"])
            response = self.session.get(endpoint_url, params=params, timeout=60)
            if response.status_code != 200:
                self._handle_error(response)
                break

            payload = response.json()
            items = payload.get(self.endpoint_config.item_key, [])
            if not items:
                LOGGER.info("No more items returned; ingestion complete")
                break

            mapped_rows = [self.endpoint_config.mapper(item) for item in items]
            success = self._upsert_batch(mapped_rows)
            self.metrics["total"] += len(items)
            self.metrics["ingested"] += len(items) if success else 0
            self.metrics["batches"] += 1

            params["offset"] += self.batch_size
            self.log_state["offset"] = params["offset"]
            self._persist_log_state(params["offset"])

            if self.dry_run:
                LOGGER.info("Dry-run requested; stopping after first batch")
                break

        post_count = self._post_count()
        if post_count is not None and pre_count is not None:
            LOGGER.info("Records delta: %s", post_count - pre_count)
        self._persist_log_state(params["offset"])

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _handle_error(self, response: Response) -> None:
        LOGGER.error(
            "API responded with %s: %s",
            response.status_code,
            response.text[:200],
        )
        self.metrics["errors"] += 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest data from congress.gov APIs")
    parser.add_argument("--source", choices=sorted(ENDPOINTS.keys()), default="congress")
    parser.add_argument("--endpoint", choices=["member", "bill"], default="member")
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--dry-run", action="store_true", help="Do not write to the database")
    parser.add_argument("--output", type=Path, help="Optional JSON output for dry-run batches")

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    congress_parser = subparsers.add_parser("congress", help="Options for congress.gov")
    congress_parser.add_argument("--congress", type=int, required=True, help="Congress number (e.g. 119)")
    congress_parser.add_argument("--session-year", type=int, help="Override session year for bills")

    openstates_parser = subparsers.add_parser("openstates", help="Options for OpenStates")
    openstates_parser.add_argument("--state", required=True, help="Two letter state code")

    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()

    if args.source == "openstates":
        params = {"state": args.state}
    else:
        params = {"congress": args.congress}
        if args.session_year:
            params["session_year"] = args.session_year

    ingester = CongressAPIIngester(
        source=args.source,
        endpoint=args.endpoint,
        params=params,
        batch_size=args.batch,
        dry_run=args.dry_run,
        output_file=args.output,
    )
    ingester.ingest()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
