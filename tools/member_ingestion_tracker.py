#!/usr/bin/env python3
"""
Member Ingestion Tracker for OpenLegislation Federal Member Data Ingestion

Tracks ingestion progress and enables resume capability for federal member data.
Similar to DownloadResumeManager but adapted for member processing workflow.

Features:
- Tracks processing status by bioguide_id (pending/in_progress/completed/failed)
- Persistent state storage in database
- Resume capability to skip already processed members
- Progress reporting and statistics
- Session-based tracking for multiple ingestion runs

Usage:
    from member_ingestion_tracker import MemberIngestionTracker

    tracker = MemberIngestionTracker(db_config)
    tracker.initialize_members(member_list)  # Mark all as pending

    # During processing
    tracker.mark_in_progress(bioguide_id)
    # ... process member ...
    tracker.mark_completed(bioguide_id)

    # For resume
    pending = tracker.get_pending_members()
    # Process only pending members
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import psycopg2
import psycopg2.extras


@dataclass
class IngestionStats:
    """Statistics for ingestion progress"""
    total_members: int = 0
    completed: int = 0
    failed: int = 0
    in_progress: int = 0
    pending: int = 0
    success_rate: float = 0.0
    average_processing_time: Optional[float] = None


class MemberIngestionTracker:
    """Tracks federal member ingestion status and enables resume capability"""

    def __init__(self, db_config: Dict[str, Any], session_id: Optional[str] = None,
                 max_retry_attempts: int = 3):
        self.db_config = db_config
        self.session_id = session_id or str(uuid.uuid4())
        self.max_retry_attempts = max_retry_attempts
        self._db_connection = None
        self._db_cursor = None

    def _get_db_connection(self):
        """Get database connection with proper cursor"""
        if not self._db_connection or self._db_connection.closed:
            self._db_connection = psycopg2.connect(**self.db_config)
            self._db_cursor = self._db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        return self._db_connection, self._db_cursor

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

    def initialize_members(self, member_list: List[Dict[str, Any]], reset_existing: bool = False):
        """Initialize ingestion status for a list of members

        Args:
            member_list: List of member dicts with 'bioguideId' keys
            reset_existing: If True, reset status of existing members to pending
        """
        bioguide_ids = [member.get('bioguideId') for member in member_list if member.get('bioguideId')]

        if not bioguide_ids:
            return

        # Create ingestion records for new members
        values = [(bioguide_id, self.session_id) for bioguide_id in bioguide_ids]
        value_placeholders = ','.join(['(%s, %s)'] * len(values))

        query = f"""
            INSERT INTO master.federal_member_ingestion_status
            (bioguide_id, ingestion_session_id, ingestion_status, created_at, updated_at)
            VALUES {value_placeholders}
            ON CONFLICT (bioguide_id) DO NOTHING
        """

        flattened_values = [item for sublist in values for item in sublist]
        self._execute_query(query, tuple(flattened_values))

        # Optionally reset existing members
        if reset_existing:
            reset_query = """
                UPDATE master.federal_member_ingestion_status
                SET ingestion_status = 'pending',
                    retry_count = 0,
                    failure_reason = NULL,
                    updated_at = now()
                WHERE bioguide_id = ANY(%s) AND ingestion_status IN ('failed', 'completed')
            """
            self._execute_query(reset_query, (bioguide_ids,))

        self._commit()

    def mark_in_progress(self, bioguide_id: str):
        """Mark a member as currently being processed"""
        query = """
            UPDATE master.federal_member_ingestion_status
            SET ingestion_status = 'in_progress',
                last_attempted_at = now(),
                updated_at = now()
            WHERE bioguide_id = %s
        """
        self._execute_query(query, (bioguide_id,))
        self._commit()

    def mark_completed(self, bioguide_id: str):
        """Mark a member as successfully processed"""
        query = """
            UPDATE master.federal_member_ingestion_status
            SET ingestion_status = 'completed',
                completed_at = now(),
                updated_at = now(),
                failure_reason = NULL
            WHERE bioguide_id = %s
        """
        self._execute_query(query, (bioguide_id,))
        self._commit()

    def mark_failed(self, bioguide_id: str, failure_reason: str = None):
        """Mark a member as failed to process"""
        # Increment retry count
        query = """
            UPDATE master.federal_member_ingestion_status
            SET ingestion_status = CASE
                    WHEN retry_count >= %s THEN 'failed'
                    ELSE 'pending'
                END,
                retry_count = retry_count + 1,
                failure_reason = %s,
                last_attempted_at = now(),
                updated_at = now()
            WHERE bioguide_id = %s
        """
        self._execute_query(query, (self.max_retry_attempts, failure_reason, bioguide_id))
        self._commit()

    def get_member_status(self, bioguide_id: str) -> Optional[Dict[str, Any]]:
        """Get current status for a specific member"""
        query = """
            SELECT * FROM master.federal_member_ingestion_status
            WHERE bioguide_id = %s
        """
        results = self._execute_query(query, (bioguide_id,), fetch=True)
        return dict(results[0]) if results else None

    def get_pending_members(self, limit: Optional[int] = None) -> List[str]:
        """Get list of members pending processing"""
        query = """
            SELECT bioguide_id
            FROM master.federal_member_ingestion_status
            WHERE ingestion_status = 'pending'
            ORDER BY processing_order ASC NULLS LAST, created_at ASC
        """
        if limit:
            query += " LIMIT %s"

        params = (limit,) if limit else ()
        results = self._execute_query(query, params, fetch=True)
        return [row['bioguide_id'] for row in results]

    def get_failed_members(self) -> List[Dict[str, Any]]:
        """Get list of members that failed processing"""
        query = """
            SELECT bioguide_id, failure_reason, retry_count, last_attempted_at
            FROM master.federal_member_ingestion_status
            WHERE ingestion_status = 'failed'
            ORDER BY last_attempted_at DESC
        """
        results = self._execute_query(query, fetch=True)
        return [dict(row) for row in results]

    def should_process_member(self, bioguide_id: str) -> bool:
        """Check if a member should be processed (not completed or failed permanently)"""
        status = self.get_member_status(bioguide_id)
        if not status:
            return True  # New member, should process

        current_status = status['ingestion_status']
        retry_count = status.get('retry_count', 0)

        # Don't process if completed
        if current_status == 'completed':
            return False

        # Don't process if failed and exceeded max retries
        if current_status == 'failed' and retry_count >= self.max_retry_attempts:
            return False

        # Process if pending or in_progress (allow retry of in_progress)
        return current_status in ('pending', 'in_progress')

    def get_ingestion_stats(self) -> IngestionStats:
        """Get comprehensive ingestion statistics"""
        query = """
            SELECT
                COUNT(*) as total_members,
                COUNT(CASE WHEN ingestion_status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN ingestion_status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN ingestion_status = 'in_progress' THEN 1 END) as in_progress,
                COUNT(CASE WHEN ingestion_status = 'pending' THEN 1 END) as pending
            FROM master.federal_member_ingestion_status
            WHERE ingestion_session_id = %s
        """
        results = self._execute_query(query, (self.session_id,), fetch=True)
        if not results:
            return IngestionStats()

        stats = results[0]
        total = stats['total_members']
        completed = stats['completed']

        success_rate = (completed / total * 100) if total > 0 else 0.0

        return IngestionStats(
            total_members=total,
            completed=completed,
            failed=stats['failed'],
            in_progress=stats['in_progress'],
            pending=stats['pending'],
            success_rate=success_rate
        )

    def reset_session(self, session_id: Optional[str] = None):
        """Reset all members for a session to pending status"""
        target_session = session_id or self.session_id

        query = """
            UPDATE master.federal_member_ingestion_status
            SET ingestion_status = 'pending',
                retry_count = 0,
                failure_reason = NULL,
                completed_at = NULL,
                updated_at = now()
            WHERE ingestion_session_id = %s
        """
        self._execute_query(query, (target_session,))
        self._commit()

    def cleanup_old_sessions(self, days_old: int = 30):
        """Remove ingestion status records older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)

        query = """
            DELETE FROM master.federal_member_ingestion_status
            WHERE updated_at < %s AND ingestion_status IN ('completed', 'failed')
        """
        self._execute_query(query, (cutoff_date,))
        self._commit()

    def close(self):
        """Clean up database connections"""
        if self._db_cursor:
            self._db_cursor.close()
        if self._db_connection:
            self._db_connection.close()


