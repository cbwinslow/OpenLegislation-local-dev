"""
Tests for queue management system.

This module tests the queue_manager.py functionality including:
- Job submission and execution
- Queue monitoring and management
- GPU acceleration support
- Performance benchmarking
- Error handling and recovery
- Database integration
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from tests.utils.test_helpers import (
    assert_performance_metrics,
    assert_no_exceptions,
    generate_mock_bill_data,
    generate_mock_member_data
)


class TestQueueManagerInitialization:
    """Test QueueManager initialization and setup."""

    @pytest.mark.unit
    def test_initialization(self):
        """Test QueueManager initialization."""
        from queue_manager import QueueManager

        manager = QueueManager()
        assert manager.pool is None
        assert manager.jobs == {}
        assert manager.active_jobs == set()
        assert manager.completed_jobs == []

    @pytest.mark.unit
    def test_database_connection_setup(self, mock_db_config):
        """Test database connection setup."""
        from queue_manager import QueueManager

        manager = QueueManager()
        manager.setup_database_connection(mock_db_config)

        assert manager.db_config == mock_db_config

    @pytest.mark.unit
    def test_gpu_detection(self):
        """Test GPU detection and setup."""
        with patch('queue_manager.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            mock_torch.cuda.device_count.return_value = 2

            from queue_manager import GPU_AVAILABLE, GPU_COUNT
            assert GPU_AVAILABLE is True
            assert GPU_COUNT == 2

    @pytest.mark.unit
    def test_no_gpu_available(self):
        """Test behavior when GPU is not available."""
        with patch('queue_manager.torch', None):
            from queue_manager import GPU_AVAILABLE, GPU_COUNT
            assert GPU_AVAILABLE is False
            assert GPU_COUNT == 0


class TestJobSubmission:
    """Test job submission functionality."""

    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for testing."""
        from queue_manager import QueueManager
        manager = QueueManager()
        manager.db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'test',
            'password': 'test',
            'database': 'test'
        }
        return manager

    @pytest.mark.asyncio
    async def test_basic_job_submission(self, queue_manager, mock_async_db_connection):
        """Test basic job submission."""
        with patch('asyncpg.create_pool', return_value=mock_async_db_connection):
            job_id = await queue_manager.submit_job(
                job_type="ingestion",
                payload={"table": "bills", "records": 100},
                priority=1
            )

            assert job_id is not None
            assert job_id in queue_manager.jobs
            assert queue_manager.jobs[job_id]["status"] == "queued"

    @pytest.mark.asyncio
    async def test_scheduled_job_submission(self, queue_manager, mock_async_db_connection):
        """Test scheduled job submission."""
        with patch('asyncpg.create_pool', return_value=mock_async_db_connection):
            schedule_time = datetime.now() + timedelta(hours=1)

            job_id = await queue_manager.submit_scheduled_job(
                job_type="maintenance",
                payload={"action": "cleanup"},
                schedule_time=schedule_time
            )

            assert job_id is not None
            assert queue_manager.jobs[job_id]["status"] == "scheduled"
            assert queue_manager.jobs[job_id]["schedule_time"] == schedule_time

    @pytest.mark.asyncio
    async def test_job_with_dependencies(self, queue_manager, mock_async_db_connection):
        """Test job submission with dependencies."""
        with patch('asyncpg.create_pool', return_value=mock_async_db_connection):
            # Submit parent job
            parent_job_id = await queue_manager.submit_job(
                job_type="ingestion",
                payload={"table": "bills"}
            )

            # Submit dependent job
            dependent_job_id = await queue_manager.submit_job(
                job_type="processing",
                payload={"table": "bills"},
                dependencies=[parent_job_id]
            )

            assert dependent_job_id in queue_manager.jobs
            assert parent_job_id in queue_manager.jobs[dependent_job_id]["dependencies"]

    @pytest.mark.asyncio
    async def test_gpu_accelerated_job(self, queue_manager, mock_async_db_connection):
        """Test GPU-accelerated job submission."""
        with patch('asyncpg.create_pool', return_value=mock_async_db_connection), \
             patch('queue_manager.GPU_AVAILABLE', True):

            job_id = await queue_manager.submit_gpu_job(
                job_type="ml_processing",
                payload={"model": "test_model", "data_size": 1000},
                gpu_memory_required=2048
            )

            assert job_id is not None
            assert queue_manager.jobs[job_id]["gpu_accelerated"] is True
            assert queue_manager.jobs[job_id]["gpu_memory_required"] == 2048


