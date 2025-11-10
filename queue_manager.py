#!/usr/bin/env python3
"""
OpenLegislation Queue Management System

A comprehensive job queue system for PostgreSQL with support for:
- Async/parallel processing
- GPU acceleration
- Job scheduling and dependencies
- Audit logging and telemetry
- Performance monitoring and benchmarking

Author: OpenLegislation Team
Date: 2025-11-08
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import psutil
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from contextlib import asynccontextmanager

import asyncpg
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

# GPU Support (optional)
try:
    import torch
    import torch.cuda
    GPU_AVAILABLE = torch.cuda.is_available()
    GPU_COUNT = torch.cuda.device_count() if GPU_AVAILABLE else 0
except ImportError:
    GPU_AVAILABLE = False
    GPU_COUNT = 0
    torch = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class JobConfig:
    """Configuration for a job execution"""
    job_id: str
    job_type: str
    job_name: str
    sql_query: Optional[str] = None
    saved_query_id: Optional[str] = None
    parameters: Dict[str, Any] = None
    config: Dict[str, Any] = None
    enable_parallel: bool = False
    max_parallel_workers: int = 4
    enable_gpu: bool = False
    gpu_memory_mb: Optional[int] = None
    timeout_seconds: int = 3600
    priority: int = 5

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.config is None:
            self.config = {}


@dataclass
class JobResult:
    """Result of a job execution"""
    job_id: str
    status: str
    duration_seconds: float
    rows_affected: Optional[int] = None
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = None
    system_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.system_metrics is None:
            self.system_metrics = {}


class QueueManager:
    """
    PostgreSQL-based job queue manager with async/parallel/GPU support
    """

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.connection_pool = None
        self.async_pool = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)
        self.process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=4)
        self.gpu_executor = GPUExecutor() if GPU_AVAILABLE else None

        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()

        # Telemetry
        self.telemetry = TelemetryManager(db_config)

        # Initialize connection pools
        self._init_connection_pools()

    def _init_connection_pools(self):
        """Initialize database connection pools"""
        try:
            # Synchronous connection pool for general operations
            self.connection_pool = ThreadedConnectionPool(
                minconn=2,
                maxconn=20,
                **self.db_config
            )

            # Async connection pool for async operations
            self.async_pool = asyncpg.create_pool(**self.db_config)

            logger.info("Database connection pools initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize connection pools: {e}")
            raise

    async def submit_job(self, config: JobConfig, scheduled_at: Optional[datetime] = None,
                        depends_on: List[str] = None) -> str:
        """
        Submit a job to the queue

        Args:
            config: Job configuration
            scheduled_at: When to schedule the job
            depends_on: List of job IDs this job depends on

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        async with self.async_pool.acquire() as conn:
            # Insert job into queue
            await conn.execute("""
                INSERT INTO queue_system.job_queue (
                    job_id, job_type, job_name, description, priority, status,
                    sql_query, saved_query_id, parameters, config,
                    scheduled_at, depends_on, timeout_seconds,
                    enable_parallel, max_parallel_workers, enable_gpu, gpu_memory_mb
                ) VALUES ($1, $2, $3, $4, $5, 'pending', $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """, (
                job_id, config.job_type, config.job_name,
                config.config.get('description', ''),
                config.priority, config.sql_query,
                config.saved_query_id, json.dumps(config.parameters),
                json.dumps(config.config), scheduled_at,
                depends_on or [], config.timeout_seconds,
                config.enable_parallel, config.max_parallel_workers,
                config.enable_gpu, config.gpu_memory_mb
            ))

            # Log telemetry
            await self.telemetry.log_event(
                'job_submitted',
                {
                    'job_id': job_id,
                    'job_type': config.job_type,
                    'job_name': config.job_name,
                    'scheduled_at': scheduled_at.isoformat() if scheduled_at else None,
                    'dependencies': depends_on or []
                },
                job_id=job_id
            )

        logger.info(f"Job submitted: {job_id} - {config.job_name}")
        return job_id

    async def execute_job(self, job_id: str) -> JobResult:
        """
        Execute a job from the queue

        Args:
            job_id: Job ID to execute

        Returns:
            JobResult with execution details
        """
        start_time = time.time()
        job_config = None

        try:
            async with self.async_pool.acquire() as conn:
                # Get job details
                job_record = await conn.fetchrow("""
                    SELECT * FROM queue_system.job_queue WHERE job_id = $1
                """, job_id)

                if not job_record:
                    raise ValueError(f"Job {job_id} not found")

                job_config = JobConfig(
                    job_id=job_record['job_id'],
                    job_type=job_record['job_type'],
                    job_name=job_record['job_name'],
                    sql_query=job_record['sql_query'],
                    saved_query_id=str(job_record['saved_query_id']) if job_record['saved_query_id'] else None,
                    parameters=job_record['parameters'] or {},
                    config=job_record['config'] or {},
                    enable_parallel=job_record['enable_parallel'],
                    max_parallel_workers=job_record['max_parallel_workers'],
                    enable_gpu=job_record['enable_gpu'],
                    gpu_memory_mb=job_record['gpu_memory_mb'],
                    timeout_seconds=job_record['timeout_seconds'],
                    priority=job_record['priority']
                )

                # Mark job as running
                await conn.execute("""
                    UPDATE queue_system.job_queue
                    SET status = 'running', started_at = NOW()
                    WHERE job_id = $1
                """, job_id)

            # Log job start
            await self.telemetry.log_event(
                'job_started',
                {'job_id': job_id, 'job_type': job_config.job_type},
                job_id=job_id
            )

            # Execute the job based on its type
            if job_config.job_type == 'ingestion':
                result = await self._execute_ingestion_job(job_config)
            elif job_config.job_type == 'query':
                result = await self._execute_query_job(job_config)
            elif job_config.job_type == 'backup':
                result = await self._execute_backup_job(job_config)
            elif job_config.job_type == 'maintenance':
                result = await self._execute_maintenance_job(job_config)
            else:
                result = await self._execute_custom_job(job_config)

            # Update job status
            duration = time.time() - start_time
            async with self.async_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE queue_system.job_queue
                    SET status = $1, completed_at = NOW(),
                        actual_duration_seconds = $2,
                        error_message = $3, error_details = $4
                    WHERE job_id = $5
                """, (
                    result.status, duration,
                    result.error_message,
                    json.dumps(result.performance_metrics) if result.error_message else None,
                    job_id
                ))

                # Insert execution history
                await conn.execute("""
                    INSERT INTO queue_system.job_execution_history (
                        job_id, execution_start, execution_end, status,
                        duration_seconds, rows_affected, error_message,
                        performance_metrics, system_metrics
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, (
                    job_id, datetime.fromtimestamp(start_time),
                    datetime.now(), result.status, duration,
                    result.rows_affected, result.error_message,
                    json.dumps(result.performance_metrics),
                    json.dumps(result.system_metrics)
                ))

            # Log completion
            await self.telemetry.log_event(
                'job_completed',
                {
                    'job_id': job_id,
                    'status': result.status,
                    'duration_seconds': duration,
                    'rows_affected': result.rows_affected
                },
                job_id=job_id,
                severity='error' if result.status == 'failed' else 'info'
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            # Update job status on failure
            async with self.async_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE queue_system.job_queue
                    SET status = 'failed', completed_at = NOW(),
                        actual_duration_seconds = $1, error_message = $2
                    WHERE job_id = $3
                """, (duration, error_msg, job_id))

            # Log failure
            await self.telemetry.log_event(
                'job_failed',
                {
                    'job_id': job_id,
                    'error': error_msg,
                    'duration_seconds': duration
                },
                job_id=job_id,
                severity='error'
            )

            logger.error(f"Job {job_id} failed: {error_msg}")
            return JobResult(
                job_id=job_id,
                status='failed',
                duration_seconds=duration,
                error_message=error_msg
            )

    async def _execute_ingestion_job(self, config: JobConfig) -> JobResult:
        """Execute an ingestion job with parallel/GPU support"""
        from tools.ingestion.core.ingestion_engine import IngestionEngine

        # Initialize ingestion engine with performance features
        engine = IngestionEngine(
            enable_parallel=config.enable_parallel,
            max_workers=config.max_parallel_workers,
            enable_gpu=config.enable_gpu,
            gpu_memory_limit=config.gpu_memory_mb
        )

        # Start performance monitoring
        perf_monitor = await self.performance_monitor.start_monitoring(f"ingestion_{config.job_id}")

        try:
            # Execute ingestion based on configuration
            if config.config.get('ingestion_type') == 'congress':
                result = await engine.ingest_congress_data(
                    api_key=config.parameters.get('api_key'),
                    start_congress=config.parameters.get('start_congress'),
                    end_congress=config.parameters.get('end_congress')
                )
            elif config.config.get('ingestion_type') == 'members':
                result = await engine.ingest_federal_members()
            elif config.config.get('ingestion_type') == 'govinfo':
                result = await engine.ingest_govinfo_bills(
                    collection=config.parameters.get('collection', 'BILLS')
                )
            else:
                # Custom ingestion
                result = await engine.ingest_custom_data(config.parameters)

            # Get performance metrics
            perf_metrics = await perf_monitor.stop_monitoring()
            system_metrics = await self._get_system_metrics()

            return JobResult(
                job_id=config.job_id,
                status='completed',
                duration_seconds=result.get('duration', 0),
                rows_affected=result.get('records_processed', 0),
                performance_metrics=perf_metrics,
                system_metrics=system_metrics
            )

        except Exception as e:
            perf_metrics = await perf_monitor.stop_monitoring()
            raise e

    async def _execute_query_job(self, config: JobConfig) -> JobResult:
        """Execute a SQL query job"""
        start_time = time.time()

        async with self.async_pool.acquire() as conn:
            try:
                # Get the query to execute
                if config.saved_query_id:
                    # Use saved query
                    query_record = await conn.fetchrow("""
                        SELECT sql_query, parameters FROM queue_system.saved_queries
                        WHERE query_id = $1
                    """, config.saved_query_id)

                    if not query_record:
                        raise ValueError(f"Saved query {config.saved_query_id} not found")

                    sql = query_record['sql_query']
                    # Merge parameters
                    query_params = {**query_record['parameters'], **config.parameters}
                else:
                    # Use direct SQL
                    sql = config.sql_query
                    query_params = config.parameters

                # Execute query
                if sql.strip().upper().startswith(('SELECT', 'WITH')):
                    # SELECT query
                    result = await conn.fetch(sql, *query_params.values())
                    rows_affected = len(result)
                else:
                    # INSERT/UPDATE/DELETE query
                    result = await conn.execute(sql, *query_params.values())
                    rows_affected = self._parse_rows_affected(result)

                duration = time.time() - start_time
                system_metrics = await self._get_system_metrics()

                return JobResult(
                    job_id=config.job_id,
                    status='completed',
                    duration_seconds=duration,
                    rows_affected=rows_affected,
                    system_metrics=system_metrics
                )

            except Exception as e:
                raise e

    async def _execute_backup_job(self, config: JobConfig) -> JobResult:
        """Execute a backup job"""
        # Implementation for backup jobs
        # This would integrate with PostgreSQL backup tools
        pass

    async def _execute_maintenance_job(self, config: JobConfig) -> JobResult:
        """Execute a maintenance job"""
        # Implementation for maintenance jobs (VACUUM, REINDEX, etc.)
        pass

    async def _execute_custom_job(self, config: JobConfig) -> JobResult:
        """Execute a custom job"""
        # Implementation for custom job types
        pass

    def _parse_rows_affected(self, result: str) -> int:
        """Parse rows affected from PostgreSQL result string"""
        # PostgreSQL returns strings like "INSERT 0 5" or "UPDATE 3"
        parts = result.split()
        if len(parts) >= 2 and parts[0] in ('INSERT', 'UPDATE', 'DELETE'):
            try:
                return int(parts[-1])
            except ValueError:
                pass
        return 0

    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_mb': psutil.virtual_memory().used // (1024 * 1024),
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'gpu_available': GPU_AVAILABLE,
            'gpu_count': GPU_COUNT,
            'gpu_memory_used': self._get_gpu_memory_usage() if GPU_AVAILABLE else 0
        }

    def _get_gpu_memory_usage(self) -> int:
        """Get GPU memory usage in MB"""
        if not GPU_AVAILABLE:
            return 0

        try:
            return torch.cuda.memory_allocated() // (1024 * 1024)
        except:
            return 0

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details"""
        async with self.async_pool.acquire() as conn:
            record = await conn.fetchrow("""
                SELECT * FROM queue_system.job_queue WHERE job_id = $1
            """, job_id)

            return dict(record) if record else None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job"""
        async with self.async_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE queue_system.job_queue
                SET status = 'cancelled', completed_at = NOW()
                WHERE job_id = $1 AND status IN ('pending', 'running')
            """, job_id)

            if result.split()[-1] != '0':
                await self.telemetry.log_event(
                    'job_cancelled',
                    {'job_id': job_id},
                    job_id=job_id
                )
                return True

        return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        async with self.async_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'running') as running,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)))
                        FILTER (WHERE status = 'completed') as avg_completion_time
                FROM queue_system.job_queue
                WHERE created_at > NOW() - INTERVAL '24 hours'
            """)

            return dict(stats)

    async def cleanup_old_jobs(self, days: int = 30):
        """Clean up old completed jobs"""
        async with self.async_pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM queue_system.job_queue
                WHERE status IN ('completed', 'failed', 'cancelled')
                AND completed_at < NOW() - INTERVAL '%s days'
            """, days)

    def close(self):
        """Close all connections and pools"""
        if self.connection_pool:
            self.connection_pool.closeall()
        if self.async_pool:
            asyncio.create_task(self.async_pool.close())
        self.executor.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)


