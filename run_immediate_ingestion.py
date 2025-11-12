#!/usr/bin/env python3
"""
Immediate Ingestion Runner for OpenLegislation

This script triggers immediate ingestion of data from all three websites:
- Congress.gov API
- GovInfo API
- State/Local sources

It uses the automated ingestion scheduler to run jobs immediately.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from automation.ingestion_scheduler import IngestionScheduler
from queue_manager import submit_ingestion_job
from comprehensive_ai_agents import DataIngestionAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImmediateIngestionRunner:
    """
    Runner for immediate ingestion of all data sources
    """

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.ingestion_agent = DataIngestionAgent(db_config)
        self.scheduler = None

    async def initialize(self):
        """Initialize the ingestion runner"""
        logger.info("Initializing immediate ingestion runner...")

        # Create ingestion scheduler
        from automation.ingestion_scheduler import create_ingestion_scheduler
        self.scheduler = await create_ingestion_scheduler(self.db_config)

        logger.info("Ingestion runner initialized")

    async def run_all_ingestions(self):
        """Run ingestion for all three websites immediately"""
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
                    'states': ['CA', 'NY', 'TX', 'FL', 'IL'],  # Major states
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

        # Submit all ingestion jobs
        for job_config in ingestion_jobs:
            try:
                logger.info(f"📋 Submitting {job_config['name']}...")

                # Use the ingestion agent to think about the job
                await self.ingestion_agent.think(
                    'immediate_ingestion_job',
                    f"Submitting {job_config['name']} for immediate execution",
                    confidence=0.95
                )

                # Submit the job
                job_id = await submit_ingestion_job(
                    job_name=job_config['name'],
                    ingestion_type=job_config['type'],
                    parameters=job_config['parameters'],
                    enable_parallel=job_config['parameters'].get('enable_parallel', True),
                    enable_gpu=job_config['parameters'].get('enable_gpu', False),
                    priority='high'  # High priority for immediate jobs
                )

                submitted_jobs.append({
                    'job_id': job_id,
                    'name': job_config['name'],
                    'type': job_config['type'],
                    'description': job_config['description']
                })

                logger.info(f"✅ Submitted {job_config['name']} with job ID: {job_id}")

                # Small delay between submissions to avoid overwhelming the queue
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Failed to submit {job_config['name']}: {e}")
                continue

        logger.info(f"🎯 Submitted {len(submitted_jobs)} ingestion jobs")

        # Monitor job progress
        await self.monitor_jobs(submitted_jobs)

        return submitted_jobs

    async def monitor_jobs(self, jobs: List[Dict[str, Any]], timeout_minutes: int = 30):
        """Monitor the progress of submitted jobs"""
        logger.info("📊 Monitoring job execution progress...")

        start_time = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        completed_jobs = set()
        failed_jobs = []

        while datetime.now() - start_time < timeout and len(completed_jobs) < len(jobs):
            try:
                # Check status of each job
                for job in jobs:
                    job_id = job['job_id']

                    if job_id in completed_jobs:
                        continue

                    # Get job status (this would need to be implemented in queue_manager)
                    try:
                        status = await self._get_job_status(job_id)

                        if status['status'] in ['completed', 'success']:
                            completed_jobs.add(job_id)
                            logger.info(f"✅ {job['name']} completed successfully")

                        elif status['status'] in ['failed', 'error']:
                            completed_jobs.add(job_id)
                            failed_jobs.append(job)
                            logger.error(f"❌ {job['name']} failed: {status.get('error', 'Unknown error')}")

                        elif status['status'] == 'running':
                            progress = status.get('progress', 0)
                            logger.info(f"🔄 {job['name']}: {progress}% complete")

                    except Exception as e:
                        logger.warning(f"Could not get status for job {job_id}: {e}")

                # Wait before next check
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Error monitoring jobs: {e}")
                await asyncio.sleep(30)

        # Final summary
        successful_jobs = len(completed_jobs) - len(failed_jobs)
        logger.info("📈 Ingestion Summary:")
        logger.info(f"   Total jobs submitted: {len(jobs)}")
        logger.info(f"   Successful: {successful_jobs}")
        logger.info(f"   Failed: {len(failed_jobs)}")
        logger.info(f"   Still running: {len(jobs) - len(completed_jobs)}")

        if failed_jobs:
            logger.warning("Failed jobs:")
            for job in failed_jobs:
                logger.warning(f"   - {job['name']} (ID: {job['job_id']})")

        return {
            'total_jobs': len(jobs),
            'successful': successful_jobs,
            'failed': len(failed_jobs),
            'still_running': len(jobs) - len(completed_jobs),
            'failed_jobs': failed_jobs
        }

    async def _get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a job (placeholder - needs implementation)"""
        # This would need to be implemented in the queue manager
        # For now, return a mock status
        return {
            'status': 'running',
            'progress': 50,
            'start_time': datetime.now().isoformat()
        }

    async def schedule_future_ingestion(self, delay_minutes: int = 5):
        """Schedule ingestion to run in the future"""
        logger.info(f"⏰ Scheduling ingestion to run in {delay_minutes} minutes...")

        # Start the automated scheduler
        await self.scheduler.start_automated_ingestion()

        # Wait for the specified delay
        await asyncio.sleep(delay_minutes * 60)

        # Run the ingestion
        await self.run_all_ingestions()

    async def run_health_check(self):
        """Run a health check before starting ingestion"""
        logger.info("🏥 Running pre-ingestion health check...")

        try:
            # Check database connectivity
            from queue_manager import QueueManager
            queue_manager = QueueManager(self.db_config)
            stats = await queue_manager.get_queue_stats()

            logger.info("✅ Database connection healthy")
            logger.info(f"   Queue status: {stats.get('pending', 0)} pending, {stats.get('running', 0)} running")

            # Check AI agent health
            agent_health = await self.ingestion_agent.get_health_status()
            logger.info(f"✅ AI Agent health: {agent_health}")

            return True

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False