# Convenience functions for CLI usage
def get_ingestion_status(db_config: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive ingestion status"""
    tracker = MemberIngestionTracker(db_config, session_id)
    try:
        stats = tracker.get_ingestion_stats()
        failed_members = tracker.get_failed_members()

        return {
            'stats': stats,
            'failed_members': failed_members[:10],  # First 10 failed members
            'total_failed': len(failed_members),
            'session_id': tracker.session_id
        }
    finally:
        tracker.close()


def reset_ingestion_status(db_config: Dict[str, Any], session_id: Optional[str] = None):
    """Reset ingestion status for a session"""
    tracker = MemberIngestionTracker(db_config, session_id)
    try:
        tracker.reset_session(session_id)
        print(f"Reset ingestion status for session: {tracker.session_id}")
    finally:
        tracker.close()


def list_ingestion_sessions(db_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List all ingestion sessions with statistics"""
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = """
            SELECT
                ingestion_session_id,
                COUNT(*) as total_members,
                COUNT(CASE WHEN ingestion_status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN ingestion_status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN ingestion_status = 'pending' THEN 1 END) as pending,
                MIN(created_at) as session_start,
                MAX(updated_at) as last_updated
            FROM master.federal_member_ingestion_status
            GROUP BY ingestion_session_id
            ORDER BY last_updated DESC
        """

        cursor.execute(query)
        results = cursor.fetchall()
        return [dict(row) for row in results]

    except Exception as e:
        print(f"Error listing sessions: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    # end of list_ingestion_sessions