class GPUExecutor:
    """GPU execution manager for GPU-accelerated jobs"""

    def __init__(self):
        self.devices = list(range(GPU_COUNT)) if GPU_AVAILABLE else []
        self.memory_limits = {}

    async def execute_gpu_task(self, func: Callable, *args, device_id: int = 0, memory_limit_mb: int = None, **kwargs):
        """Execute a function on GPU"""
        if not GPU_AVAILABLE:
            raise RuntimeError("GPU not available")

        if device_id >= GPU_COUNT:
            raise ValueError(f"Invalid GPU device ID: {device_id}")

        # Set GPU device
        torch.cuda.set_device(device_id)

        # Set memory limit if specified
        if memory_limit_mb:
            torch.cuda.set_per_process_memory_fraction(memory_limit_mb / torch.cuda.get_device_properties(device_id).total_memory * 1024 * 1024)

        # Execute function in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._gpu_wrapper,
            func, args, kwargs, device_id
        )

    def _gpu_wrapper(self, func, args, kwargs, device_id):
        """Wrapper for GPU function execution"""
        torch.cuda.set_device(device_id)
        try:
            return func(*args, **kwargs)
        finally:
            torch.cuda.empty_cache()


class PerformanceMonitor:
    """Performance monitoring for job execution"""

    def __init__(self):
        self.monitors = {}

    async def start_monitoring(self, monitor_id: str) -> str:
        """Start performance monitoring"""
        self.monitors[monitor_id] = {
            'start_time': time.time(),
            'start_cpu': psutil.cpu_percent(),
            'start_memory': psutil.virtual_memory().percent,
            'gpu_start': torch.cuda.memory_allocated() if GPU_AVAILABLE else 0
        }
        return monitor_id

    async def stop_monitoring(self, monitor_id: str) -> Dict[str, Any]:
        """Stop performance monitoring and return metrics"""
        if monitor_id not in self.monitors:
            return {}

        start_data = self.monitors[monitor_id]
        end_time = time.time()

        metrics = {
            'duration_seconds': end_time - start_data['start_time'],
            'cpu_usage_percent': psutil.cpu_percent() - start_data['start_cpu'],
            'memory_usage_percent': psutil.virtual_memory().percent - start_data['start_memory'],
            'gpu_memory_used_mb': (torch.cuda.memory_allocated() - start_data['gpu_start']) // (1024 * 1024) if GPU_AVAILABLE else 0,
            'peak_memory_percent': psutil.virtual_memory().percent
        }

        del self.monitors[monitor_id]
        return metrics


