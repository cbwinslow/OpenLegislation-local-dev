#!/usr/bin/env python3
"""
Enhanced Ingestion Orchestrator for OpenLegislation

Builds on the existing BaseIngestionProcess framework to provide:
- Automatic migration checking and execution
- User-friendly parameter configuration
- Unified interface for all data sources
- Migration status tracking

Usage:
    # Interactive mode
    python3 tools/enhanced_ingestion_orchestrator.py --interactive

    # Run specific data source
    python3 tools/enhanced_ingestion_orchestrator.py --source congress_api --start-congress 118

    # Check migrations
    python3 tools/enhanced_ingestion_orchestrator.py --check-migrations

    # Run all with defaults
    python3 tools/enhanced_ingestion_orchestrator.py --all
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import psycopg2
from psycopg2.extras import DictCursor
from dataclasses import dataclass, asdict

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.config.settings import settings
from tools.ingestion.core.generic_ingestion_tracker import get_ingestion_status


@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    name: str
    description: str
    script_path: str
    table_name: str
    source_id: str
    migration_files: Optional[List[str]] = None
    default_params: Optional[Dict[str, Any]] = None
    required_params: Optional[List[str]] = None
    optional_params: Optional[List[str]] = None
    param_help: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.migration_files is None:
            self.migration_files = []
        if self.default_params is None:
            self.default_params = {}
        if self.required_params is None:
            self.required_params = []
        if self.optional_params is None:
            self.optional_params = []
        if self.param_help is None:
            self.param_help = {}


class EnhancedIngestionOrchestrator:
    """Enhanced ingestion orchestrator with migration management"""

    def __init__(self, db_config: Optional[Dict] = None):
        self.db_config = db_config or settings.db_config
        self.data_sources = self._initialize_data_sources()

    def _initialize_data_sources(self) -> Dict[str, DataSourceConfig]:
        """Initialize all available data sources with their configurations"""
        return {
            'congress_api': DataSourceConfig(
                name='Congress API',
                description='Federal legislation and committee data from congress.gov API',
                script_path='tools/ingestion/core/ingest_federal_data.py',
                table_name='master.bill',  # Primary table for tracking
                source_id='congress_api',
                migration_files=[
                    'src/main/resources/sql/migrations/V20250921.0004__federal_member_schema.sql',
                    'src/main/resources/sql/migrations/V20250921.0005__federal_member_ingestion_tracking.sql'
                ],
                default_params={
                    'type': 'bills',  # or 'committees'
                    'start_congress': 118,
                    'batch_size': 250
                },
                required_params=[],
                optional_params=['type', 'start_congress', 'batch_size', 'dry-run'],
                param_help={
                    'type': 'Data type to ingest: bills or committees',
                    'start_congress': 'Starting congress number (works backwards from here)',
                    'batch_size': 'Number of records per batch',
                    'dry-run': 'Simulate without making changes'
                }
            ),

            'federal_members': DataSourceConfig(
                name='Federal Members',
                description='Federal member data from congress.gov API',
                script_path='tools/ingestion/members/ingest_federal_members.py',
                table_name='master.federal_person',
                source_id='congress_api',
                migration_files=[
                    'src/main/resources/sql/migrations/V20250921.0004__federal_member_schema.sql',
                    'src/main/resources/sql/migrations/V20250921.0005__federal_member_ingestion_tracking.sql'
                ],
                default_params={},
                required_params=[],
                optional_params=['api-key', 'limit', 'no-resume', 'reset', 'dry-run'],
                param_help={
                    'api-key': 'Congress.gov API key (or set CONGRESS_API_KEY env var)',
                    'limit': 'Limit number of members to process',
                    'no-resume': 'Start fresh instead of resuming',
                    'reset': 'Reset ingestion status before starting'
                }
            ),

            'govinfo_bills': DataSourceConfig(
                name='GovInfo Bills',
                description='Bill data from GovInfo XML files',
                script_path='tools/ingestion/govinfo/govinfo_bill_ingestion.py',
                table_name='master.bill',
                source_id='govinfo',
                migration_files=[
                    'src/main/resources/sql/migrations/V20250921.0002__govinfo_bill_tables_expanded.sql'
                ],
                default_params={
                    'xml_dir': 'staging/govinfo/bills',
                    'patterns': ['BILLS-*.xml', 'BILLSTATUS-*.xml']
                },
                required_params=[],
                optional_params=['xml-dir', 'pattern', 'file', 'recursive', 'reset', 'limit'],
                param_help={
                    'xml-dir': 'Directory containing XML files',
                    'pattern': 'File patterns to match (default: BILLS-*.xml BILLSTATUS-*.xml)',
                    'file': 'Specific files to process',
                    'recursive': 'Search directories recursively',
                    'reset': 'Reset ingestion status',
                    'limit': 'Limit number of files to process'
                }
            ),

            'govinfo_agendas': DataSourceConfig(
                name='GovInfo Agendas',
                description='Committee agendas from GovInfo JSON files',
                script_path='tools/govinfo/agenda_ingestion.py',
                table_name='master.agenda',
                source_id='govinfo_agenda',
                migration_files=[],
                default_params={
                    'agenda_dir': 'staging/govinfo/agendas'
                },
                required_params=[],
                optional_params=['json-dir', 'reset', 'limit'],
                param_help={
                    'json-dir': 'Directory containing agenda JSON files',
                    'reset': 'Reset ingestion status',
                    'limit': 'Limit number of files to process'
                }
            ),

            'govinfo_calendars': DataSourceConfig(
                name='GovInfo Calendars',
                description='Calendar active lists from GovInfo JSON files',
                script_path='tools/govinfo/calendar_ingestion.py',
                table_name='master.calendar',
                source_id='govinfo_calendar',
                migration_files=[],
                default_params={
                    'calendar_dir': 'staging/govinfo/calendars'
                },
                required_params=[],
                optional_params=['json-dir', 'reset', 'limit'],
                param_help={
                    'json-dir': 'Directory containing calendar JSON files',
                    'reset': 'Reset ingestion status',
                    'limit': 'Limit number of files to process'
                }
            ),

            'member_data': DataSourceConfig(
                name='Member Data',
                description='Member/session data from JSON files',
                script_path='tools/ingestion/members/member_data_ingestion.py',
                table_name='public.session_member',
                source_id='member_data',
                migration_files=[],
                default_params={
                    'json_dir': 'staging/members'
                },
                required_params=[],
                optional_params=['json-dir', 'pattern', 'file', 'recursive', 'reset', 'limit'],
                param_help={
                    'json-dir': 'Directory containing member JSON files',
                    'pattern': 'File patterns to match (default: MEMBERS-*.json)',
                    'file': 'Specific files to process',
                    'recursive': 'Search directories recursively',
                    'reset': 'Reset ingestion status',
                    'limit': 'Limit number of files to process'
                }
            ),

            'bill_votes': DataSourceConfig(
                name='Bill Votes',
                description='Bill vote data from JSON files',
                script_path='tools/utilities/bill_vote_ingestion.py',
                table_name='master.bill_amendment_vote_info',
                source_id='bill_votes',
                migration_files=[],
                default_params={
                    'json_dir': 'staging/govinfo/votes'
                },
                required_params=[],
                optional_params=['json-dir', 'pattern', 'file', 'recursive', 'reset', 'limit'],
                param_help={
                    'json-dir': 'Directory containing vote JSON files',
                    'pattern': 'File patterns to match (default: VOTES-*.json)',
                    'file': 'Specific files to process',
                    'recursive': 'Search directories recursively',
                    'reset': 'Reset ingestion status',
                    'limit': 'Limit number of files to process'
                }
            ),

            'bill_status': DataSourceConfig(
                name='Bill Status',
                description='Bill status/milestone data from JSON files',
                script_path='tools/utilities/bill_status_ingestion.py',
                table_name='master.bill_milestone',
                source_id='bill_status',
                migration_files=[],
                default_params={
                    'json_dir': 'staging/govinfo/status'
                },
                required_params=[],
                optional_params=['json-dir', 'pattern', 'file', 'recursive', 'reset', 'limit'],
                param_help={
                    'json-dir': 'Directory containing status JSON files',
                    'pattern': 'File patterns to match (default: STATUS-*.json)',
                    'file': 'Specific files to process',
                    'recursive': 'Search directories recursively',
                    'reset': 'Reset ingestion status',
                    'limit': 'Limit number of files to process'
                }
            )
        }

    def get_db_connection(self) -> psycopg2.extensions.connection:
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")

    def check_migrations(self, source_names: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Check migration status for data sources"""
        if source_names is None:
            source_names = list(self.data_sources.keys())

        migration_status = {}

        with self.get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Check if migration table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'flyway_schema_history'
                    );
                """)
                result = cursor.fetchone()
                has_migration_table = result[0] if result else False

                if not has_migration_table:
                    print("WARNING: Migration table not found. Database may not be properly migrated.")
                    return {source: {'status': 'unknown', 'message': 'Migration table not found'} 
                           for source in source_names}

                # Get applied migrations
                cursor.execute("""
                    SELECT version, description, installed_on 
                    FROM public.flyway_schema_history 
                    ORDER BY installed_on DESC;
                """)
                applied_migrations = {row['version']: row for row in cursor.fetchall()}

                # Check each source's migrations
                for source_name in source_names:
                    if source_name not in self.data_sources:
                        migration_status[source_name] = {
                            'status': 'error',
                            'message': f'Unknown data source: {source_name}'
                        }
                        continue

                    source = self.data_sources[source_name]
                    source_status = {
                        'status': 'ok',
                        'applied': [],
                        'pending': [],
                        'missing': []
                    }

                    for migration_file in (source.migration_files or []):
                        if not os.path.exists(migration_file):
                            source_status['missing'].append(migration_file)
                            continue

                        # Extract version from filename
                        migration_version = os.path.basename(migration_file).split('__')[0]
                        
                        if migration_version in applied_migrations:
                            source_status['applied'].append({
                                'file': migration_file,
                                'version': migration_version,
                                'applied_at': applied_migrations[migration_version]['installed_on']
                            })
                        else:
                            source_status['pending'].append(migration_file)

                    if source_status['pending']:
                        source_status['status'] = 'pending'
                    if source_status['missing']:
                        source_status['status'] = 'error'

                    migration_status[source_name] = source_status

        return migration_status

    def run_migrations(self, source_names: Optional[List[str]] = None, dry_run: bool = False) -> bool:
        """Run pending migrations for data sources"""
        if source_names is None:
            source_names = list(self.data_sources.keys())

        migration_status = self.check_migrations(source_names)
        success = True

        for source_name in source_names:
            status = migration_status.get(source_name, {})
            
            if status.get('status') == 'error':
                print(f"❌ {source_name}: {status.get('message', 'Migration error')}")
                success = False
                continue

            pending = status.get('pending', [])
            if not pending:
                print(f"✅ {source_name}: No pending migrations")
                continue

            print(f"📋 {source_name}: {len(pending)} pending migrations")
            
            if dry_run:
                for migration in pending:
                    print(f"  Would apply: {migration}")
                continue

            # Apply migrations using psql
            for migration_file in pending:
                try:
                    print(f"  Applying: {migration_file}")
                    if self._apply_migration_file(migration_file):
                        print(f"  ✅ Applied: {migration_file}")
                    else:
                        print(f"  ❌ Failed: {migration_file}")
                        success = False
                        break
                except Exception as e:
                    print(f"  ❌ Error applying {migration_file}: {e}")
                    success = False
                    break

        return success

    def _apply_migration_file(self, migration_file: str) -> bool:
        """Apply a single migration file using psql"""
        try:
            # Build psql command
            cmd = [
                'psql',
                f'--host={self.db_config["host"]}',
                f'--port={self.db_config["port"]}',
                f'--username={self.db_config["user"]}',
                f'--dbname={self.db_config["database"]}',
                '--file=' + migration_file
            ]

            # Execute migration
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"    Migration output: {result.stderr}")
                return False

        except Exception as e:
            print(f"Migration failed: {e}")
            return False

    def validate_parameters(self, source_name: str, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate parameters for a data source"""
        if source_name not in self.data_sources:
            return False, [f"Unknown data source: {source_name}"]

        source = self.data_sources[source_name]
        errors = []

        # Check required parameters
        for required_param in (source.required_params or []):
            if required_param not in params or params[required_param] is None:
                errors.append(f"Missing required parameter: {required_param}")

        # Validate parameter values
        for param, value in params.items():
            if param == 'start_congress':
                if not isinstance(value, int) or value < 1 or value > 200:
                    errors.append(f"Invalid congress number: {value}")
            elif param == 'batch_size':
                if not isinstance(value, int) or value < 1:
                    errors.append(f"Invalid batch size: {value}")
            elif param.endswith('_dir'):
                if not os.path.exists(value):
                    errors.append(f"Directory does not exist: {value}")

        return len(errors) == 0, errors

    def get_ingestion_status(self, source_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get current ingestion status"""
        if source_names is None:
            source_names = list(self.data_sources.keys())

        status = {}
        for source_name in source_names:
            if source_name not in self.data_sources:
                continue
            
            source = self.data_sources[source_name]
            try:
                stats = get_ingestion_status(self.db_config, source.table_name, source.source_id)
                status[source_name] = {
                    'description': source.description,
                    'table': source.table_name,
                    'stats': stats
                }
            except Exception as e:
                status[source_name] = {
                    'description': source.description,
                    'error': str(e)
                }

        return status

    def run_ingestion(self, source_names: Optional[List[str]] = None, params: Optional[Dict[str, Any]] = None) -> bool:
        """Run ingestion for specified data sources"""
        if source_names is None:
            source_names = list(self.data_sources.keys())

        if params is None:
            params = {}

        # Check and run migrations first
        print("🔍 Checking migrations...")
        if not self.run_migrations(source_names):
            print("❌ Migration check failed. Aborting ingestion.")
            return False

        print("✅ Migrations are up to date.\n")

        # Validate parameters for each source
        for source_name in source_names:
            source_params = {**(self.data_sources[source_name].default_params or {}), **(params or {})}
            is_valid, errors = self.validate_parameters(source_name, source_params)
            if not is_valid:
                print(f"❌ {source_name}: Parameter validation failed")
                for error in errors:
                    print(f"   - {error}")
                return False

        # Run ingestion sequentially
        overall_success = True

        for source_name in source_names:
            source = self.data_sources[source_name]
            source_params = {**(source.default_params or {}), **(params or {})}

            print(f"🚀 Starting {source_name}: {source.description}")
            print(f"   Parameters: {json.dumps(source_params, indent=2)}")

            try:
                success = self._execute_ingestion_script(source, source_params)
                if success:
                    print(f"✅ {source_name} completed successfully")
                else:
                    print(f"❌ {source_name} failed")
                    overall_success = False
            except Exception as e:
                print(f"❌ {source_name} error: {e}")
                overall_success = False

            print()

        return overall_success

    def _execute_ingestion_script(self, source: DataSourceConfig, params: Dict[str, Any]) -> bool:
        """Execute a single ingestion script"""
        try:
            # Build command
            cmd = ['python3', source.script_path]
            
            # Add parameters as command line arguments
            for param, value in params.items():
                if value is not None:
                    # Only include parameters that the script supports
                    if (source.optional_params and param.replace('-', '_') not in source.optional_params):
                        continue
                        
                    # Convert parameter name to CLI format
                    cli_param = f'--{param.replace("_", "-")}'
                    
                    # Handle boolean flags
                    if isinstance(value, bool):
                        if value:
                            cmd.append(cli_param)
                    else:
                        cmd.extend([cli_param, str(value)])

            # Execute script
            print(f"   Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600 * 4  # 4 hour timeout
            )

            if result.returncode == 0:
                return True
            else:
                if result.stdout:
                    print(f"   Script output: {result.stdout}")
                if result.stderr:
                    print(f"   Script errors: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"   Script timed out after 4 hours")
            return False
        except Exception as e:
            print(f"   Script execution error: {e}")
            return False

    def interactive_mode(self):
        """Interactive configuration mode"""
        print("🎯 OpenLegislation Enhanced Ingestion Orchestrator - Interactive Mode")
        print("=" * 70)

        # Show available data sources
        print("\n📊 Available Data Sources:")
        for i, (name, config) in enumerate(self.data_sources.items(), 1):
            print(f"  {i}. {name}: {config.description}")

        # Select data sources
        while True:
            try:
                selection = input("\nSelect data sources (comma-separated numbers or 'all'): ").strip()
                if selection.lower() == 'all':
                    selected_sources = list(self.data_sources.keys())
                    break
                
                indices = [int(x.strip()) for x in selection.split(',')]
                source_names = list(self.data_sources.keys())
                selected_sources = [source_names[i-1] for i in indices if 1 <= i <= len(source_names)]
                
                if selected_sources:
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")

        print(f"\nSelected: {', '.join(selected_sources)}")

        # Configure parameters for each selected source
        final_params = {}
        for source_name in selected_sources:
            source = self.data_sources[source_name]
            print(f"\n⚙️  Configuring {source_name}:")
            
            source_params = (source.default_params or {}).copy()
            
            # Prompt for optional parameters
            for param in (source.optional_params or []):
                current_value = source_params.get(param, '')
                help_text = (source.param_help or {}).get(param, '')
                prompt = f"  {param} [{current_value}]"
                if help_text:
                    prompt += f" - {help_text}"
                prompt += ": "
                
                new_value = input(prompt).strip()
                if new_value:
                    # Convert to appropriate type
                    if param in ['reset', 'recursive', 'dry-run']:
                        source_params[param] = new_value.lower() in ['true', 'yes', 'y', '1']
                    elif param in ['start_congress', 'batch_size', 'limit']:
                        try:
                            source_params[param] = int(new_value)
                        except ValueError:
                            print(f"    Invalid number, keeping current value: {current_value}")
                    else:
                        source_params[param] = new_value

            final_params[source_name] = source_params

        # Show configuration summary
        print("\n📋 Configuration Summary:")
        for source_name, params in final_params.items():
            print(f"\n{source_name}:")
            for param, value in params.items():
                print(f"  {param}: {value}")

        # Confirm execution
        confirm = input("\n🚀 Start ingestion with this configuration? (y/N): ").strip().lower()
        if confirm == 'y':
            # Use the first source's parameters as global defaults (they might differ)
            global_params = {}
            for params in final_params.values():
                global_params.update(params)
            
            success = self.run_ingestion(selected_sources, global_params)
            if success:
                print("\n🎉 Ingestion completed successfully!")
            else:
                print("\n❌ Ingestion encountered errors.")
        else:
            print("Ingestion cancelled.")

    def list_sources(self):
        """List all available data sources with details"""
        print("📊 Available Data Sources:")
        print("=" * 70)
        
        for name, config in self.data_sources.items():
            print(f"\n{name}:")
            print(f"  Description: {config.description}")
            print(f"  Script: {config.script_path}")
            print(f"  Table: {config.table_name}")
            print(f"  Default Parameters:")
            for param, value in (config.default_params or {}).items():
                print(f"    {param}: {value}")
            if config.optional_params:
                print(f"  Optional Parameters:")
                for param in config.optional_params:
                    help_text = (config.param_help or {}).get(param, '')
                    print(f"    {param}: {help_text}")


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Ingestion Orchestrator for OpenLegislation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python3 tools/enhanced_ingestion_orchestrator.py --interactive

  # Check migrations
  python3 tools/enhanced_ingestion_orchestrator.py --check-migrations

  # Run specific source
  python3 tools/enhanced_ingestion_orchestrator.py --source congress_api --start-congress 118

  # Run all sources
  python3 tools/enhanced_ingestion_orchestrator.py --all

  # List sources
  python3 tools/enhanced_ingestion_orchestrator.py --list-sources
        """
    )

    # Main actions
    parser.add_argument('--all', action='store_true', help='Run all data sources')
    parser.add_argument('--source', action='append', help='Specific data source(s) to run')
    parser.add_argument('--check-migrations', action='store_true', help='Check migration status')
    parser.add_argument('--run-migrations', action='store_true', help='Run pending migrations')
    parser.add_argument('--dry-run-migrations', action='store_true', help='Show pending migrations without applying')
    parser.add_argument('--status', action='store_true', help='Show ingestion status')
    parser.add_argument('--interactive', action='store_true', help='Interactive configuration mode')
    parser.add_argument('--list-sources', action='store_true', help='List available data sources')

    # Common parameters
    parser.add_argument('--start-congress', type=int, help='Starting congress number')
    parser.add_argument('--batch-size', type=int, help='Batch size for processing')
    parser.add_argument('--api-key', help='API key for external services')
    parser.add_argument('--xml-dir', help='XML files directory')
    parser.add_argument('--json-dir', help='JSON files directory')
    parser.add_argument('--agenda-dir', help='Agenda files directory')
    parser.add_argument('--calendar-dir', help='Calendar files directory')
    parser.add_argument('--pattern', action='append', help='File patterns to match')
    parser.add_argument('--file', action='append', help='Specific files to process')
    parser.add_argument('--recursive', action='store_true', help='Search directories recursively')
    parser.add_argument('--reset', action='store_true', help='Reset ingestion status')
    parser.add_argument('--limit', type=int, help='Limit number of records/files to process')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without making changes')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh instead of resuming')

    # Configuration
    parser.add_argument('--db-config', help='Database configuration JSON file')

    args = parser.parse_args()

    # Load custom database config if provided
    db_config = None
    if args.db_config:
        try:
            with open(args.db_config, 'r') as f:
                db_config = json.load(f)
        except Exception as e:
            print(f"Error loading database config: {e}")
            sys.exit(1)

    # Create orchestrator
    orchestrator = EnhancedIngestionOrchestrator(db_config)

    try:
        if args.list_sources:
            orchestrator.list_sources()

        elif args.interactive:
            orchestrator.interactive_mode()

        elif args.check_migrations:
            print("🔍 Checking migration status...")
            migration_status = orchestrator.check_migrations(args.source)
            
            for source_name, status in migration_status.items():
                print(f"\n{source_name}:")
                if status['status'] == 'ok':
                    print(f"  ✅ All migrations applied ({len(status['applied'])} files)")
                elif status['status'] == 'pending':
                    print(f"  ⏳ {len(status['pending'])} pending migrations")
                    for migration in status['pending']:
                        print(f"    - {migration}")
                elif status['status'] == 'error':
                    print(f"  ❌ {status.get('message', 'Migration error')}")

        elif args.run_migrations or args.dry_run_migrations:
            print("📋 Running migrations..." if not args.dry_run_migrations else "📋 Dry run - checking migrations...")
            success = orchestrator.run_migrations(args.source, args.dry_run_migrations)
            sys.exit(0 if success else 1)

        elif args.status:
            print("📊 Ingestion Status:")
            status = orchestrator.get_ingestion_status(args.source)
            
            for source_name, data in status.items():
                print(f"\n{source_name}:")
                if 'error' in data:
                    print(f"  ❌ {data['error']}")
                else:
                    stats = data['stats']
                    print(f"  Table: {data['table']}")
                    print(f"  Total: {stats.total_records}")
                    print(f"  Completed: {stats.completed}")
                    print(f"  Failed: {stats.failed}")
                    print(f"  In Progress: {stats.in_progress}")
                    print(f"  Success Rate: {stats.success_rate:.1f}%")

        elif args.all or args.source:
            source_names = args.source if args.source else list(orchestrator.data_sources.keys())
            
            # Build parameters
            params = {}
            if args.start_congress:
                params['start_congress'] = args.start_congress
            if args.batch_size:
                params['batch_size'] = args.batch_size
            if args.api_key:
                params['api_key'] = args.api_key
            if args.xml_dir:
                params['xml_dir'] = args.xml_dir
            if args.json_dir:
                params['json_dir'] = args.json_dir
            if args.agenda_dir:
                params['agenda_dir'] = args.agenda_dir
            if args.calendar_dir:
                params['calendar_dir'] = args.calendar_dir
            if args.pattern:
                params['pattern'] = args.pattern
            if args.file:
                params['file'] = args.file
            if args.recursive:
                params['recursive'] = True
            if args.reset:
                params['reset'] = True
            if args.limit:
                params['limit'] = args.limit
            if args.dry_run:
                params['dry_run'] = True
            if args.no_resume:
                params['no_resume'] = True

            print(f"🚀 Starting ingestion for: {', '.join(source_names)}")
            success = orchestrator.run_ingestion(source_names, params)
            
            if success:
                print("\n🎉 Ingestion completed successfully!")
            else:
                print("\n❌ Ingestion encountered errors.")
            
            sys.exit(0 if success else 1)

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()