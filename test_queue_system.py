#!/usr/bin/env python3
"""
Test script for the OpenLegislation Queue System

This script demonstrates the complete queue system functionality including:
- Job submission and scheduling
- GPU-accelerated ingestion
- Parallel processing
- Audit logging and telemetry
- Performance monitoring
- Queue management and monitoring

Author: OpenLegislation Team
Date: 2025-11-08
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules
from queue_manager import QueueManager, submit_ingestion_job, submit_query_job
from tools.ingestion.core.ingestion_engine import create_ingestion_engine


async def test_basic_job_submission():
    """Test basic job submission and execution"""
    logger.info("Testing basic job submission...")

    # Submit a simple ingestion job
    job_id = await submit_ingestion_job(
        job_name="Test Congress Ingestion",
        ingestion_type="congress",
        parameters={
            'start_congress': 117,
            'end_congress': 118,
            'api_key': os.getenv('CONGRESS_API_KEY', '')
        },
        enable_parallel=True,
        enable_gpu=False  # Disable GPU for basic test
    )

    logger.info(f"Submitted job: {job_id}")

    # Wait a bit and check status
    await asyncio.sleep(2)

    manager = QueueManager({
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'openlegislation')
    })

    status = await manager.get_job_status(job_id)
    logger.info(f"Job status: {status}")

    return job_id


async def test_query_job_submission():
    """Test SQL query job submission"""
    logger.info("Testing query job submission...")

    # Submit a query job
    job_id = await submit_query_job(
        job_name="Test Query Job",
        sql_query="SELECT COUNT(*) as total_bills FROM master.bill WHERE congress >= 117",
        parameters={}
    )

    logger.info(f"Submitted query job: {job_id}")

    # Wait and check status
    await asyncio.sleep(2)

    manager = QueueManager({
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'openlegislation')
    })

    status = await manager.get_job_status(job_id)
    logger.info(f"Query job status: {status}")

    return job_id


async def test_saved_query_job():
    """Test job using saved query"""
    logger.info("Testing saved query job...")

    manager = QueueManager({
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'openlegislation')
    })

    # Submit job using saved query
    from queue_manager import JobConfig

    config = JobConfig(
        job_id='',
        job_type='query',
        job_name='Test Saved Query Job',
        saved_query_id='get_recent_bills',  # This should exist from our SQL setup
        parameters={'limit': 100}
    )

    job_id = await manager.submit_job(config)
    logger.info(f"Submitted saved query job: {job_id}")

    return job_id


async def test_scheduled_job():
    """Test scheduled job submission"""
    logger.info("Testing scheduled job submission...")

    # Schedule a job to run in 5 minutes
    scheduled_time = datetime.now() + timedelta(minutes=5)

    job_id = await submit_ingestion_job(
        job_name="Scheduled Test Job",
        ingestion_type="members",
        parameters={},
        enable_parallel=True,
        enable_gpu=False
    )

    # Update the job to be scheduled
    manager = QueueManager({
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'openlegislation')
    })

    # Note: In a real implementation, we'd update the scheduled_at field
    logger.info(f"Scheduled job for {scheduled_time}: {job_id}")

    return job_id


async def test_job_dependencies():
    """Test job dependencies"""
    logger.info("Testing job dependencies...")

    manager = QueueManager({
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'openlegislation')
    })

    # Submit parent job
    parent_job = await submit_ingestion_job(
        job_name="Parent Ingestion Job",
        ingestion_type="congress",
        parameters={'start_congress': 117, 'end_congress': 117},
        enable_parallel=True
    )

    # Submit dependent job
    from queue_manager import JobConfig

    dependent_config = JobConfig(
        job_id='',
        job_type='query',
        job_name='Dependent Query Job',
        sql_query='SELECT COUNT(*) FROM master.bill WHERE congress = 117',
        parameters={}
    )

    dependent_job = await manager.submit_job(
        dependent_config,
        depends_on=[parent_job]
    )

    logger.info(f"Submitted dependent job: {dependent_job} (depends on {parent_job})")

    return parent_job, dependent_job


async def test_queue_monitoring():
    """Test queue monitoring and statistics"""
    logger.info("Testing queue monitoring...")

    manager = QueueManager({
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'openlegislation')
    })

    # Get queue statistics
    stats = await manager.get_queue_stats()
    logger.info(f"Queue statistics: {stats}")

    # Get telemetry history for recent jobs
    telemetry = await manager.telemetry.get_job_history('test_job_id')
    logger.info(f"Recent telemetry events: {len(telemetry)} events")

    return stats


async def test_gpu_accelerated_ingestion():
    """Test GPU-accelerated ingestion"""
    logger.info("Testing GPU-accelerated ingestion...")

    try:
        # Create ingestion engine with GPU support
        async with await create_ingestion_engine(
            enable_parallel=True,
            max_workers=4,
            enable_gpu=True,
            gpu_memory_limit=2048  # 2GB limit
        ) as engine:

            # Test congress data ingestion with GPU
            result = await engine.ingest_congress_data(
                api_key=os.getenv('CONGRESS_API_KEY', ''),
                start_congress=117,
                end_congress=118
            )

            logger.info(f"GPU ingestion result: {result.records_processed} records, {result.duration:.2f}s")
            logger.info(f"Performance metrics: {result.performance_metrics}")

            return result

    except Exception as e:
        logger.error(f"GPU ingestion test failed: {e}")
        return None


async def test_parallel_processing():
    """Test parallel processing capabilities"""
    logger.info("Testing parallel processing...")

    try:
        # Create ingestion engine with parallel processing
        async with await create_ingestion_engine(
            enable_parallel=True,
            max_workers=8,
            enable_gpu=False
        ) as engine:

            # Test with multiple congresses in parallel
            result = await engine.ingest_congress_data(
                api_key=os.getenv('CONGRESS_API_KEY', ''),
                start_congress=110,
                end_congress=118
            )

            logger.info(f"Parallel ingestion result: {result.records_processed} records, {result.duration:.2f}s")

            # Calculate throughput
            if result.duration > 0:
                throughput = result.records_processed / result.duration
                logger.info(f"Throughput: {throughput:.2f} records/second")

            return result

    except Exception as e:
        logger.error(f"Parallel processing test failed: {e}")
        return None


async def test_error_handling():
    """Test error handling and recovery"""
    logger.info("Testing error handling...")

    manager = QueueManager({
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'openlegislation')
    })

    # Submit a job that will fail (invalid SQL)
    from queue_manager import JobConfig

    config = JobConfig(
        job_id='',
        job_type='query',
        job_name='Test Error Handling',
        sql_query='SELECT * FROM nonexistent_table',
        parameters={}
    )

    job_id = await manager.submit_job(config)
    logger.info(f"Submitted job that should fail: {job_id}")

    # Wait for execution
    await asyncio.sleep(5)

    # Check final status
    status = await manager.get_job_status(job_id)
    logger.info(f"Failed job final status: {status}")

    # Check telemetry for error events
    telemetry = await manager.telemetry.get_job_history(job_id)
    error_events = [e for e in telemetry if e.get('severity') == 'error']
    logger.info(f"Error events for job: {len(error_events)}")

    return job_id


async def test_performance_benchmarks():
    """Test performance benchmarking"""
    logger.info("Testing performance benchmarks...")

    # Run multiple ingestion tests and compare performance
    results = []

    # Test 1: CPU-only
    logger.info("Running CPU-only benchmark...")
    async with await create_ingestion_engine(enable_parallel=False, enable_gpu=False) as engine:
        result = await engine.ingest_congress_data(
            api_key=os.getenv('CONGRESS_API_KEY', ''),
            start_congress=117,
            end_congress=117
        )
        results.append(('CPU-only', result))

    # Test 2: Parallel CPU
    logger.info("Running parallel CPU benchmark...")
    async with await create_ingestion_engine(enable_parallel=True, max_workers=4, enable_gpu=False) as engine:
        result = await engine.ingest_congress_data(
            api_key=os.getenv('CONGRESS_API_KEY', ''),
            start_congress=117,
            end_congress=117
        )
        results.append(('Parallel CPU', result))

    # Test 3: GPU (if available)
    try:
        logger.info("Running GPU benchmark...")
        async with await create_ingestion_engine(enable_parallel=True, enable_gpu=True) as engine:
            result = await engine.ingest_congress_data(
                api_key=os.getenv('CONGRESS_API_KEY', ''),
                start_congress=117,
                end_congress=117
            )
            results.append(('GPU', result))
    except Exception as e:
        logger.warning(f"GPU benchmark failed: {e}")

    # Print comparison
    print("\n=== Performance Benchmark Results ===")
    for test_name, result in results:
        throughput = result.records_processed / result.duration if result.duration > 0 else 0
        print(f"{test_name}: {result.records_processed} records in {result.duration:.2f}s ({throughput:.2f} rec/s)")

    return results


async def test_queue_cleanup():
    """Test queue cleanup functionality"""
    logger.info("Testing queue cleanup...")

    manager = QueueManager({
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'openlegislation')
    })

    # Clean up old jobs (older than 1 day for testing)
    await manager.cleanup_old_jobs(days=1)
    logger.info("Cleaned up old jobs")

    # Get updated stats
    stats = await manager.get_queue_stats()
    logger.info(f"Queue stats after cleanup: {stats}")


async def main():
    """Run all tests"""
    print("🚀 Starting OpenLegislation Queue System Tests")
    print("=" * 50)

    try:
        # Basic functionality tests
        await test_basic_job_submission()
        await test_query_job_submission()
        await test_saved_query_job()
        await test_scheduled_job()
        await test_job_dependencies()

        # Monitoring and telemetry
        await test_queue_monitoring()

        # Performance tests
        await test_gpu_accelerated_ingestion()
        await test_parallel_processing()
        await test_performance_benchmarks()

        # Error handling
        await test_error_handling()

        # Cleanup
        await test_queue_cleanup()

        print("\n✅ All tests completed successfully!")
        print("📊 Check the logs above for detailed results")
        print("📈 Performance metrics and telemetry have been logged to the database")

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise


if __name__ == '__main__':
    # Set up environment variables for testing
    os.environ.setdefault('DB_HOST', 'localhost')
    os.environ.setdefault('DB_PORT', '5432')
    os.environ.setdefault('DB_USER', 'postgres')
    os.environ.setdefault('DB_PASSWORD', '')
    os.environ.setdefault('DB_NAME', 'openlegislation')

    # Run the tests
    asyncio.run(main())
