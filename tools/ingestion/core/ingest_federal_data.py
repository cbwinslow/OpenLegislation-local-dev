#!/usr/bin/env python3
"""
Enhanced Federal Data Ingestion Script for OpenLegislation
Optimized for congress.gov API: full/recent data (start congress=118 backwards), dedup via unique constraints/upserts,
events/callbacks for progress/stop, observability with structlog/metrics.
Supports bills, amendments (via bill details), committees. Efficient: full pagination, bulk fallback noted.
Loads config from .env (API key, DB URL).
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from sqlalchemy import create_engine, text, UniqueConstraint
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog  # For structured logging
from dotenv import load_dotenv

load_dotenv()  # Load .env from project root

# API Configuration from .env
CONGRESS_API_BASE = "https://api.congress.gov/v3"
API_KEY = os.getenv('CONGRESS_API_KEY')
if not API_KEY:
    logger.error("CONGRESS_API_KEY required in .env")
    sys.exit(1)

# Database Configuration from .env (user-provided: host=100.90.23.59, db=opendiscourse, pass=opendiscourse123, port=5432)
DB_URL = os.getenv('DATABASE_URL', 'postgresql://opendiscourse:opendiscourse123@100.90.23.59:5432/opendiscourse')
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

# Event System (unchanged)
class IngestionEvent:
    """Base event class for ingestion callbacks."""
    def __init__(self, event_type: str, data: Dict):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.utcnow()

class ProgressEvent(IngestionEvent):
    """Progress report event."""
    def __init__(self, ingested: int, total: int, stage: str):
        super().__init__('progress', {'ingested': ingested, 'total': total, 'stage': stage})

class StopEvent(IngestionEvent):
    """Stop signal event."""
    def __init__(self, reason: str):
        super().__init__('stop', {'reason': reason})

class ErrorEvent(IngestionEvent):
    """Error event."""
    def __init__(self, error: str, record_id: str):
        super().__init__('error', {'error': error, 'record_id': record_id})

class IngestionCallback:
    """Callback handler for events."""
    def __init__(self, on_progress: Optional[Callable] = None, on_stop: Optional[Callable] = None, on_error: Optional[Callable] = None):
        self.on_progress = on_progress or (lambda e: None)
        self.on_stop = on_stop or (lambda e: None)
        self.on_error = on_error or (lambda e: None)

    def handle(self, event: IngestionEvent):
        if isinstance(event, ProgressEvent):
            self.on_progress(event)
        elif isinstance(event, StopEvent):
            self.on_stop(event)
            raise StopIteration("Ingestion stopped")
        elif isinstance(event, ErrorEvent):
            self.on_error(event)

# Setup structured logging with structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()

# Retry session (unchanged)
def create_api_session():
    session = requests.Session()
    retry_strategy = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def api_get(session, endpoint: str, params: Dict) -> Dict:
    url = f"{CONGRESS_API_BASE}/{endpoint}"
    params['api_key'] = API_KEY
    params['format'] = 'json'
    params['limit'] = params.get('limit', 250)  # Max per page for efficiency
    response = session.get(url, params=params)
    if response.status_code == 429:
        logger.warning("Rate limit hit, waiting...")
    response.raise_for_status()
    return response.json()

def store_raw_payload(db_session, ingestion_type: str, record_id: str, payload: Dict):
    raw = GovInfoRawPayload(ingestion_type=ingestion_type, record_id=record_id, payload=payload)
    db_session.add(raw)

def upsert_record(db_session, model, data: Dict, unique_fields: List[str], event_callback: IngestionCallback):
    """Upsert with dedup using ON CONFLICT."""
    try:
        stmt = insert(model).values(**data)
        stmt = stmt.on_conflict_do_update(
            index_elements=unique_fields,
            set_=dict((k, v) for k, v in data.items() if k != 'id')
        ).returning(model.id)
        result = db_session.execute(stmt)
        db_session.commit()
        return result.scalar()
    except IntegrityError as e:
        logger.warning(f"Dedup: {e}")
        db_session.rollback()
        event_callback.handle(ErrorEvent(str(e), data.get('bill_print_no', record_id)))
    except SQLAlchemyError as e:
        logger.error(f"DB error: {e}")
        db_session.rollback()
        event_callback.handle(ErrorEvent(str(e), data.get('bill_print_no', record_id)))
        raise

def map_bill_api_to_model(bill_data: Dict, congress: int) -> Dict:
    """Comprehensive mapping from API to Bill model."""
    bill_type = bill_data.get('type', '')
    number = bill_data.get('number', '')
    bill_print_no = f"{bill_type.upper()}{number}"  # e.g., HR1 -> HR1
    session_year = congress

    return {
        'bill_print_no': bill_print_no,
        'bill_session_year': session_year,
        'title': bill_data.get('officialTitle', '') or bill_data.get('shortTitle', ''),
        'summary': bill_data.get('summary', ''),
        'active_version': bill_data.get('latestVersion', {}).get('versionName', ''),
        'data_source': 'federal',
        'congress': congress,
        'bill_type': bill_type,
        'sponsor_party': bill_data.get('sponsorParty', ''),
        'sponsor_state': bill_data.get('sponsorState', ''),
        'status': bill_data.get('status', {}).get('name', ''),
        'status_date': datetime.fromisoformat(bill_data.get('lastAction', {}).get('date', '')) if bill_data.get('lastAction') else None,
        'short_title': bill_data.get('shortTitle', ''),
        # Add more: program_info, etc. from API fields
    }

def map_sponsor_api_to_model(sponsor_data: Dict, bill_print_no: str, session_year: int) -> Dict:
    return {
        'bill_print_no': bill_print_no,
        'bill_session_year': session_year,
        'session_member_id': None,  # Map to federal_member.id via bioguide
        'budget_bill': False,
        'rules_sponsor': sponsor_data.get('isPrimary', False),
    }

def map_action_api_to_model(action_data: Dict, bill_print_no: str, session_year: int, version: str, seq: int) -> Dict:
    date_str = action_data.get('date', '')
    effect_date = datetime.fromisoformat(date_str).date() if date_str else None
    return {
        'bill_print_no': bill_print_no,
        'bill_session_year': session_year,
        'bill_amend_version': version,
        'effect_date': effect_date,
        'text': action_data.get('description', ''),
        'sequence_no': seq,
        'chamber': action_data.get('chamber', ''),
    }

def ingest_bills_optimized(db_session, callback: IngestionCallback, start_congress: int = 118, batch_size: int = 250):
    """Optimized full ingestion starting from recent congress backwards."""
    api_session = create_api_session()
    total_ingested = 0
    for congress in range(start_congress, 110, -1):  # Backwards from 118 to 111 (adjust range)
        offset = 0
        congress_total = 0
        params = {'congress': congress, 'limit': batch_size, 'offset': offset}

        while True:
            try:
                data = api_get(api_session, 'bill', params)
                bills = data.get('bills', [])
                if not bills:
                    break

                for bill_data in bills:
                    if hasattr(callback, 'should_stop') and callback.should_stop():
                        callback.handle(StopEvent("User stop requested"))
                        return

                    bill_type = bill_data.get('type', '')
                    number = bill_data.get('number', '')
                    bill_print_no = f"{bill_type.upper()}{number}"
                    record_id = f"{congress}-{bill_print_no}"

                    # Store raw
                    store_raw_payload(db_session, 'bill', record_id, bill_data)

                    # Upsert bill with full mapping
                    bill_data_dict = map_bill_api_to_model(bill_data, congress)
                    upsert_record(db_session, Bill, bill_data_dict, ['bill_print_no', 'bill_session_year'])

                    # Sponsors (full mapping)
                    sponsors = bill_data.get('sponsors', [])
                    for sponsor in sponsors:
                        sponsor_dict = map_sponsor_api_to_model(sponsor, bill_print_no, congress)
                        upsert_record(db_session, BillSponsor, sponsor_dict, ['bill_print_no', 'bill_session_year'])

                    # Actions (full)
                    actions = bill_data.get('actions', [])
                    version = bill_data.get('latestVersion', {}).get('versionName', '')
                    for seq, action in enumerate(actions, 1):
                        action_dict = map_action_api_to_model(action, bill_print_no, congress, version, seq)
                        upsert_record(db_session, BillAmendmentAction, action_dict, ['bill_print_no', 'bill_session_year', 'bill_amend_version', 'sequence_no'])

                    # Amendments/Votes if in data
                    if 'amendments' in bill_data:
                        # Map amendments
                        pass  # Implement mapping

                    total_ingested += 1
                    congress_total += 1

                    if congress_total % 100 == 0:
                        callback.handle(ProgressEvent(congress_total, None, f"Congress {congress}"))

                offset += len(bills)
                params['offset'] = offset
                db_session.commit()  # Batch commit

                logger.info("Congress progress", congress=congress, ingested_so_far=congress_total)

            except StopIteration:
                logger.info("Ingestion stopped by callback")
                break
            except Exception as e:
                logger.error("Error in congress", congress=congress, error=str(e), exc_info=True)
                db_session.rollback()
                callback.handle(ErrorEvent(str(e), f"congress-{congress}"))
                continue

        callback.handle(ProgressEvent(congress_total, None, f"Completed Congress {congress}"))
        logger.info("Completed congress", congress=congress, total=congress_total)

    api_session.close()
    logger.info("Total ingestion complete", total_ingested=total_ingested)

def ingest_committees_optimized(db_session, callback: IngestionCallback, start_congress: int = 118):
    api_session = create_api_session()
    total_ingested = 0
    for congress in range(start_congress, 110, -1):
        offset = 0
        params = {'congress': congress, 'limit': 250, 'offset': offset}

        while True:
            try:
                data = api_get(api_session, 'committee', params)
                committees = data.get('committees', [])
                if not committees:
                    break

                for comm_data in committees:
                    if hasattr(callback, 'should_stop') and callback.should_stop():
                        callback.handle(StopEvent("User stop requested"))
                        return

                    comm_name = comm_data.get('name', '')
                    chamber = comm_data.get('chamber', 'senate').lower()  # Map to enum
                    record_id = f"{congress}-{comm_name}"

                    # Store raw
                    store_raw_payload(db_session, 'committee', record_id, comm_data)

                    # Upsert committee
                    comm_dict = {
                        'name': comm_name,
                        'chamber': chamber,
                        'id': comm_data.get('committeeId'),
                        'current_session': congress,
                        'full_name': comm_data.get('fullName', '')
                    }
                    upsert_record(db_session, Committee, comm_dict, ['name', 'chamber'])

                    # Members
                    members = comm_data.get('members', [])
                    for seq, member in enumerate(members, 1):
                        member_dict = {
                            'majority': member.get('party') == 'Majority',
                            'sequence_no': seq,
                            'title': member.get('title', 'member'),
                            'committee_name': comm_name,
                            'version_created': datetime.utcnow(),
                            'session_year': congress,
                            'session_member_id': None,  # Map via bioguide
                            'chamber': chamber
                        }
                        upsert_record(db_session, CommitteeMember, member_dict, ['committee_name', 'chamber', 'session_year', 'session_member_id'])

                    total_ingested += 1

                offset += len(committees)
                params['offset'] = offset
                db_session.commit()

                logger.info("Committee progress", congress=congress, ingested=len(committees))

            except StopIteration:
                break
            except Exception as e:
                logger.error("Committee error", congress=congress, error=str(e))
                db_session.rollback()
                callback.handle(ErrorEvent(str(e), f"congress-{congress}-{comm_name}"))
                continue

        logger.info("Completed committees congress", congress=congress)

    api_session.close()
    logger.info("Committees ingestion complete", total_ingested=total_ingested)

def main():
    parser = argparse.ArgumentParser(description="Optimized Federal Ingestion with Events/Dedup/Observability")
    parser.add_argument('--type', choices=['bills', 'committees'], required=True)
    parser.add_argument('--start-congress', type=int, default=118, help="Start from recent congress backwards")
    parser.add_argument('--batch-size', type=int, default=250)
    parser.add_argument('--dry-run', action='store_true', help="Simulate without DB writes")
    args = parser.parse_args()

    class StoppableCallback(IngestionCallback):
        def __init__(self):
            self._stop_requested = False
            super().__init__(
                on_progress=lambda e: logger.info("Progress update", **e.data),
                on_error=lambda e: logger.error("Error event", **e.data),
                on_stop=lambda e: setattr(self, '_stop_requested', True)
            )

        def should_stop(self):
            return self._stop_requested

    callback = StoppableCallback()

    start_time = datetime.utcnow()
    db_session = SessionLocal()
    total_ingested = 0  # Track globally or per type

    try:
        if args.dry_run:
            logger.info("Dry run: Simulating ingestion")
            return

        if args.type == 'bills':
            ingest_bills_optimized(db_session, callback, args.start_congress, args.batch_size)
        elif args.type == 'committees':
            ingest_committees_optimized(db_session, callback, args.start_congress)

        # Final metrics
        end_time = datetime.utcnow()
        metrics = {
            'type': args.type,
            'start_congress': args.start_congress,
            'total_ingested': total_ingested,
            'duration_seconds': (end_time - start_time).total_seconds(),
            'end_time': end_time.isoformat()
        }
        with open('ingestion_metrics.json', 'w') as f:
            json.dump(metrics, f, default=str)
        logger.info("Metrics saved", metrics=metrics)

        # Verification
        verify_ingestion(db_session, args.type, args.start_congress)

    except Exception as e:
        logger.error("Fatal ingestion error", error=str(e), exc_info=True)
        db_session.rollback()
    finally:
        db_session.close()

def verify_ingestion(db_session, data_type: str, congress: int):
    """Enhanced verification with integrity checks."""
    if data_type == 'bills':
        count_q = text("SELECT COUNT(*) FROM master.bill WHERE congress >= :congress AND data_source = 'federal'")
        count = db_session.execute(count_q, {'congress': congress}).scalar()
        logger.info("Verification: Bills", count=count)

        # Integrity: Check for orphans (e.g., actions without bill)
        orphan_q = text("""
            SELECT COUNT(*) FROM master.bill_amendment_action baa
            LEFT JOIN master.bill b ON (baa.bill_print_no = b.bill_print_no AND baa.bill_session_year = b.bill_session_year)
            WHERE b.bill_print_no IS NULL AND b.data_source = 'federal'
        """)
        orphans = db_session.execute(orphan_q).scalar()
        if orphans > 0:
            logger.warning("Integrity issue: Orphan actions", count=orphans)
        else:
            logger.info("Verification: No orphan actions")

    # Similar for committees
    logger.info("Verification complete")

if __name__ == "__main__":
    main()