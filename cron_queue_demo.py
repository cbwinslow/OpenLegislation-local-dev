#!/usr/bin/env python3
"""
Cron-Based Queue System Demo

This script demonstrates the database-driven cron queue system where:
1. Scripts are stored in the database (queue_system.stored_scripts)
2. Cron schedules are stored in the database (queue_system.cron_schedules)
3. The system automatically creates jobs based on cron schedules
4. Jobs execute stored scripts or reference filesystem scripts

Usage:
    python3 cron_queue_demo.py
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database_connection import get_session

def create_sample_scripts():
    """Create sample scripts in the database"""
    session = get_session()

    # Sample Python script for federal data ingestion
    federal_ingestion_script = '''
import sys
import os
sys.path.insert(0, '/home/cbwinslow/OpenLegislation-local-dev')

from tools.ingestion.core.ingest_federal_data import ingest_bills_optimized
from database_connection import get_session

# Get database session
db_session = get_session()

# Run federal bills ingestion
try:
    callback = type('Callback', (), {'should_stop': lambda: False})()
    ingest_bills_optimized(db_session, callback, start_congress=118, batch_size=10)
    print("Federal bills ingestion completed successfully")
except Exception as e:
    print(f"Federal bills ingestion failed: {e}")
    sys.exit(1)
'''

    # Sample SQL script for data cleanup
    cleanup_script = '''
-- Clean up old telemetry data
DELETE FROM telemetry_events
WHERE timestamp < NOW() - INTERVAL '30 days';

-- Clean up old performance metrics
DELETE FROM performance_metrics
WHERE timestamp < NOW() - INTERVAL '7 days';

-- Vacuum analyze for performance
VACUUM ANALYZE bills;
VACUUM ANALYZE bill_actions;

SELECT 'Data cleanup completed' as status;
'''

    # Insert scripts into database
    scripts_data = [
        {
            'script_name': 'federal_bills_ingestion',
            'description': 'Automated federal bills data ingestion from congress.gov API',
            'script_type': 'python',
            'script_language': 'python3',
            'script_content': federal_ingestion_script.strip(),
            'parameters': json.dumps({
                'start_congress': {'type': 'integer', 'default': 118, 'description': 'Starting congress number'},
                'batch_size': {'type': 'integer', 'default': 250, 'description': 'Batch size for API calls'}
            }),
            'environment_vars': json.dumps({
                'CONGRESS_API_KEY': 'your_api_key_here',
                'PYTHONPATH': '/home/cbwinslow/OpenLegislation-local-dev'
            }),
            'working_directory': '/home/cbwinslow/OpenLegislation-local-dev',
            'timeout_seconds': 3600,
            'tags': ['ingestion', 'federal', 'bills', 'automated']
        },
        {
            'script_name': 'database_cleanup',
            'description': 'Clean up old telemetry and performance data',
            'script_type': 'sql',
            'script_content': cleanup_script.strip(),
            'parameters': json.dumps({}),
            'timeout_seconds': 1800,
            'tags': ['maintenance', 'cleanup', 'database']
        }
    ]

    for script_data in scripts_data:
        session.execute('''
            INSERT INTO queue_system.stored_scripts
            (script_name, description, script_type, script_language, script_content,
             parameters, environment_vars, working_directory, timeout_seconds, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (script_name) DO UPDATE SET
                script_content = EXCLUDED.script_content,
                parameters = EXCLUDED.parameters,
                updated_at = NOW()
        ''', (
            script_data['script_name'],
            script_data['description'],
            script_data['script_type'],
            script_data.get('script_language'),
            script_data['script_content'],
            script_data['parameters'],
            script_data.get('environment_vars', '{}'),
            script_data.get('working_directory'),
            script_data['timeout_seconds'],
            script_data['tags']
        ))

    session.commit()
    print("✅ Sample scripts created in database")

    # Get script IDs for creating schedules
    script_ids = {}
    result = session.execute('SELECT script_id, script_name FROM queue_system.stored_scripts WHERE script_name IN (%s, %s)',
                           ('federal_bills_ingestion', 'database_cleanup'))
    for row in result:
        script_ids[row[1]] = row[0]

    return script_ids

def create_cron_schedules(script_ids):
    """Create cron schedules that reference the stored scripts"""
    session = get_session()

    schedules_data = [
        {
            'schedule_name': 'daily_federal_ingestion',
            'description': 'Run federal bills ingestion daily at 2 AM',
            'cron_expression': '0 2 * * *',  # Daily at 2 AM
            'timezone': 'UTC',
            'script_id': script_ids['federal_bills_ingestion'],
            'job_template': json.dumps({
                'priority': 8,
                'config': {'notification_enabled': True}
            }),
            'parameters': json.dumps({
                'start_congress': 118,
                'batch_size': 100
            })
        },
        {
            'schedule_name': 'weekly_database_cleanup',
            'description': 'Run database cleanup weekly on Sundays at 3 AM',
            'cron_expression': '0 3 * * 0',  # Weekly on Sunday at 3 AM
            'timezone': 'UTC',
            'script_id': script_ids['database_cleanup'],
            'job_template': json.dumps({
                'priority': 5,
                'config': {'maintenance_mode': True}
            }),
            'parameters': json.dumps({})
        },
        {
            'schedule_name': 'hourly_health_check',
            'description': 'Run system health check every hour',
            'cron_expression': '0 * * * *',  # Every hour
            'timezone': 'UTC',
            'script_id': script_ids['database_cleanup'],  # Reuse cleanup script for health check
            'job_template': json.dumps({
                'priority': 3,
                'config': {'health_check_only': True}
            }),
            'parameters': json.dumps({})
        }
    ]

    for schedule_data in schedules_data:
        session.execute('''
            INSERT INTO queue_system.cron_schedules
            (schedule_name, description, cron_expression, timezone, script_id,
             job_template, parameters)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (schedule_name) DO UPDATE SET
                cron_expression = EXCLUDED.cron_expression,
                parameters = EXCLUDED.parameters,
                updated_at = NOW()
        ''', (
            schedule_data['schedule_name'],
            schedule_data['description'],
            schedule_data['cron_expression'],
            schedule_data['timezone'],
            schedule_data['script_id'],
            schedule_data['job_template'],
            schedule_data['parameters']
        ))

    session.commit()
    print("✅ Cron schedules created in database")

def demonstrate_cron_processing():
    """Demonstrate how the cron system processes schedules"""
    session = get_session()

    print("\n🔄 Simulating cron schedule processing...")

    # Manually trigger cron processing (normally done by pg_cron)
    result = session.execute('SELECT queue_system.process_cron_schedules()')
    jobs_created = result.fetchone()[0]

    print(f"✅ Created {jobs_created} jobs from cron schedules")

    # Show pending jobs
    result = session.execute('''
        SELECT jq.job_id, jq.job_name, jq.job_type, cs.schedule_name, jq.parameters
        FROM queue_system.job_queue jq
        LEFT JOIN queue_system.cron_schedules cs ON jq.cron_schedule_id = cs.schedule_id
        WHERE jq.status = 'pending'
        ORDER BY jq.created_at DESC
        LIMIT 5
    ''')

    print("\n📋 Pending jobs created from cron schedules:")
    for row in result:
        print(f"  - {row[1]} ({row[2]}) from schedule: {row[3]}")

def show_system_status():
    """Show current system status"""
    session = get_session()

    print("\n📊 System Status:")

    # Count scripts
    result = session.execute('SELECT COUNT(*) FROM queue_system.stored_scripts')
    script_count = result.fetchone()[0]
    print(f"  📄 Stored Scripts: {script_count}")

    # Count schedules
    result = session.execute('SELECT COUNT(*) FROM queue_system.cron_schedules WHERE is_active = true')
    schedule_count = result.fetchone()[0]
    print(f"  ⏰ Active Cron Schedules: {schedule_count}")

    # Count pending jobs
    result = session.execute('SELECT COUNT(*) FROM queue_system.job_queue WHERE status = \'pending\'')
    pending_jobs = result.fetchone()[0]
    print(f"  ⏳ Pending Jobs: {pending_jobs}")

    # Show next schedule runs
    result = session.execute('''
        SELECT schedule_name, next_run_at, cron_expression
        FROM queue_system.cron_schedules
        WHERE is_active = true AND next_run_at IS NOT NULL
        ORDER BY next_run_at ASC
        LIMIT 3
    ''')

    print("  📅 Next Schedule Runs:")
    for row in result:
        print(f"    - {row[0]}: {row[1]} (cron: {row[2]})")

def main():
    """Main demonstration function"""
    print("🚀 Cron-Based Queue System Demo")
    print("=" * 50)

    try:
        # Create sample scripts
        script_ids = create_sample_scripts()

        # Create cron schedules
        create_cron_schedules(script_ids)

        # Demonstrate cron processing
        demonstrate_cron_processing()

        # Show system status
        show_system_status()

        print("\n✅ Cron-based queue system demo completed!")
        print("\n🎯 Key Features Demonstrated:")
        print("  • Scripts stored in database (queue_system.stored_scripts)")
        print("  • Cron schedules stored in database (queue_system.cron_schedules)")
        print("  • Automatic job creation from cron schedules")
        print("  • Support for Python, SQL, and other script types")
        print("  • Parameterized script execution")
        print("  • Environment variable and working directory support")

        print("\n🔧 How to Use:")
        print("  1. Store your scripts in queue_system.stored_scripts table")
        print("  2. Create cron schedules in queue_system.cron_schedules table")
        print("  3. pg_cron automatically processes schedules every minute")
        print("  4. Jobs are created and executed based on your cron expressions")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
