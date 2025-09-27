#!/usr/bin/env python3
"""
Generic Ingestion Tracker for OpenLegislation

A flexible ingestion tracking system that can monitor progress for any type of data ingestion
across different tables, sources, and processes.

Features:
- Table-agnostic tracking (works with any database table)
- Configurable record identifiers (single column or composite keys)
- Source-based organization (API, file, etc.)
- Session-based grouping for multiple ingestion runs
- Resume capability with automatic state recovery
- Progress statistics and reporting

Usage:
    from generic_ingestion_tracker import GenericIngestionTracker

    # Track bill ingestion
    tracker = GenericIngestionTracker(db_config, 'master.bill', 'bill_id')
    tracker.initialize_records(bill_list, source='govinfo')

    # During processing
    tracker.mark_in_progress('H123-119')
    # ... process bill ...
    tracker.mark_completed('H123-119')

    # For resume
    pending = tracker.get_pending_records()
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass

import psycopg2
import psycopg2.extras

from settings import settings


@dataclass
class IngestionRecord:
    """Represents a record to be ingested"""

    record_id: str  # Unique identifier for the record
    metadata: Dict[str, Any] = None  # Additional data about the record
    source: str = "unknown"  # Data source (api, file, etc.)
    priority: int = 0  # Processing priority (higher = more important)


@dataclass
class IngestionStats:
    """Statistics for ingestion progress"""

    total_records: int = 0
    completed: int = 0
    failed: int = 0
    in_progress: int = 0
    pending: int = 0
    success_rate: float = 0.0
    source: str = "unknown"
    table_name: str = "unknown"


class GenericIngestionTracker:
    """Generic tracker for any type of data ingestion"""

    def __init__(
        self,
        db_config: Dict[str, Any],
        table_name: str,
        record_id_column: Union[str, List[str]],
        source: str = "unknown",
        session_id: Optional[str] = None,
        max_retry_attempts: int = 3,
    ):
        """
        Initialize tracker for a specific table and data source

        Args:
            db_config: Database configuration
            table_name: Name of the table being ingested into
            record_id_column: Column name(s) that uniquely identify records
            source: Data source identifier (e.g., 'govinfo', 'congress_api')
            session_id: Optional session identifier
            max_retry_attempts: Maximum retry attempts for failed records
        """
        self.db_config = db_config
        self.table_name = table_name
        self.record_id_column = (
            record_id_column
            if isinstance(record_id_column, list)
            else [record_id_column]
        )
        self.source = source
        self.session_id = session_id or str(uuid.uuid4())
        self.max_retry_attempts = max_retry_attempts
        self._db_connection = None
        self._db_cursor = None

        # Ensure tracking table exists
        self._ensure_tracking_table()

    def _ensure_tracking_table(self):
        """Create the generic ingestion tracking table if it doesn't exist"""
        conn = None
        try:
            print("[tracker] _ensure_tracking_table start")
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Ensure master schema exists so table creation succeeds
            print("[tracker] Creating schema if not exists")
            cursor.execute(
                """
                CREATE SCHEMA IF NOT EXISTS master
            """
            )
            print("[tracker] Schema ensured")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS master.ingestion_status (
                    id BIGSERIAL PRIMARY KEY,
                    table_name TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'unknown',
                    ingestion_status TEXT NOT NULL CHECK (ingestion_status IN ('pending', 'in_progress', 'completed', 'failed')),
                    last_attempted_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    failure_reason TEXT,
                    retry_count INTEGER DEFAULT 0,
                    processing_priority INTEGER DEFAULT 0,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT now(),
                    updated_at TIMESTAMP DEFAULT now(),
                    ingestion_session_id TEXT,
                    UNIQUE(table_name, record_id, source)
                )
            """
            )

            # Indexes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ingestion_status_table_record
                ON master.ingestion_status(table_name, record_id, source)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ingestion_status_status
                ON master.ingestion_status(ingestion_status)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ingestion_status_session
                ON master.ingestion_status(ingestion_session_id)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ingestion_status_source
                ON master.ingestion_status(source)
            """
            )

            # Triggers - use DO block to create trigger if it doesn't exist (Postgres doesn't support
            # CREATE TRIGGER IF NOT EXISTS on all versions)
            try:
                cursor.execute(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'log_ingestion_updates_to_change_log') THEN
                            EXECUTE 'CREATE TRIGGER log_ingestion_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.ingestion_status FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates()';
                        END IF;
                    END
                    $$;
                """
                )
            except Exception as e:
                # Trigger creation may fail if helper function does not exist in DB migrations.
                # Log warning and continue - tracking table still usable without trigger.
                print(f"Warning: could not create ingestion trigger: {e}")

            conn.commit()
            try:
                cursor.execute(
                    "SELECT current_database(), current_user, inet_client_addr()"
                )
                dbinfo = cursor.fetchone()
            except Exception:
                dbinfo = None
            try:
                cursor.execute("SHOW search_path")
                search_path = cursor.fetchone()
            except Exception:
                search_path = None
            try:
                cursor.execute("SELECT to_regclass('master.ingestion_status')")
                reg = cursor.fetchone()
            except Exception:
                reg = None

            print(
                f"[tracker] Table creation/commit complete; dbinfo={dbinfo}, search_path={search_path}, to_regclass={reg}"
            )

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def _get_db_connection(self):
        """Get database connection with proper cursor"""
        if not self._db_connection or self._db_connection.closed:
            self._db_connection = psycopg2.connect(**self.db_config)
            self._db_cursor = self._db_connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        return self._db_connection, self._db_cursor

    def _table_exists(self, schema_table: str) -> bool:
        """Check if a table exists in the database"""
        conn, cursor = self._get_db_connection()
        try:
            cursor.execute("SELECT to_regclass(%s)", (schema_table,))
            res = cursor.fetchone()
            return bool(res and res[0])
        except Exception:
            return False

    def _execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Execute a database query with error handling"""
        conn, cursor = self._get_db_connection()
        try:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            return None
        except Exception as e:
            print(f"Database error: {e}")
            conn.rollback()
            raise

    def _commit(self):
        """Commit current transaction"""
        if self._db_connection:
            self._db_connection.commit()

    def initialize_records(
        self,
        records: List[Union[IngestionRecord, Dict, str]],
        reset_existing: bool = False,
    ):
        """
        Initialize ingestion status for a list of records

        Args:
            records: List of records (IngestionRecord objects, dicts, or strings)
            reset_existing: If True, reset status of existing records to pending
        """
        # Convert records to IngestionRecord objects
        ingestion_records = []
        for record in records:
            if isinstance(record, IngestionRecord):
                ingestion_records.append(record)
            elif isinstance(record, dict):
                record_id = record.get("record_id") or record.get("id") or str(record)
                metadata = {
                    k: v for k, v in record.items() if k not in ["record_id", "id"]
                }
                ingestion_records.append(
                    IngestionRecord(
                        record_id=record_id, metadata=metadata, source=self.source
                    )
                )
            else:
                ingestion_records.append(
                    IngestionRecord(record_id=str(record), source=self.source)
                )

        if not ingestion_records:
            return

        # Prepare data for bulk insert
        values = []
        for record in ingestion_records:
            values.append(
                (
                    self.table_name,
                    record.record_id,
                    self.source,
                    self.session_id,
                    psycopg2.extras.Json(record.metadata or {}),
                    record.priority,
                    "pending",
                )
            )

        value_placeholders = ",".join(["(%s, %s, %s, %s, %s, %s, %s)"] * len(values))
        flattened_values = [item for sublist in values for item in sublist]

        query = f"""
            INSERT INTO master.ingestion_status
            (table_name, record_id, source, ingestion_session_id, metadata, processing_priority, ingestion_status)
            VALUES {value_placeholders}
            ON CONFLICT (table_name, record_id, source) DO NOTHING
        """

        # Ensure table exists before attempting insert (some DBs may not have schema applied)
        if not self._table_exists("master.ingestion_status"):
            print(
                "[tracker] master.ingestion_status missing at insert time, attempting to ensure table"
            )
            self._ensure_tracking_table()

        self._execute_query(query, tuple(flattened_values))

        # Optionally reset existing records
        if reset_existing:
            record_ids = [r.record_id for r in ingestion_records]
            reset_query = """
                UPDATE master.ingestion_status
                SET ingestion_status = 'pending',
                    retry_count = 0,
                    failure_reason = NULL,
                    updated_at = now()
                WHERE table_name = %s AND source = %s AND record_id = ANY(%s)
                  AND ingestion_status IN ('failed', 'completed')
            """
            self._execute_query(reset_query, (self.table_name, self.source, record_ids))

        self._commit()

    def mark_in_progress(self, record_id: str):
        """Mark a record as currently being processed"""
        query = """
            UPDATE master.ingestion_status
            SET ingestion_status = 'in_progress',
                last_attempted_at = now(),
                updated_at = now()
            WHERE table_name = %s AND record_id = %s AND source = %s
        """
        self._execute_query(query, (self.table_name, record_id, self.source))
        self._commit()

    def mark_completed(self, record_id: str):
        """Mark a record as successfully processed"""
        query = """
            UPDATE master.ingestion_status
            SET ingestion_status = 'completed',
                completed_at = now(),
                updated_at = now(),
                failure_reason = NULL
            WHERE table_name = %s AND record_id = %s AND source = %s
        """
        self._execute_query(query, (self.table_name, record_id, self.source))
        self._commit()

    def mark_failed(self, record_id: str, failure_reason: str = None):
        """Mark a record as failed to process"""
        # Increment retry count
        query = """
            UPDATE master.ingestion_status
            SET ingestion_status = CASE
                    WHEN retry_count >= %s THEN 'failed'
                    ELSE 'pending'
                END,
                retry_count = retry_count + 1,
                failure_reason = %s,
                last_attempted_at = now(),
                updated_at = now()
            WHERE table_name = %s AND record_id = %s AND source = %s
        """
        self._execute_query(
            query,
            (
                self.max_retry_attempts,
                failure_reason,
                self.table_name,
                record_id,
                self.source,
            ),
        )
        self._commit()

    def get_record_status(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Get current status for a specific record"""
        query = """
            SELECT * FROM master.ingestion_status
            WHERE table_name = %s AND record_id = %s AND source = %s
        """
        results = self._execute_query(
            query, (self.table_name, record_id, self.source), fetch=True
        )
        return dict(results[0]) if results else None

    def get_pending_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get list of records pending processing"""
        query = """
            SELECT record_id, metadata, processing_priority
            FROM master.ingestion_status
            WHERE table_name = %s AND source = %s AND ingestion_status = 'pending'
            ORDER BY processing_priority DESC, created_at ASC
        """
        if limit:
            query += " LIMIT %s"

        params = (self.table_name, self.source)
        if limit:
            params = params + (limit,)

        results = self._execute_query(query, params, fetch=True)
        return [dict(row) for row in results]

    def get_failed_records(self) -> List[Dict[str, Any]]:
        """Get list of records that failed processing"""
        query = """
            SELECT record_id, failure_reason, retry_count, last_attempted_at, metadata
            FROM master.ingestion_status
            WHERE table_name = %s AND source = %s AND ingestion_status = 'failed'
            ORDER BY last_attempted_at DESC
        """
        results = self._execute_query(query, (self.table_name, self.source), fetch=True)
        return [dict(row) for row in results]

    def should_process_record(self, record_id: str) -> bool:
        """Check if a record should be processed"""
        status = self.get_record_status(record_id)
        if not status:
            return True  # New record, should process

        current_status = status["ingestion_status"]
        retry_count = status.get("retry_count", 0)

        # Don't process if completed
        if current_status == "completed":
            return False

        # Don't process if failed and exceeded max retries
        if current_status == "failed" and retry_count >= self.max_retry_attempts:
            return False

        # Process if pending or in_progress (allow retry of in_progress)
        return current_status in ("pending", "in_progress")

    def get_ingestion_stats(self) -> IngestionStats:
        """Get comprehensive ingestion statistics"""
        query = """
            SELECT
                COUNT(*) as total_records,
                COUNT(CASE WHEN ingestion_status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN ingestion_status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN ingestion_status = 'in_progress' THEN 1 END) as in_progress,
                COUNT(CASE WHEN ingestion_status = 'pending' THEN 1 END) as pending
            FROM master.ingestion_status
            WHERE table_name = %s AND source = %s AND ingestion_session_id = %s
        """
        results = self._execute_query(
            query, (self.table_name, self.source, self.session_id), fetch=True
        )
        if not results:
            return IngestionStats(source=self.source, table_name=self.table_name)

        stats = results[0]
        total = stats["total_records"]
        completed = stats["completed"]

        success_rate = (completed / total * 100) if total > 0 else 0.0

        return IngestionStats(
            total_records=total,
            completed=completed,
            failed=stats["failed"],
            in_progress=stats["in_progress"],
            pending=stats["pending"],
            success_rate=success_rate,
            source=self.source,
            table_name=self.table_name,
        )

    def reset_session(self, session_id: Optional[str] = None):
        """Reset all records for a session to pending status"""
        target_session = session_id or self.session_id

        query = """
            UPDATE master.ingestion_status
            SET ingestion_status = 'pending',
                retry_count = 0,
                failure_reason = NULL,
                completed_at = NULL,
                updated_at = now()
            WHERE table_name = %s AND source = %s AND ingestion_session_id = %s
        """
        self._execute_query(query, (self.table_name, self.source, target_session))
        self._commit()

    def cleanup_old_sessions(self, days_old: int = 30):
        """Remove ingestion status records older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)

        query = """
            DELETE FROM master.ingestion_status
            WHERE table_name = %s AND source = %s AND updated_at < %s
              AND ingestion_status IN ('completed', 'failed')
        """
        self._execute_query(query, (self.table_name, self.source, cutoff_date))
        self._commit()

    def close(self):
        """Clean up database connections"""
        if self._db_cursor:
            self._db_cursor.close()
        if self._db_connection:
            self._db_connection.close()


# Utility functions for CLI usage
def get_ingestion_status(
    db_config: Dict[str, Any],
    table_name: str,
    source: str,
    session_id: Optional[str] = None,
) -> IngestionStats:
    """Get ingestion status for a specific table/source"""
    tracker = GenericIngestionTracker(
        db_config, table_name, "record_id", source, session_id
    )
    try:
        return tracker.get_ingestion_stats()
    finally:
        tracker.close()


def reset_ingestion_status(
    db_config: Dict[str, Any],
    table_name: str,
    source: str,
    session_id: Optional[str] = None,
):
    """Reset ingestion status for a table/source"""
    tracker = GenericIngestionTracker(
        db_config, table_name, "record_id", source, session_id
    )
    try:
        tracker.reset_session(session_id)
        print(f"Reset ingestion status for {table_name} ({source})")
    finally:
        tracker.close()


def cleanup_old_ingestion_state(
    db_config: Dict[str, Any], table_name: str, source: str, days_old: int = 30
):
    """Clean up old ingestion state for a table/source"""
    tracker = GenericIngestionTracker(db_config, table_name, "record_id", source)
    try:
        tracker.cleanup_old_sessions(days_old)
        print(f"Cleaned up {table_name} ({source}) entries older than {days_old} days")
    finally:
        tracker.close()
