#!/usr/bin/env python3
"""
Simple Ingestion Runner for OpenLegislation

Directly submits ingestion jobs to the queue system for immediate processing.
"""

import asyncio
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def submit_ingestion_jobs():
    """Submit ingestion jobs directly to the queue system"""

    # Import here to avoid dependency issues
    try:
        from queue_manager import submit_ingestion_job
    except ImportError as e:
        logger.error(f"Failed to import queue_manager: {e}")
        logger.info("Please ensure the database is running and dependencies are installed")
        return

    logger.info("🚀 Starting immediate ingestion of all data sources...")

    ingestion_jobs = [
        {
            'name': 'Congress.gov Data Ingestion',
            'type': 'congress',
            'description': 'Ingest legislative data from Congress.gov API',
            'parameters': {
                'start_congress': 110,
                'end_congress': 118,
                'enable_gpu': True,
                'enable_parallel': True,
                'batch_size': 1000,
                'max_workers': 8
            }
        },
        {
            'name': 'GovInfo Bills Ingestion',
            'type': 'govinfo',
            'description': 'Ingest bill data from GovInfo API',
            'parameters': {
                'collection': 'BILLS',
                'content_type': 'json',
                'enable_gpu': True,
                'enable_parallel': True,
                'start_date': '2020-01-01',
                'end_date': datetime.now().strftime('%Y-%m-%d')
            }
        },
        {
            'name': 'Federal Members Ingestion',
            'type': 'members',
            'description': 'Ingest federal member data',
            'parameters': {
                'congress': 118,
                'include_committees': True,
                'include_votes': False,
                'enable_parallel': True
            }
        },
        {
            'name': 'State Legislative Data',
            'type': 'state',
            'description': 'Ingest state legislative data',
            'parameters': {
                'states': ['CA', 'NY', 'TX', 'FL', 'IL'],
                'data_types': ['bills', 'members', 'committees'],
                'enable_parallel': True,
                'max_concurrent_states': 3
            }
        },
        {
            'name': 'Local Government Data',
            'type': 'local',
            'description': 'Ingest local government legislative data',
            'parameters': {
                'cities': ['New York City', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
                'data_types': ['ordinances', 'resolutions', 'meetings'],
                'enable_parallel': True,
                'max_concurrent_cities': 2
            }
        }
    ]

    submitted_jobs = []

    for job_config in ingestion_jobs:
        try:
            logger.info(f"📋 Submitting {job_config['name']}...")

            # Submit the job
            job_id = await submit_ingestion_job(
                job_name=job_config['name'],
                ingestion_type=job_config['type'],
                parameters=job_config['parameters'],
                enable_parallel=job_config['parameters'].get('enable_parallel', True),
                enable_gpu=job_config['parameters'].get('enable_gpu', False),
                priority='high'
            )

            submitted_jobs.append({
                'job_id': job_id,
                'name': job_config['name'],
                'type': job_config['type'],
                'description': job_config['description']
            })

            logger.info(f"✅ Submitted {job_config['name']} with job ID: {job_id}")

            # Small delay between submissions
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Failed to submit {job_config['name']}: {e}")
            continue

    logger.info(f"🎯 Successfully submitted {len(submitted_jobs)} ingestion jobs")

    # Print summary
    print("\n" + "="*80)
    print("INGESTION JOBS SUBMITTED SUCCESSFULLY")
    print("="*80)
    print(f"Total jobs submitted: {len(submitted_jobs)}")
    print()
    print("Jobs submitted:")
    for job in submitted_jobs:
        print(f"  • {job['name']} (ID: {job['job_id']})")
        print(f"    Type: {job['type']}")
        print(f"    Description: {job['description']}")
    print()
    print("The ingestion jobs are now running in the background.")
    print("You can monitor progress using the queue management tools.")
    print("="*80)

    return submitted_jobs


async def main():
    """Main function"""
    print("OpenLegislation Simple Ingestion Runner")
    print("=======================================")
    print()
    print("This will submit ingestion jobs for data from:")
    print("  1. Congress.gov API (Federal legislative data)")
    print("  2. GovInfo API (Government publications)")
    print("  3. State/Local sources (State and local government data)")
    print()
    print("Jobs will be submitted with high priority and run immediately.")
    print()

    try:
        input("Press Enter to start ingestion...")
        print()

        await submit_ingestion_jobs()

    except KeyboardInterrupt:
        print("\nIngestion cancelled by user.")
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        print(f"\nError: {e}")


if __name__ == '__main__':
    asyncio.run(main())