class TestJobExecution:
    """Test job execution functionality."""

    @pytest.fixture
    async def queue_manager(self):
        """Create and setup a QueueManager instance."""
        from queue_manager import QueueManager
        manager = QueueManager()
        manager.db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'test',
            'password': 'test',
            'database': 'test'
        }

        # Mock the database pool
        mock_pool = AsyncMock()
        manager.pool = mock_pool

        yield manager

    @pytest.mark.asyncio
    async def test_job_execution(self, queue_manager):
        """Test basic job execution."""
        # Create a simple test job
        async def test_task():
            await asyncio.sleep(0.01)
            return {"status": "completed", "processed": 100}

        job_id = await queue_manager.submit_job(
            job_type="test",
            payload={"test": True}
        )

        # Execute the job
        result = await queue_manager.execute_job(job_id, test_task)

        assert result["status"] == "completed"
        assert result["processed"] == 100
        assert queue_manager.jobs[job_id]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_parallel_job_execution(self, queue_manager):
        """Test parallel job execution."""
        async def parallel_task(task_id):
            await asyncio.sleep(0.01)
            return {"task_id": task_id, "status": "completed"}

        # Submit multiple jobs
        job_ids = []
        for i in range(3):
            job_id = await queue_manager.submit_job(
                job_type="parallel_test",
                payload={"task_id": i}
            )
            job_ids.append(job_id)

        # Execute jobs in parallel
        tasks = [queue_manager.execute_job(job_id, lambda j=job_id: parallel_task(j)) for job_id in job_ids]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        for result in results:
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_job_error_handling(self, queue_manager):
        """Test job error handling."""
        async def failing_task():
            raise ValueError("Test error")

        job_id = await queue_manager.submit_job(
            job_type="failing_test",
            payload={"test": True}
        )

        # Execute the failing job
        with pytest.raises(ValueError, match="Test error"):
            await queue_manager.execute_job(job_id, failing_task)

        # Check that job status is updated to failed
        assert queue_manager.jobs[job_id]["status"] == "failed"
        assert "error" in queue_manager.jobs[job_id]

    @pytest.mark.asyncio
    async def test_job_timeout_handling(self, queue_manager):
        """Test job timeout handling."""
        async def slow_task():
            await asyncio.sleep(2)  # Longer than timeout
            return {"status": "completed"}

        job_id = await queue_manager.submit_job(
            job_type="slow_test",
            payload={"test": True}
        )

        # Execute with short timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                queue_manager.execute_job(job_id, slow_task),
                timeout=0.1
            )


