"""Command line entrypoint for running ingestion jobs."""
from __future__ import annotations

import argparse
import logging
from typing import Iterable

from ..clients import (
    CongressGovClient,
    GovInfoClient,
    OpenLegislationClient,
    OpenStatesClient,
)
from ..models import (
    CongressBill,
    CongressMember,
    CongressVote,
    GovInfoDownload,
    GovInfoPackage,
    OpenLegislationAgenda,
    OpenLegislationBill,
    OpenStatesBill,
    OpenStatesPerson,
    OpenStatesVoteEvent,
)
from .config import get_settings
from .db import session_scope
from .schema import (
    congress_bills,
    congress_members,
    congress_votes,
    govinfo_downloads,
    govinfo_packages,
    openleg_agendas,
    openleg_bills,
    openstates_bills,
    openstates_people,
    openstates_votes,
)
from .utils import chunked, upsert_records

logger = logging.getLogger(__name__)


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _model_to_dict(model) -> dict:
    return model.dict(exclude_none=True)


def ingest_openstates_people(state: str | None, chamber: str | None, batch_size: int) -> None:
    settings = get_settings()
    target_state = state or settings.default_state
    if not target_state:
        raise ValueError("State must be provided via --state or PIPELINE_DEFAULT_STATE")
    logger.info("Fetching OpenStates legislators for %s", target_state)
    with OpenStatesClient(api_key=settings.openstates_api_key) as client:
        people: Iterable[OpenStatesPerson] = client.list_people(state=target_state, chamber=chamber)
        with session_scope() as db_session:
            for batch in chunked(people, batch_size):
                records = [_model_to_dict(person) for person in batch]
                upsert_records(db_session, openstates_people, records, ["id"])


def ingest_openstates_bills(state: str | None, session: str | None, batch_size: int) -> None:
    settings = get_settings()
    target_state = state or settings.default_state
    target_session = session or settings.default_session
    if not target_state:
        raise ValueError("State must be provided via --state or PIPELINE_DEFAULT_STATE")
    if not target_session:
        raise ValueError("Session must be provided via --session or PIPELINE_DEFAULT_SESSION")
    logger.info("Fetching OpenStates bills for %s session %s", target_state, target_session)
    with OpenStatesClient(api_key=settings.openstates_api_key) as client:
        bills: Iterable[OpenStatesBill] = client.list_bills(state=target_state, session=target_session)
        with session_scope() as db_session:
            for batch in chunked(bills, batch_size):
                records = [_model_to_dict(bill) for bill in batch]
                upsert_records(db_session, openstates_bills, records, ["id"])


def ingest_openstates_votes(bill_id: str, batch_size: int) -> None:
    settings = get_settings()
    logger.info("Fetching OpenStates vote events for %s", bill_id)
    with OpenStatesClient(api_key=settings.openstates_api_key) as client:
        votes: Iterable[OpenStatesVoteEvent] = client.list_votes(bill_id)
        with session_scope() as db_session:
            for batch in chunked(votes, batch_size):
                records = [_model_to_dict(vote) for vote in batch]
                upsert_records(db_session, openstates_votes, records, ["id"])


def ingest_congress_bills(congress: str, batch_size: int) -> None:
    settings = get_settings()
    logger.info("Fetching Congress bills for congress %s", congress)
    with CongressGovClient(api_key=settings.congress_api_key) as client:
        bills: Iterable[CongressBill] = client.list_bills(congress=congress)
        with session_scope() as db_session:
            for batch in chunked(bills, batch_size):
                records = [_model_to_dict(bill) for bill in batch]
                for record in records:
                    record.setdefault("bill_id", f"{record['bill_type'].upper()}{record['bill_number']}-{record['congress']}")
                upsert_records(db_session, congress_bills, records, ["bill_id"])


def ingest_congress_members(congress: str, chamber: str, batch_size: int) -> None:
    settings = get_settings()
    logger.info("Fetching Congress members for %s %s", congress, chamber)
    with CongressGovClient(api_key=settings.congress_api_key) as client:
        members: Iterable[CongressMember] = client.list_members(congress=congress, chamber=chamber)
        with session_scope() as db_session:
            for batch in chunked(members, batch_size):
                records = [_model_to_dict(member) for member in batch]
                upsert_records(db_session, congress_members, records, ["bioguide_id"])


def ingest_congress_votes(congress: str, chamber: str, batch_size: int) -> None:
    settings = get_settings()
    logger.info("Fetching Congress votes for %s %s", congress, chamber)
    with CongressGovClient(api_key=settings.congress_api_key) as client:
        votes: Iterable[CongressVote] = client.list_votes(congress=congress, chamber=chamber)
        with session_scope() as db_session:
            for batch in chunked(votes, batch_size):
                records = [_model_to_dict(vote) for vote in batch]
                for record in records:
                    record.setdefault(
                        "id",
                        f"{record['chamber']}-{record['congress']}-{record.get('session', '1')}-{record['roll_call']}",
                    )
                upsert_records(db_session, congress_votes, records, ["id"])


