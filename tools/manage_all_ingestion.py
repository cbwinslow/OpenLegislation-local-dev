#!/usr/bin/env python3
"""
Universal Ingestion Manager for OpenLegislation

Central command-line tool for managing all data ingestion processes with resume capability.
Supports multiple data sources and provides unified status reporting and control.

Features:
- Manage ingestion for any table/data source
- Resume capability across all ingestion types
- Status reporting and monitoring
- Cleanup and reset utilities
- Parallel ingestion coordination

Usage:
    python3 tools/manage_all_ingestion.py --status
    python3 tools/manage_all_ingestion.py --run federal_members --api-key KEY
    python3 tools/manage_all_ingestion.py --reset govinfo_bills
    python3 tools/manage_all_ingestion.py --cleanup 30
"""

import argparse
import importlib
import json
import sys
from typing import Dict, Any, List, Optional

from settings import settings
from generic_ingestion_tracker import (
    get_ingestion_status,
    reset_ingestion_status,
    cleanup_old_ingestion_state,
    list_ingestion_sessions
)


class IngestionManager:
    """Manages multiple ingestion processes"""

    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        self.db_config = db_config or settings.db_config
        self.ingestion_types = self._discover_ingestion_types()

    def _discover_ingestion_types(self) -> Dict[str, Dict[str, Any]]:
        """Discover available ingestion types from the codebase"""
        # Define known ingestion types
        ingestion_types = {
            'federal_members': {
                'module': 'ingest_federal_members',
                'class': 'CongressMemberIngestor',
                'description': 'Federal member data from Congress.gov API',
                'table': 'master.federal_person',
                'source': 'congress_api'
            },
            'govinfo_bills': {
                'module': 'govinfo_bill_ingestion',  # To be created
                'class': 'GovInfoBillIngestor',
                'description': 'Bill data from GovInfo XML files',
                'table': 'master.bill',
                'source': 'govinfo',
                'default_kwargs': {
                    'xml_dir': getattr(settings, 'govinfo_xml_dir', 'staging/govinfo/bills')
                }
            },
            'govinfo_agendas': {
                'module': 'govinfo.agenda_ingestion',
                'class': 'GovInfoAgendaIngestor',
                'description': 'Agenda info/vote addenda from GovInfo JSON',
                'table': 'master.agenda',
                'source': 'govinfo_agenda',
                'default_kwargs': {
                    'agenda_dir': getattr(settings, 'govinfo_agenda_dir', 'staging/govinfo/agendas')
                }
            },
            'govinfo_calendars': {
                'module': 'govinfo.calendar_ingestion',
                'class': 'GovInfoCalendarIngestor',
                'description': 'Calendar active lists and supplements from GovInfo JSON',
                'table': 'master.calendar',
                'source': 'govinfo_calendar',
                'default_kwargs': {
                    'calendar_dir': getattr(settings, 'govinfo_calendar_dir', 'staging/govinfo/calendars')
                }
            },
            'member_data': {
                'module': 'member_data_ingestion',
                'class': 'MemberDataIngestor',
                'description': 'Member/person/session-member JSON payloads',
                'table': 'public.session_member',
                'source': 'member_data',
                'default_kwargs': {
                    'json_dir': getattr(settings, 'member_json_dir', 'staging/members')
                }
            },
            'bill_votes': {
                'module': 'bill_vote_ingestion',
                'class': 'BillVoteIngestor',
                'description': 'Bill vote metadata and roll calls',
                'table': 'master.bill_amendment_vote_info',
                'source': 'bill_votes',
                'default_kwargs': {
                    'json_dir': getattr(settings, 'vote_json_dir', 'staging/govinfo/votes')
                }
            },
            'bill_status': {
                'module': 'bill_status_ingestion',
                'class': 'BillStatusIngestor',
                'description': 'Bill milestone/status history',
                'table': 'master.bill_milestone',
                'source': 'bill_status',
                'default_kwargs': {
                    'json_dir': getattr(settings, 'bill_status_json_dir', 'staging/govinfo/status')
                }
            },
            # Add more as they are implemented
        }
        return ingestion_types

    def get_available_types(self) -> List[str]:
        """Get list of available ingestion types"""
        return list(self.ingestion_types.keys())

    def get_ingestion_info(self, ingestion_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific ingestion type"""
        return self.ingestion_types.get(ingestion_type)

    def run_ingestion(self, ingestion_type: str, **kwargs) -> bool:
        """Run a specific ingestion process"""
        info = self.get_ingestion_info(ingestion_type)
        if not info:
            print(f"Unknown ingestion type: {ingestion_type}")
            return False

        try:
            # Import the module dynamically
            module = importlib.import_module(f"tools.{info['module']}")
            ingestor_class = getattr(module, info['class'])

            # Create and run the ingestor
            default_kwargs = info.get('default_kwargs', {})
            merged_kwargs = {**default_kwargs, **kwargs}
            ingestor = ingestor_class(**merged_kwargs)
            ingestor.run()
            return True

        except ImportError as e:
            print(f"Cannot import {info['module']}: {e}")
            print("Make sure the ingestion module is implemented")
            return False
        except Exception as e:
            print(f"Error running {ingestion_type}: {e}")
            return False

    def get_status(self, ingestion_type: Optional[str] = None) -> Dict[str, Any]:
        """Get status for ingestion type(s)"""
        if ingestion_type:
            info = self.get_ingestion_info(ingestion_type)
            if not info:
                return {'error': f'Unknown ingestion type: {ingestion_type}'}

            stats = get_ingestion_status(self.db_config, info['table'], info['source'])
            return {
                'type': ingestion_type,
                'description': info['description'],
                'table': info['table'],
                'source': info['source'],
                'stats': stats
            }
        else:
            # Get status for all types
            all_status = {}
            for ing_type, info in self.ingestion_types.items():
                try:
                    stats = get_ingestion_status(self.db_config, info['table'], info['source'])
                    all_status[ing_type] = {
                        'description': info['description'],
                        'stats': stats
                    }
                except Exception as e:
                    all_status[ing_type] = {'error': str(e)}

            return all_status

    def reset_ingestion(self, ingestion_type: str, session_id: Optional[str] = None) -> bool:
        """Reset ingestion status for a type"""
        info = self.get_ingestion_info(ingestion_type)
        if not info:
            print(f"Unknown ingestion type: {ingestion_type}")
            return False

        try:
            reset_ingestion_status(self.db_config, info['table'], info['source'], session_id)
            print(f"Reset {ingestion_type} ingestion status")
            return True
        except Exception as e:
            print(f"Error resetting {ingestion_type}: {e}")
            return False

    def cleanup_old_data(self, days_old: int = 30, ingestion_type: Optional[str] = None) -> bool:
        """Clean up old ingestion data"""
        try:
            if ingestion_type:
                info = self.get_ingestion_info(ingestion_type)
                if not info:
                    print(f"Unknown ingestion type: {ingestion_type}")
                    return False
                cleanup_old_ingestion_state(self.db_config, info['table'], info['source'], days_old)
                print(f"Cleaned up {ingestion_type} data older than {days_old} days")
            else:
                # Clean up all types
                for ing_type, info in self.ingestion_types.items():
                    try:
                        cleanup_old_ingestion_state(self.db_config, info['table'], info['source'], days_old)
                        print(f"Cleaned up {ing_type}")
                    except Exception as e:
                        print(f"Error cleaning up {ing_type}: {e}")
                print(f"Cleaned up all ingestion data older than {days_old} days")
            return True
        except Exception as e:
            print(f"Error during cleanup: {e}")
            return False

    def list_sessions(self, ingestion_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List ingestion sessions"""
        if ingestion_type:
            info = self.get_ingestion_info(ingestion_type)
            if not info:
                return []

            # Filter sessions by table/source
            all_sessions = list_ingestion_sessions(self.db_config)
            filtered_sessions = [
                session for session in all_sessions
                if session.get('table_name') == info['table'] and session.get('source') == info['source']
            ]
            return filtered_sessions
        else:
            return list_ingestion_sessions(self.db_config)


def print_status(status_data: Dict[str, Any], verbose: bool = False):
    """Print formatted status information"""
    if 'error' in status_data:
        print(f"Error: {status_data['error']}")
        return

    if 'type' in status_data:
        # Single type status
        print(f"\n=== {status_data['type'].upper()} INGESTION STATUS ===")
        print(f"Description: {status_data['description']}")
        print(f"Table: {status_data['table']}")
        print(f"Source: {status_data['source']}")

        stats = status_data['stats']
        print(f"Total Records: {stats.total_records}")
        print(f"Completed: {stats.completed}")
        print(f"Failed: {stats.failed}")
        print(f"In Progress: {stats.in_progress}")
        print(f"Pending: {stats.pending}")
        print(f"Success Rate: {stats.success_rate:.1f}%")
    else:
        # All types status
        print("\n=== ALL INGESTION STATUS ===")
        for ing_type, data in status_data.items():
            if 'error' in data:
                print(f"{ing_type}: ERROR - {data['error']}")
            else:
                stats = data['stats']
                status_line = f"{ing_type}: {stats.completed}/{stats.total_records} completed"
                if stats.failed > 0:
                    status_line += f" ({stats.failed} failed)"
                if stats.in_progress > 0:
                    status_line += f" ({stats.in_progress} in progress)"
                print(status_line)


def print_sessions(sessions: List[Dict[str, Any]]):
    """Print formatted session information"""
    if not sessions:
        print("No ingestion sessions found.")
        return

    print("\n=== INGESTION SESSIONS ===")
    print(f"{'Session ID':<40} {'Type':<15} {'Source':<12} {'Total':<6} {'Done':<6} {'Fail':<6} {'Last Updated'}")
    print("-" * 100)

    for session in sessions:
        session_id = session['ingestion_session_id'][:38] + "..." if len(session['ingestion_session_id']) > 38 else session['ingestion_session_id']
        table_name = session.get('table_name', 'unknown')[:14]
        source = session.get('source', 'unknown')[:11]
        last_updated = session['last_updated'].strftime('%Y-%m-%d %H:%M') if session['last_updated'] else 'N/A'

        print(f"{session_id:<40} {table_name:<15} {source:<12} {session['total_members']:<6} {session['completed']:<6} {session['failed']:<6} {last_updated}")


def main():
    parser = argparse.ArgumentParser(description='Universal Ingestion Manager for OpenLegislation')
    parser.add_argument('--db-config', help='Database config JSON file')

    # Commands
    parser.add_argument('--status', nargs='?', const='all', help='Show ingestion status (optionally specify type)')
    parser.add_argument('--run', help='Run specific ingestion type')
    parser.add_argument('--reset', help='Reset ingestion status for type')
    parser.add_argument('--cleanup', type=int, metavar='DAYS', help='Clean up data older than DAYS')
    parser.add_argument('--list-sessions', nargs='?', const='all', help='List ingestion sessions (optionally filter by type)')
    parser.add_argument('--types', action='store_true', help='List available ingestion types')

    # Ingestion-specific args
    parser.add_argument('--api-key', help='API key for ingestion processes')
    parser.add_argument('--session-id', help='Specific session ID')
    parser.add_argument('--limit', type=int, help='Limit records to process')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh instead of resuming')
    parser.add_argument('--no-progress', action='store_true', help='Disable progress reporting')
    parser.add_argument('--xml-dir', help='Override XML directory for applicable ingestors')
    parser.add_argument('--json-dir', help='Override JSON directory for applicable ingestors')

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

    manager = IngestionManager(db_config)

    # Execute commands
    try:
        if args.types:
            print("Available ingestion types:")
            for ing_type, info in manager.ingestion_types.items():
                print(f"  {ing_type}: {info['description']}")

        elif args.status:
            if args.status == 'all':
                status = manager.get_status()
            else:
                status = manager.get_status(args.status)
            print_status(status)

        elif args.run:
            kwargs = {
                'session_id': args.session_id,
                'enable_progress': not args.no_progress
            }
            if args.api_key:
                kwargs['api_key'] = args.api_key
            if args.xml_dir:
                kwargs['xml_dir'] = args.xml_dir
            if args.json_dir:
                # Determine parameter name based on ingestion type
                if args.run == 'govinfo_agendas':
                    kwargs['agenda_dir'] = args.json_dir
                elif args.run == 'govinfo_calendars':
                    kwargs['calendar_dir'] = args.json_dir
                else:
                    kwargs['json_dir'] = args.json_dir
            if args.no_resume:
                kwargs['resume'] = False
                kwargs['reset'] = True
            if args.limit:
                kwargs['limit'] = args.limit

            success = manager.run_ingestion(args.run, **kwargs)
            sys.exit(0 if success else 1)

        elif args.reset:
            success = manager.reset_ingestion(args.reset, args.session_id)
            sys.exit(0 if success else 1)

        elif args.cleanup:
            success = manager.cleanup_old_data(args.cleanup, args.reset if args.reset else None)
            sys.exit(0 if success else 1)

        elif args.list_sessions:
            if args.list_sessions == 'all':
                sessions = manager.list_sessions()
            else:
                sessions = manager.list_sessions(args.list_sessions)
            print_sessions(sessions)

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
