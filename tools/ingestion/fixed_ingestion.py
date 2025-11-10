#!/usr/bin/env python3
"""
Fixed Federal Data Ingestion Script for OpenLegislation

This script properly ingests data into the opendiscourse PostgreSQL database
using SQLAlchemy models and proper error handling.

Features:
- Uses SQLAlchemy models from database_models.py
- Connects to opendiscourse database
- Proper error handling and observability
- Stores data in correct tables
- Comprehensive logging and monitoring

Author: OpenLegislation Team
Date: 2025-11-08
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog  # For structured logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import our modules
from decorators import (
    ingestion_performance, telemetry, performance_monitor,
    feature_flag, TelemetryCollector, PerformanceMonitor
)
from database_models import (
    get_session, upsert_bill, upsert_bill_sponsor, upsert_bill_action,
    upsert_committee, upsert_committee_member, upsert_federal_member,
    store_raw_payload, Bill, BillSponsor, BillAction, Committee, CommitteeMember
)
from observability_setup import init_observability

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# API Configuration
CONGRESS_API_BASE = "https://api.congress.gov/v3"
API_KEY = os.getenv('CONGRESS_API_KEY', '')  # Will be empty in test environment

# Initialize observability
init_observability()

# Setup structured logging
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


# Event System
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


# Retry session
def create_api_session():
    """Create API session with retry logic"""
    session = requests.Session()
    retry_strategy = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def api_get(session, endpoint: str, params: Dict) -> Dict:
    """Make API request with retry logic"""
    url = f"{CONGRESS_API_BASE}/{endpoint}"
    params['api_key'] = API_KEY
    params['format'] = 'json'
    params['limit'] = params.get('limit', 250)  # Max per page

    response = session.get(url, params=params)
    if response.status_code == 429:
        logger.warning("Rate limit hit, waiting...")
    response.raise_for_status()
    return response.json()


def map_bill_api_to_db(bill_data: Dict, congress: int) -> Dict:
    """Map API bill data to database format"""
    bill_type = bill_data.get('type', '')
    number = bill_data.get('number', '')
    bill_print_no = f"{bill_type.upper()}{number}"

    # Calculate session year from congress
    session_year = 1789 + (congress - 1) * 2
    if congress >= 118:
        session_year = 2023 if congress == 118 else 2025

    return {
        'bill_print_no': bill_print_no,
        'bill_session_year': session_year,
        'title': bill_data.get('officialTitle', '') or bill_data.get('shortTitle', ''),
        'summary': bill_data.get('summary', {}).get('text', '') if bill_data.get('summary') else '',
        'active_version': bill_data.get('latestVersion', {}).get('versionName', ''),
        'data_source': 'federal',
        'congress': congress,
        'bill_type': bill_type,
        'sponsor_party': bill_data.get('sponsorParty', ''),
        'sponsor_state': bill_data.get('sponsorState', ''),
        'status': bill_data.get('status', {}).get('name', ''),
        'status_date': datetime.fromisoformat(bill_data.get('lastAction', {}).get('date', '')) if bill_data.get('lastAction', {}).get('date') else None,
        'short_title': bill_data.get('shortTitle', ''),
        'federal_congress': congress,
        'federal_source': 'congress.gov',
        'session_year': session_year
    }


def map_sponsor_api_to_db(sponsor_data: Dict, bill_print_no: str, session_year: int) -> Dict:
    """Map API sponsor data to database format"""
    return {
        'bill_print_no': bill_print_no,
        'bill_session_year': session_year,
        'budget_bill': False,
        'rules_sponsor': sponsor_data.get('isPrimary', False),
        # Note: session_member_id would need to be mapped from bioguide ID
        # For now, we'll leave it null and handle member mapping separately
    }


def map_action_api_to_db(action_data: Dict, bill_print_no: str, session_year: int, version: str, seq: int) -> Dict:
    """Map API action data to database format"""
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


@ingestion_performance(track_records=True, track_api_calls=True)
@feature_flag("federal_bills_ingestion_enabled", default_enabled=True)
def ingest_bills_fixed(db_session, callback: IngestionCallback, start_congress: int = 118, batch_size: int = 250):
    """Fixed bill ingestion that properly stores data in database"""
    api_session = create_api_session()
    total_ingested = 0

    # Process congresses from most recent backwards
    for congress in range(start_congress, 110, -1):
        offset = 0
        congress_total = 0
        params = {'congress': congress, 'limit': batch_size, 'offset': offset}

        logger.info("Starting congress processing", congress=congress)

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

                    # Map API data to database format
                    bill_db_data = map_bill_api_to_db(bill_data, congress)
                    bill_print_no = bill_db_data['bill_print_no']
                    session_year = bill_db_data['bill_session_year']
                    record_id = f"{congress}-{bill_print_no}"

                    try:
                        # Store raw payload
                        store_raw_payload(db_session, 'bill', record_id, bill_data)

                        # Upsert bill
                        upsert_bill(db_session, bill_db_data)

                        # Process sponsors
                        sponsors = bill_data.get('sponsors', [])
                        for sponsor in sponsors:
                            sponsor_db_data = map_sponsor_api_to_db(sponsor, bill_print_no, session_year)
                            upsert_bill_sponsor(db_session, sponsor_db_data)

                        # Process actions
                        actions = bill_data.get('actions', [])
                        version = bill_data.get('latestVersion', {}).get('versionName', '')
                        for seq, action in enumerate(actions, 1):
                            action_db_data = map_action_api_to_db(action, bill_print_no, session_year, version, seq)
                            upsert_bill_action(db_session, action_db_data)

                        total_ingested += 1
                        congress_total += 1

                        if congress_total % 50 == 0:
                            callback.handle(ProgressEvent(congress_total, None, f"Congress {congress}"))
                            logger.info("Congress progress", congress=congress, ingested_so_far=congress_total)

                    except Exception as e:
                        logger.error("Error processing bill", bill=bill_print_no, error=str(e))
                        callback.handle(ErrorEvent(str(e), record_id))
                        continue

                offset += len(bills)
                params['offset'] = offset
                db_session.commit()  # Batch commit

            except StopIteration:
                logger.info("Ingestion stopped by callback")
                break
            except Exception as e:
                logger.error("Error in congress", congress=congress, error=str(e), exc_info=True)
                db_session.rollback()
                callback.handle(ErrorEvent(str(e), f"congress-{congress}"))
                break  # Move to next congress instead of retrying

        callback.handle(ProgressEvent(congress_total, None, f"Completed Congress {congress}"))
        logger.info("Completed congress", congress=congress, total=congress_total)

    api_session.close()
    logger.info("Bill ingestion complete", total_ingested=total_ingested)
    return total_ingested


@ingestion_performance(track_records=True, track_api_calls=True)
@feature_flag("federal_committees_ingestion_enabled", default_enabled=True)
def ingest_committees_fixed(db_session, callback: IngestionCallback, start_congress: int = 118):
    """Fixed committee ingestion"""
    api_session = create_api_session()
    total_ingested = 0

    for congress in range(start_congress, 110, -1):
        offset = 0
        params = {'congress': congress, 'limit': 250, 'offset': offset}

        logger.info("Starting committee processing", congress=congress)

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
                    chamber = comm_data.get('chamber', 'senate').lower()
                    record_id = f"{congress}-{comm_name}"

                    try:
                        # Store raw payload
                        store_raw_payload(db_session, 'committee', record_id, comm_data)

                        # Upsert committee
                        comm_db_data = {
                            'name': comm_name,
                            'chamber': chamber,
                            'committee_id': comm_data.get('committeeId'),
                            'current_session': congress,
                            'full_name': comm_data.get('fullName', '')
                        }
                        upsert_committee(db_session, comm_db_data)

                        # Process members
                        members = comm_data.get('members', [])
                        for seq, member in enumerate(members, 1):
                            member_db_data = {
                                'majority': member.get('party') == 'Majority',
                                'sequence_no': seq,
                                'title': member.get('title', 'member'),
                                'committee_name': comm_name,
                                'session_year': congress,
                                'chamber': chamber,
                                # Note: session_member_id would need bioguide mapping
                            }
                            upsert_committee_member(db_session, member_db_data)

                        total_ingested += 1

                        if total_ingested % 25 == 0:
                            callback.handle(ProgressEvent(total_ingested, None, f"Committees processed: {total_ingested}"))

                    except Exception as e:
                        logger.error("Error processing committee", committee=comm_name, error=str(e))
                        callback.handle(ErrorEvent(str(e), record_id))
                        continue

                offset += len(committees)
                params['offset'] = offset
                db_session.commit()

            except StopIteration:
                break
            except Exception as e:
                logger.error("Committee error", congress=congress, error=str(e))
                db_session.rollback()
                callback.handle(ErrorEvent(str(e), f"congress-{congress}"))
                break

        logger.info("Completed committees congress", congress=congress)

    api_session.close()
    logger.info("Committees ingestion complete", total_ingested=total_ingested)
    return total_ingested


def verify_ingestion(db_session):
    """Verify data was ingested correctly"""
    try:
        # Check bills count
        bill_count = db_session.query(Bill).count()
        logger.info("Verification: Bills ingested", count=bill_count)

        # Check committees count
        committee_count = db_session.query(Committee).count()
        logger.info("Verification: Committees ingested", count=committee_count)

        # Check recent bills
        recent_bills = db_session.query(Bill).filter(Bill.congress >= 115).count()
        logger.info("Verification: Recent bills (115+)", count=recent_bills)

        return {
            'bills': bill_count,
            'committees': committee_count,
            'recent_bills': recent_bills
        }

    except Exception as e:
        logger.error("Verification failed", error=str(e))
        return {}


def main():
    """Main ingestion function"""
    parser = argparse.ArgumentParser(description="Fixed Federal Data Ingestion for OpenLegislation")
    parser.add_argument('--type', choices=['bills', 'committees', 'all'], default='all',
                       help="Type of data to ingest")
    parser.add_argument('--start-congress', type=int, default=118,
                       help="Start from congress (default: 118)")
    parser.add_argument('--batch-size', type=int, default=250,
                       help="Batch size for API calls")
    parser.add_argument('--dry-run', action='store_true',
                       help="Simulate without database writes")
    parser.add_argument('--verify-only', action='store_true',
                       help="Only run verification")

    args = parser.parse_args()

    # Setup callback
    class LoggingCallback(IngestionCallback):
        def __init__(self):
            super().__init__(
                on_progress=lambda e: logger.info("Progress", **e.data),
                on_error=lambda e: logger.error("Ingestion error", **e.data),
                on_stop=lambda e: logger.info("Ingestion stopped", **e.data)
            )

    callback = LoggingCallback()

    # Get database session
    db_session = get_session()

    try:
        start_time = datetime.utcnow()
        logger.info("Starting fixed ingestion",
                   type=args.type,
                   start_congress=args.start_congress,
                   dry_run=args.dry_run)

        if args.verify_only:
            # Only run verification
            results = verify_ingestion(db_session)
            logger.info("Verification results", **results)
            return

        if args.dry_run:
            logger.info("DRY RUN: Simulating ingestion without database writes")
            # Simulate some work
            import time
            time.sleep(1)
            logger.info("Dry run completed")
            return

        total_ingested = 0

        # Run ingestion based on type
        if args.type in ['bills', 'all']:
            logger.info("Starting bill ingestion")
            bills_ingested = ingest_bills_fixed(db_session, callback, args.start_congress, args.batch_size)
            total_ingested += bills_ingested
            logger.info("Bill ingestion completed", count=bills_ingested)

        if args.type in ['committees', 'all']:
            logger.info("Starting committee ingestion")
            committees_ingested = ingest_committees_fixed(db_session, callback, args.start_congress)
            total_ingested += committees_ingested
            logger.info("Committee ingestion completed", count=committees_ingested)

        # Verification
        verification_results = verify_ingestion(db_session)

        # Final metrics
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        metrics = {
            'ingestion_type': args.type,
            'start_congress': args.start_congress,
            'total_ingested': total_ingested,
            'duration_seconds': duration,
            'end_time': end_time.isoformat(),
            'verification': verification_results
        }

        logger.info("Ingestion completed successfully", **metrics)

        # Save metrics to file
        with open('ingestion_metrics.json', 'w') as f:
            json.dump(metrics, f, default=str, indent=2)

        print(f"\n🎉 Ingestion completed successfully!")
        print(f"📊 Total records ingested: {total_ingested}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📋 Verification: {verification_results}")

    except Exception as e:
        logger.error("Fatal ingestion error", error=str(e), exc_info=True)
        db_session.rollback()
        raise
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
