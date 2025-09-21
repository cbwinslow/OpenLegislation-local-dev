#!/usr/bin/env python3
"""
Base Ingestion Process for OpenLegislation

A reusable framework for data ingestion processes with built-in resume capability,
progress tracking, and error handling.

Features:
- Resume capability from interruptions
- Progress reporting with cancellation support
- Configurable retry logic
- Session-based tracking
- Standardized CLI interface
- Error handling and logging

Usage:
    from base_ingestion_process import BaseIngestionProcess

    class MyIngestionProcess(BaseIngestionProcess):
        def get_data_source(self):
            return "my_api"

        def get_target_table(self):
            return "master.my_table"

        def discover_records(self):
            # Return list of records to process
            return [{'id': 'record1', 'data': '...'}, ...]

        def process_record(self, record):
            # Process individual record
            # Return True for success, False for failure
            return True

    if __name__ == '__main__':
        process = MyIngestionProcess()
        process.run()
"""

import argparse
import signal
import sys
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union

from settings import settings
from generic_ingestion_tracker import GenericIngestionTracker, IngestionRecord
from ingestion_progress import create_progress_tracker


class BaseIngestionProcess(ABC):
    """Base class for data ingestion processes with resume capability"""

    def __init__(self, db_config: Optional[Dict[str, Any]] = None,
                 session_id: Optional[str] = None, enable_progress: bool = True):
        self.db_config = db_config or settings.db_config
        self.session_id = session_id
        self.enable_progress = enable_progress

        # Initialize components
        self.tracker: Optional[GenericIngestionTracker] = None
        self.progress = None
        self.cancelled = False

        # Set up signal handlers for graceful cancellation
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle cancellation signals"""
        print(f"\nReceived signal {signum}, initiating graceful shutdown...")
        self.cancelled = True
        if self.progress:
            self.progress.cancel()

    @abstractmethod
    def get_data_source(self) -> str:
        """Return the data source identifier (e.g., 'govinfo', 'congress_api')"""
        pass

    @abstractmethod
    def get_target_table(self) -> str:
        """Return the target database table name"""
        pass

    @abstractmethod
    def get_record_id_column(self) -> Union[str, List[str]]:
        """Return the column name(s) that uniquely identify records"""
        pass

    @abstractmethod
    def discover_records(self) -> List[Union[IngestionRecord, Dict, str]]:
        """Discover and return list of records to be processed

        Returns:
            List of IngestionRecord objects, dicts with record data, or record ID strings
        """
        pass

    @abstractmethod
    def process_record(self, record: Dict[str, Any]) -> bool:
        """Process a single record

        Args:
            record: Record data dictionary

        Returns:
            True if processing succeeded, False if failed
        """
        pass

    def get_max_retries(self) -> int:
        """Return maximum retry attempts for failed records"""
        return 3

    def get_batch_size(self) -> int:
        """Return batch size for processing (0 = process all at once)"""
        return 0

    def get_rate_limit_delay(self) -> float:
        """Return delay between record processing in seconds"""
        return 0.5

    def initialize_tracker(self):
        """Initialize the ingestion tracker"""
        self.tracker = GenericIngestionTracker(
            db_config=self.db_config,
            table_name=self.get_target_table(),
            record_id_column=self.get_record_id_column(),
            source=self.get_data_source(),
            session_id=self.session_id,
            max_retry_attempts=self.get_max_retries()
        )

    def prepare_records(self, records: List[Union[IngestionRecord, Dict, str]],
                       reset_existing: bool = False) -> List[Dict[str, Any]]:
        """Prepare records for processing and initialize tracking

        Returns:
            List of record dictionaries ready for processing
        """
        # Initialize tracking for all records
        self.tracker.initialize_records(records, reset_existing=reset_existing)

        # Convert to dict format and filter to pending only
        record_dicts = []
        for record in records:
            if isinstance(record, IngestionRecord):
                record_dict = {
                    'record_id': record.record_id,
                    'metadata': record.metadata or {},
                    'source': record.source,
                    'priority': record.priority
                }
            elif isinstance(record, dict):
                record_dict = record.copy()
                if 'record_id' not in record_dict and 'id' in record_dict:
                    record_dict['record_id'] = record_dict['id']
            else:
                record_dict = {'record_id': str(record)}

            record_dicts.append(record_dict)

        return record_dicts

    def get_pending_records(self) -> List[Dict[str, Any]]:
        """Get records that are pending processing"""
        if not self.tracker:
            return []

        pending = self.tracker.get_pending_records()
        return pending

    def run(self, resume: bool = True, reset: bool = False, limit: Optional[int] = None):
        """Run the complete ingestion process

        Args:
            resume: Whether to resume from previous run
            reset: Whether to reset all records to pending
            limit: Maximum number of records to process
        """
        print(f"Starting {self.get_data_source()} ingestion process...")

        # Initialize tracker
        self.initialize_tracker()

        # Discover all available records
        all_records = self.discover_records()
        if not all_records:
            print("No records found to process")
            return

        print(f"Discovered {len(all_records)} records")

        # Prepare records for processing
        record_dicts = self.prepare_records(all_records, reset_existing=reset)

        # Determine which records to process
        if resume:
            records_to_process = self.get_pending_records()
            print(f"Resuming: {len(records_to_process)} records pending")
        else:
            records_to_process = record_dicts
            print(f"Starting fresh: processing all {len(records_to_process)} records")

        if not records_to_process:
            print("All records already processed!")
            return

        # Apply limit if specified
        if limit:
            records_to_process = records_to_process[:limit]
            print(f"Limited to {len(records_to_process)} records")

        # Initialize progress tracking
        if self.enable_progress:
            self.progress = create_progress_tracker(len(records_to_process), f"{self.get_data_source()} Ingestion")
            self.progress.total_items = len(records_to_process)

        # Process records
        successful = 0
        failed = 0
        processed_count = 0

        batch_size = self.get_batch_size()
        rate_limit_delay = self.get_rate_limit_delay()

        for record in records_to_process:
            # Check for cancellation
            if self.cancelled:
                print("\nIngestion cancelled by user")
                break

            processed_count += 1
            record_id = record['record_id']

            try:
                # Mark as in progress
                self.tracker.mark_in_progress(record_id)

                # Update progress
                if self.progress:
                    self.progress.update(
                        current_item=processed_count,
                        status=f"Processing {record_id}",
                        bioguide_id=record_id
                    )

                # Process the record
                if self.process_record(record):
                    self.tracker.mark_completed(record_id)
                    successful += 1
                    if self.progress:
                        self.progress.update(success=True)
                else:
                    self.tracker.mark_failed(record_id, "Processing failed")
                    failed += 1
                    if self.progress:
                        self.progress.update(success=False)

                # Rate limiting
                if rate_limit_delay > 0:
                    time.sleep(rate_limit_delay)

                # Commit progress periodically
                if processed_count % 10 == 0:
                    # Any database connection cleanup would happen here
                    pass

            except Exception as e:
                error_msg = f"Unexpected error processing {record_id}: {e}"
                print(f"Error: {error_msg}")
                self.tracker.mark_failed(record_id, error_msg)
                failed += 1
                if self.progress:
                    self.progress.update(success=False)

        # Complete progress tracking
        if self.progress:
            if self.cancelled:
                self.progress.complete("Ingestion cancelled")
            else:
                self.progress.complete("Ingestion completed")

        # Print final summary
        print("\n=== INGESTION COMPLETE ===")
        print(f"Session ID: {self.tracker.session_id}")
        print(f"Records processed: {processed_count}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        # Get final stats
        final_stats = self.tracker.get_ingestion_stats()
        print(f"Success rate: {final_stats.success_rate:.1f}%")

        # Exit with error code if failures occurred
        if failed > 0:
            print("Some records failed to process")
            sys.exit(2)

    def close(self):
        """Clean up resources"""
        if self.tracker:
            self.tracker.close()


def create_cli_parser(process_name: str) -> argparse.ArgumentParser:
    """Create a standard CLI parser for ingestion processes"""
    parser = argparse.ArgumentParser(description=f'Ingest {process_name} data')
    parser.add_argument('--db-config', help='Database config JSON file')
    parser.add_argument('--session-id', help='Custom session ID for tracking')
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh instead of resuming')
    parser.add_argument('--reset', action='store_true', help='Reset all records to pending')
    parser.add_argument('--no-progress', action='store_true', help='Disable progress reporting')
    return parser


def run_ingestion_process(process_class, process_name: str):
    """Standard main function for ingestion processes"""
    parser = create_cli_parser(process_name)
    args = parser.parse_args()

    # Load database config if provided
    db_config = None
    if args.db_config:
        try:
            with open(args.db_config, 'r') as f:
                db_config = json.load(f)
        except Exception as e:
            print(f"Error loading database config: {e}")
            sys.exit(1)

    # Create and run process
    process = process_class(
        db_config=db_config,
        session_id=args.session_id,
        enable_progress=not args.no_progress
    )

    try:
        resume = not args.no_resume
        process.run(resume=resume, reset=args.reset, limit=args.limit)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        if process.progress:
            process.progress.cancel()
    except Exception as e:
        print(f"Ingestion failed: {e}")
        if process.progress:
            process.progress.complete(f"Ingestion failed: {e}")
        sys.exit(1)
    finally:
        process.close()