def ingest_govinfo(collection: str, batch_size: int) -> None:
    settings = get_settings()
    logger.info("Fetching GovInfo packages for collection %s", collection)
    with GovInfoClient(api_key=settings.govinfo_api_key) as client:
        packages: Iterable[GovInfoPackage] = client.list_packages(collection=collection)
        with session_scope() as db_session:
            for batch in chunked(packages, batch_size):
                records = [_model_to_dict(pkg) for pkg in batch]
                upsert_records(db_session, govinfo_packages, records, ["package_id"])
                for record in records:
                    downloads: Iterable[GovInfoDownload] = client.list_downloads(record["package_id"])
                    download_records = [_model_to_dict(d) for d in downloads]
                    upsert_records(db_session, govinfo_downloads, download_records, ["package_id", "format"])


def ingest_openleg_bills(session: str, batch_size: int) -> None:
    settings = get_settings()
    logger.info("Fetching OpenLegislation bills for session %s", session)
    with OpenLegislationClient(api_key=settings.ny_openleg_api_key) as client:
        bills: Iterable[OpenLegislationBill] = client.list_bills(session=session)
        with session_scope() as db_session:
            for batch in chunked(bills, batch_size):
                records = [_model_to_dict(bill) for bill in batch]
                upsert_records(db_session, openleg_bills, records, ["print_no"])


def ingest_openleg_agendas(year: str, batch_size: int) -> None:
    settings = get_settings()
    logger.info("Fetching OpenLegislation agendas for year %s", year)
    with OpenLegislationClient(api_key=settings.ny_openleg_api_key) as client:
        agendas: Iterable[OpenLegislationAgenda] = client.list_agendas(year=year)
        with session_scope() as db_session:
            for batch in chunked(agendas, batch_size):
                records = [_model_to_dict(agenda) for agenda in batch]
                upsert_records(db_session, openleg_agendas, records, ["agenda_id"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest legislative data into PostgreSQL")
    parser.add_argument("source", choices=[
        "openstates-people",
        "openstates-bills",
        "openstates-votes",
        "congress-bills",
        "congress-members",
        "congress-votes",
        "govinfo",
        "openleg-bills",
        "openleg-agendas",
    ])
    parser.add_argument("--state", help="State/jurisdiction for OpenStates requests")
    parser.add_argument("--session", help="Session identifier")
    parser.add_argument("--chamber", help="Legislative chamber")
    parser.add_argument("--bill-id", help="OpenStates bill ID for vote ingestion")
    parser.add_argument("--collection", help="GovInfo collection code (e.g., BILLS)")
    parser.add_argument("--year", help="OpenLegislation agenda year")
    parser.add_argument("--congress", default="118", help="Congress number for Congress.gov requests")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of records to write per batch")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.verbose)

    if args.source == "openstates-people":
        ingest_openstates_people(args.state, args.chamber, args.batch_size)
    elif args.source == "openstates-bills":
        ingest_openstates_bills(args.state, args.session, args.batch_size)
    elif args.source == "openstates-votes":
        if not args.bill_id:
            raise ValueError("--bill-id is required for openstates-votes")
        ingest_openstates_votes(args.bill_id, args.batch_size)
    elif args.source == "congress-bills":
        ingest_congress_bills(args.congress, args.batch_size)
    elif args.source == "congress-members":
        if not args.chamber:
            raise ValueError("--chamber is required for congress-members")
        ingest_congress_members(args.congress, args.chamber, args.batch_size)
    elif args.source == "congress-votes":
        if not args.chamber:
            raise ValueError("--chamber is required for congress-votes")
        ingest_congress_votes(args.congress, args.chamber, args.batch_size)
    elif args.source == "govinfo":
        if not args.collection:
            raise ValueError("--collection is required for GovInfo ingestion")
        ingest_govinfo(args.collection, args.batch_size)
    elif args.source == "openleg-bills":
        session = args.session or args.year
        if not session:
            raise ValueError("--session is required for OpenLegislation bills")
        ingest_openleg_bills(session, args.batch_size)
    elif args.source == "openleg-agendas":
        if not args.year:
            raise ValueError("--year is required for OpenLegislation agendas")
        ingest_openleg_agendas(args.year, args.batch_size)
    else:
        parser.error(f"Unsupported source {args.source}")


if __name__ == "__main__":
    main()