class TelemetryManager:
    """Telemetry and audit logging manager"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config

    async def log_event(self, event_type: str, event_data: Dict[str, Any],
                       source: str = 'queue_manager', severity: str = 'info',
                       job_id: str = None, user_id: str = None):
        """Log a telemetry event"""
        async with asyncpg.create_pool(**self.db_config) as pool:
            async with pool.acquire() as conn:
                await conn.execute("""
                    SELECT queue_system.log_telemetry_event($1, $2, $3, $4, $5, $6)
                """, event_type, json.dumps(event_data), source, severity, job_id, user_id)

    async def get_job_history(self, job_id: str) -> List[Dict[str, Any]]:
        """Get telemetry history for a job"""
        async with asyncpg.create_pool(**self.db_config) as pool:
            async with pool.acquire() as conn:
                records = await conn.fetch("""
                    SELECT * FROM queue_system.telemetry_events
                    WHERE job_id = $1
                    ORDER BY timestamp DESC
                """, job_id)

                return [dict(record) for record in records]


# Global queue manager instance
_queue_manager = None

def get_queue_manager(db_config: Dict[str, Any] = None) -> QueueManager:
    """Get or create global queue manager instance"""
    global _queue_manager

    if _queue_manager is None:
        if db_config is None:
            # Default database configuration
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_NAME', 'openlegislation')
            }

        _queue_manager = QueueManager(db_config)

    return _queue_manager


# Convenience functions for job submission
async def submit_ingestion_job(job_name: str, ingestion_type: str,
                              parameters: Dict[str, Any] = None,
                              enable_parallel: bool = True,
                              enable_gpu: bool = False) -> str:
    """Submit an ingestion job to the queue"""
    manager = get_queue_manager()

    config = JobConfig(
        job_id='',  # Will be set by manager
        job_type='ingestion',
        job_name=job_name,
        parameters=parameters or {},
        config={'ingestion_type': ingestion_type},
        enable_parallel=enable_parallel,
        enable_gpu=enable_gpu
    )

    return await manager.submit_job(config)


async def submit_query_job(job_name: str, sql_query: str = None,
                          saved_query_id: str = None,
                          parameters: Dict[str, Any] = None) -> str:
    """Submit a query job to the queue"""
    manager = get_queue_manager()

    config = JobConfig(
        job_id='',
        job_type='query',
        job_name=job_name,
        sql_query=sql_query,
        saved_query_id=saved_query_id,
        parameters=parameters or {}
    )

    return await manager.submit_job(config)


if __name__ == '__main__':
    # Example usage
    async def main():
        # Submit an ingestion job
        job_id = await submit_ingestion_job(
            'Congress Data Ingestion',
            'congress',
            parameters={'start_congress': 110, 'end_congress': 118},
            enable_parallel=True,
            enable_gpu=True
        )

        print(f"Submitted job: {job_id}")

        # Wait and check status
        await asyncio.sleep(5)
        manager = get_queue_manager()
        status = await manager.get_job_status(job_id)
        print(f"Job status: {status}")

    asyncio.run(main())