async def main():
    """Main function to run immediate ingestion"""
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': '',  # Will be read from environment
        'database': 'openlegislation'
    }

    # Create and initialize the runner
    runner = ImmediateIngestionRunner(db_config)
    await runner.initialize()

    # Run health check
    if not await runner.run_health_check():
        logger.error("Health check failed. Aborting ingestion.")
        return

    # Ask user if they want to run immediately or schedule for later
    print("\n" + "="*60)
    print("OpenLegislation Immediate Ingestion Runner")
    print("="*60)
    print("This will ingest data from all three websites:")
    print("  1. Congress.gov API (Federal legislative data)")
    print("  2. GovInfo API (Government publications)")
    print("  3. State/Local sources (State and local government data)")
    print()
    print("Options:")
    print("  1. Run immediately")
    print("  2. Schedule to run in 5 minutes")
    print("  3. Schedule to run in 10 minutes")
    print()

    try:
        choice = input("Enter your choice (1-3): ").strip()

        if choice == '1':
            # Run immediately
            logger.info("🚀 Running ingestion immediately...")
            results = await runner.run_all_ingestions()

        elif choice == '2':
            # Schedule for 5 minutes
            logger.info("⏰ Scheduling ingestion for 5 minutes from now...")
            await runner.schedule_future_ingestion(delay_minutes=5)

        elif choice == '3':
            # Schedule for 10 minutes
            logger.info("⏰ Scheduling ingestion for 10 minutes from now...")
            await runner.schedule_future_ingestion(delay_minutes=10)

        else:
            logger.error("Invalid choice. Exiting.")
            return

    except KeyboardInterrupt:
        logger.info("Ingestion cancelled by user")
        return
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        return

    logger.info("🎉 Ingestion process completed!")


if __name__ == '__main__':
    # Run the ingestion
    asyncio.run(main())
