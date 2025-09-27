#!/usr/bin/env python3
"""
Ingestion State Management Utility

Command-line tool for managing federal member ingestion state.
Provides status reporting, reset functionality, and cleanup utilities.

Usage:
    python3 tools/manage_ingestion_state.py --status
    python3 tools/manage_ingestion_state.py --reset --session-id <session>
    python3 tools/manage_ingestion_state.py --cleanup 30
    python3 tools/manage_ingestion_state.py --list-sessions
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any

from settings import settings
from member_ingestion_tracker import (
    get_ingestion_status,
    reset_ingestion_status,
    cleanup_old_ingestion_state,
    list_ingestion_sessions
)


def print_status(status_info: Dict[str, Any]):
    """Print formatted ingestion status"""
    stats = status_info['stats']

    print("
=== INGESTION STATUS ==="    print(f"Session ID: {status_info['session_id']}")
    print(f"Total Members: {stats.total_members}")
    print(f"Completed: {stats.completed}")
    print(f"Failed: {stats.failed}")
    print(f"In Progress: {stats.in_progress}")
    print(f"Pending: {stats.pending}")
    print(f"Success Rate: {stats.success_rate:.1f}%")

    if status_info['failed_members']:
        print(f"\nRecent Failures ({len(status_info['failed_members'])}):")
        for failure in status_info['failed_members'][:5]:
            print(f"  {failure['bioguide_id']}: {failure.get('failure_reason', 'Unknown error')}")

    if stats.total_members > 0:
        progress_pct = (stats.completed + stats.failed) / stats.total_members * 100
        print(f"\nOverall Progress: {progress_pct:.1f}%")


def print_sessions(sessions: list):
    """Print formatted session list"""
    if not sessions:
        print("No ingestion sessions found.")
        return

    print("
=== INGESTION SESSIONS ==="    print(f"{'Session ID':<40} {'Total':<6} {'Done':<6} {'Fail':<6} {'Pending':<6} {'Last Updated'}")
    print("-" * 90)

    for session in sessions:
        session_id = session['ingestion_session_id'][:38] + "..." if len(session['ingestion_session_id']) > 38 else session['ingestion_session_id']
        last_updated = session['last_updated'].strftime('%Y-%m-%d %H:%M') if session['last_updated'] else 'N/A'

        print(f"{session_id:<40} {session['total_members']:<6} {session['completed']:<6} {session['failed']:<6} {session['pending']:<6} {last_updated}")


def main():
    parser = argparse.ArgumentParser(description='Manage federal member ingestion state')
    parser.add_argument('--db-config', help='Database config JSON file (overrides .env settings)')
    parser.add_argument('--session-id', help='Specific session ID to operate on')

    # Commands
    parser.add_argument('--status', action='store_true', help='Show current ingestion status')
    parser.add_argument('--reset', action='store_true', help='Reset ingestion status to pending')
    parser.add_argument('--cleanup', type=int, metavar='DAYS', help='Clean up entries older than DAYS')
    parser.add_argument('--cleanup-session', action='store_true', help='Clean up specific session (requires --session-id)')
    parser.add_argument('--list-sessions', action='store_true', help='List all ingestion sessions')

    args = parser.parse_args()

    # Load database config
    db_config = None
    if args.db_config:
        try:
            with open(args.db_config, 'r') as f:
                db_config = json.load(f)
        except Exception as e:
            print(f"Error loading database config: {e}")
            sys.exit(1)
    else:
        db_config = settings.db_config

    # Execute commands
    try:
        if args.status:
            status_info = get_ingestion_status(db_config, args.session_id)
            print_status(status_info)

        elif args.reset:
            reset_ingestion_status(db_config, args.session_id)
            session_desc = f" for session {args.session_id}" if args.session_id else ""
            print(f"✓ Ingestion status reset{session_desc}")

        elif args.cleanup:
            cleanup_old_ingestion_state(db_config, args.cleanup, args.session_id)
            target_desc = f"session {args.session_id}" if args.session_id else f"entries older than {args.cleanup} days"
            print(f"✓ Cleaned up {target_desc}")

        elif args.cleanup_session:
            if not args.session_id:
                print("Error: --cleanup-session requires --session-id")
                sys.exit(1)
            cleanup_old_ingestion_state(db_config, session_id=args.session_id)
            print(f"✓ Cleaned up session {args.session_id}")

        elif args.list_sessions:
            sessions = list_ingestion_sessions(db_config)
            print_sessions(sessions)

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()</parameter>