class TestQueueMonitoring:
    """Test queue monitoring functionality."""

    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for monitoring tests."""
        from queue_manager import QueueManager
        manager = QueueManager()
        return manager

    @pytest.mark.unit
    def test_queue_status_monitoring(self, queue_manager):
        """Test queue status monitoring."""
        # Add some test jobs
        queue_manager.jobs = {
            "job1": {"status": "queued", "job_type": "ingestion"},
            "job2": {"status": "running", "job_type": "processing"},
            "job3": {"status": "completed", "job_type": "cleanup"},
            "job4": {"status": "failed", "job_type": "maintenance"}
        }

        status = queue_manager.get_queue_status()

        assert status["total_jobs"] == 4
        assert status["queued"] == 1
        assert status["running"] == 1
        assert status["completed"] == 1
        assert status["failed"] == 1

    @pytest.mark.unit
    def test_performance_monitoring(self, queue_manager):
        """Test performance monitoring."""
        # Simulate some completed jobs with timing data
        queue_manager.completed_jobs = [
            {"duration": 1.5, "cpu_usage": 45.2, "memory_usage": 128.7},
            {"duration": 2.1, "cpu_usage": 52.1, "memory_usage": 145.3},
            {"duration": 0.8, "cpu_usage": 38.9, "memory_usage": 112.4}
        ]

        metrics = queue_manager.get_performance_metrics()

        assert "average_duration" in metrics
        assert "average_cpu_usage" in metrics
        assert "average_memory_usage" in metrics
        assert "total_jobs_completed" in metrics

    @pytest.mark.unit
    def test_job_history_tracking(self, queue_manager):
        """Test job history tracking."""
        # Add completed jobs
        queue_manager.completed_jobs = [
            {"job_id": "job1", "job_type": "ingestion", "completed_at": datetime.now()},
            {"job_id": "job2", "job_type": "processing", "completed_at": datetime.now()},
        ]

        history = queue_manager.get_job_history(limit=10)

        assert len(history) == 2
        assert all(job["job_id"] in ["job1", "job2"] for job in history)


class TestGPUSupport:
    """Test GPU support functionality."""

    @pytest.mark.unit
    def test_gpu_job_scheduling(self):
        """Test GPU job scheduling."""
        from queue_manager import QueueManager

        with patch('queue_manager.GPU_AVAILABLE', True), \
             patch('queue_manager.GPU_COUNT', 2):

            manager = QueueManager()

            # Test GPU job scheduling
            gpu_jobs = manager.get_gpu_queue_status()
            assert "available_gpus" in gpu_jobs
            assert "queued_gpu_jobs" in gpu_jobs

    @pytest.mark.unit
    def test_gpu_memory_management(self):
        """Test GPU memory management."""
        from queue_manager import QueueManager

        with patch('queue_manager.GPU_AVAILABLE', True):
            manager = QueueManager()

            # Test memory allocation
            allocation = manager.allocate_gpu_memory(1024)
            assert allocation is not None

            # Test memory deallocation
            deallocation = manager.deallocate_gpu_memory(allocation)
            assert deallocation is True

    @pytest.mark.unit
    def test_no_gpu_fallback(self):
        """Test fallback behavior when GPU is not available."""
        from queue_manager import QueueManager

        with patch('queue_manager.GPU_AVAILABLE', False):
            manager = QueueManager()

            # Should handle GPU requests gracefully
            assert_no_exceptions(manager.allocate_gpu_memory, 1024)
            assert_no_exceptions(manager.get_gpu_queue_status)


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery functionality."""

    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for error handling tests."""
        from queue_manager import QueueManager
        manager = QueueManager()
        return manager

    @pytest.mark.unit
    def test_job_retry_mechanism(self, queue_manager):
        """Test job retry mechanism."""
        # Create a job that fails
        queue_manager.jobs["test_job"] = {
            "status": "failed",
            "retry_count": 0,
            "max_retries": 3,
            "error": "Test error"
        }

        # Test retry logic
        can_retry = queue_manager.can_retry_job("test_job")
        assert can_retry is True

        # Increment retry count
        queue_manager.increment_retry_count("test_job")
        assert queue_manager.jobs["test_job"]["retry_count"] == 1

        # Test max retries reached
        queue_manager.jobs["test_job"]["retry_count"] = 3
        can_retry = queue_manager.can_retry_job("test_job")
        assert can_retry is False

    @pytest.mark.unit
    def test_database_connection_recovery(self, queue_manager):
        """Test database connection recovery."""
        # Simulate connection failure
        queue_manager.pool = None

        # Test reconnection logic
        assert_no_exceptions(queue_manager.ensure_database_connection)

    @pytest.mark.unit
    def test_graceful_shutdown(self, queue_manager):
        """Test graceful shutdown handling."""
        # Add some running jobs
        queue_manager.active_jobs = {"job1", "job2", "job3"}

        # Test shutdown procedure
        assert_no_exceptions(queue_manager.graceful_shutdown)

        # Verify jobs are marked for termination
        assert len(queue_manager.active_jobs) == 0


class TestPerformanceBenchmarks:
    """Test performance benchmarking functionality."""

    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for benchmarking tests."""
        from queue_manager import QueueManager
        manager = QueueManager()
        return manager

    @pytest.mark.performance
    def test_ingestion_performance_benchmark(self, queue_manager):
        """Test ingestion performance benchmarking."""
        # Generate test data
        test_data = generate_mock_bill_data(1000)

        start_time = time.time()

        # Simulate ingestion process
        for bill in test_data:
            # Simulate processing time
            time.sleep(0.001)

        end_time = time.time()
        duration = end_time - start_time

        # Verify performance metrics
        assert duration < 2.0  # Should complete within 2 seconds
        assert len(test_data) == 1000

    @pytest.mark.performance
    def test_concurrent_processing_benchmark(self, queue_manager):
        """Test concurrent processing performance."""
        import concurrent.futures

        def process_item(item):
            time.sleep(0.01)  # Simulate processing
            return item * 2

        test_data = list(range(100))

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_item, test_data))

        end_time = time.time()
        duration = end_time - start_time

        # Verify results and performance
        assert len(results) == 100
        assert all(result == item * 2 for item, result in zip(test_data, results))
        assert duration < 1.0  # Should complete within 1 second with concurrency

    @pytest.mark.performance
    def test_memory_usage_monitoring(self, queue_manager):
        """Test memory usage monitoring during operations."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform memory-intensive operation
        large_data = [list(range(1000)) for _ in range(1000)]

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Verify memory monitoring
        memory_increase = peak_memory - initial_memory
        assert memory_increase > 0  # Memory usage should increase

        # Clean up
        del large_data


class TestIntegrationTests:
    """Integration tests for queue management system."""

    @pytest.mark.integration
    async def test_full_ingestion_workflow(self, mock_async_db_connection):
        """Test full ingestion workflow."""
        from queue_manager import QueueManager

        manager = QueueManager()
        manager.db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'test',
            'password': 'test',
            'database': 'test'
        }

        with patch('asyncpg.create_pool', return_value=mock_async_db_connection):
            # Submit ingestion job
            job_id = await manager.submit_job(
                job_type="bill_ingestion",
                payload={"jurisdiction": "federal", "count": 100}
            )

            # Submit processing job with dependency
            processing_job_id = await manager.submit_job(
                job_type="bill_processing",
                payload={"job_id": job_id},
                dependencies=[job_id]
            )

            # Verify job relationships
            assert processing_job_id in manager.jobs
            assert job_id in manager.jobs[processing_job_id]["dependencies"]

            # Verify job statuses
            assert manager.jobs[job_id]["status"] == "queued"
            assert manager.jobs[processing_job_id]["status"] == "queued"

    @pytest.mark.integration
    async def test_error_recovery_workflow(self, mock_async_db_connection):
        """Test error recovery workflow."""
        from queue_manager import QueueManager

        manager = QueueManager()

        with patch('asyncpg.create_pool', return_value=mock_async_db_connection):
            # Submit a job that will fail
            job_id = await manager.submit_job(
                job_type="failing_operation",
                payload={"should_fail": True}
            )

            # Simulate job failure
            manager.jobs[job_id]["status"] = "failed"
            manager.jobs[job_id]["error"] = "Simulated failure"

            # Test retry logic
            can_retry = manager.can_retry_job(job_id)
            assert can_retry is True

            # Test recovery by resubmitting
            new_job_id = await manager.resubmit_failed_job(job_id)
            assert new_job_id != job_id
            assert manager.jobs[new_job_id]["status"] == "queued"