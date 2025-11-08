#!/usr/bin/env python3
"""
OpenLegislation Ingestion Engine

High-performance ingestion engine with support for:
- GPU acceleration for data processing
- Parallel and async processing
- Multi-threading and multiprocessing
- Real-time performance monitoring
- Scalable architecture for large datasets

Author: OpenLegislation Team
Date: 2025-11-08
"""

import asyncio
import concurrent.futures
import json
import logging
import multiprocessing
import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import aiohttp
import psutil
import requests
from tqdm.asyncio import tqdm

# GPU Support (optional)
try:
    import torch
    import torch.cuda
    import cudf  # RAPIDS cuDF for GPU DataFrames
    import cupy as cp  # CuPy for GPU arrays
    GPU_AVAILABLE = torch.cuda.is_available()
    GPU_COUNT = torch.cuda.device_count() if GPU_AVAILABLE else 0
    RAPIDS_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    GPU_COUNT = 0
    cudf = None
    cp = None
    RAPIDS_AVAILABLE = False
    torch = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
    """Result of an ingestion operation"""
    records_processed: int = 0
    duration: float = 0.0
    success: bool = True
    errors: List[str] = None
    performance_metrics: Dict[str, Any] = None
    data_quality_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.data_quality_metrics is None:
            self.data_quality_metrics = {}


class IngestionEngine:
    """
    High-performance ingestion engine with GPU/parallel/async support
    """

    def __init__(self, enable_parallel: bool = True, max_workers: int = 4,
                 enable_gpu: bool = False, gpu_memory_limit: int = None,
                 batch_size: int = 1000, timeout: int = 3600):
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.enable_gpu = enable_gpu and GPU_AVAILABLE
        self.gpu_memory_limit = gpu_memory_limit
        self.batch_size = batch_size
        self.timeout = timeout

        # Initialize executors
        self.thread_executor = ThreadPoolExecutor(max_workers=max_workers) if enable_parallel else None
        self.process_executor = ProcessPoolExecutor(max_workers=max_workers // 2) if enable_parallel else None

        # GPU setup
        if self.enable_gpu:
            self._setup_gpu()

        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()

        # Session management for HTTP requests
        self.http_session = None
        self.aiohttp_session = None

        logger.info(f"IngestionEngine initialized: parallel={enable_parallel}, gpu={self.enable_gpu}, workers={max_workers}")

    def _setup_gpu(self):
        """Setup GPU environment"""
        if not GPU_AVAILABLE:
            logger.warning("GPU requested but not available")
            self.enable_gpu = False
            return

        try:
            # Set GPU memory limit
            if self.gpu_memory_limit:
                torch.cuda.set_per_process_memory_fraction(
                    self.gpu_memory_limit / torch.cuda.get_device_properties(0).total_memory
                )

            # Empty cache to start fresh
            torch.cuda.empty_cache()

            logger.info(f"GPU setup complete: {GPU_COUNT} devices available")
        except Exception as e:
            logger.error(f"GPU setup failed: {e}")
            self.enable_gpu = False

    async def __aenter__(self):
        """Async context manager entry"""
        # Create HTTP sessions
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
        self.aiohttp_session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.aiohttp_session:
            await self.aiohttp_session.close()

        # Close executors
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)
        if self.process_executor:
            self.process_executor.shutdown(wait=True)

        # Clean up GPU memory
        if self.enable_gpu and torch:
            torch.cuda.empty_cache()

    async def ingest_congress_data(self, api_key: str = None, start_congress: int = 80,
                                  end_congress: int = 118) -> IngestionResult:
        """
        Ingest congressional data with parallel processing and GPU acceleration
        """
        start_time = time.time()
        monitor_id = await self.performance_monitor.start_monitoring("congress_ingestion")

        try:
            logger.info(f"Starting congress data ingestion: {start_congress}-{end_congress}")

            # Create ingestion tasks
            tasks = []
            for congress_num in range(start_congress, end_congress + 1):
                task = self._ingest_congress_async(congress_num, api_key)
                tasks.append(task)

            # Execute with progress tracking
            results = []
            with tqdm(total=len(tasks), desc="Congress ingestion") as pbar:
                if self.enable_parallel and len(tasks) > 1:
                    # Parallel execution
                    semaphore = asyncio.Semaphore(self.max_workers)

                    async def bounded_task(task_func):
                        async with semaphore:
                            result = await task_func
                            pbar.update(1)
                            return result

                    bounded_tasks = [bounded_task(task) for task in tasks]
                    results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
                else:
                    # Sequential execution
                    for task in tasks:
                        result = await task
                        results.append(result)
                        pbar.update(1)

            # Aggregate results
            total_records = sum(r.records_processed for r in results if isinstance(r, IngestionResult))
            errors = [str(r) for r in results if isinstance(r, Exception)]

            # Performance metrics
            perf_metrics = await self.performance_monitor.stop_monitoring(monitor_id)
            duration = time.time() - start_time

            result = IngestionResult(
                records_processed=total_records,
                duration=duration,
                success=len(errors) == 0,
                errors=errors,
                performance_metrics=perf_metrics
            )

            logger.info(f"Congress ingestion completed: {total_records} records in {duration:.2f}s")
            return result

        except Exception as e:
            await self.performance_monitor.stop_monitoring(monitor_id)
            logger.error(f"Congress ingestion failed: {e}")
            return IngestionResult(success=False, errors=[str(e)])

    async def _ingest_congress_async(self, congress_num: int, api_key: str = None) -> IngestionResult:
        """Ingest data for a specific congress number"""
        try:
            # Use GPU acceleration if available
            if self.enable_gpu:
                return await self._gpu_ingest_congress(congress_num, api_key)
            else:
                return await self._cpu_ingest_congress(congress_num, api_key)
        except Exception as e:
            logger.error(f"Failed to ingest congress {congress_num}: {e}")
            return IngestionResult(success=False, errors=[str(e)])

    async def _gpu_ingest_congress(self, congress_num: int, api_key: str = None) -> IngestionResult:
        """GPU-accelerated congress data ingestion"""
        if not RAPIDS_AVAILABLE:
            # Fallback to CPU if RAPIDS not available
            return await self._cpu_ingest_congress(congress_num, api_key)

        try:
            # Fetch data
            bills_data = await self._fetch_congress_bills(congress_num, api_key)

            if not bills_data:
                return IngestionResult(records_processed=0)

            # Process on GPU using RAPIDS
            gpu_start = time.time()

            # Convert to GPU DataFrame
            df = cudf.DataFrame(bills_data)

            # GPU-accelerated data processing
            df = self._gpu_process_bills_dataframe(df)

            # Convert back to CPU for database insertion
            cpu_df = df.to_pandas()

            gpu_time = time.time() - gpu_start

            # Insert to database
            records_inserted = await self._insert_bills_batch(cpu_df.to_dict('records'))

            return IngestionResult(
                records_processed=records_inserted,
                performance_metrics={'gpu_processing_time': gpu_time}
            )

        except Exception as e:
            logger.error(f"GPU congress ingestion failed: {e}")
            # Fallback to CPU
            return await self._cpu_ingest_congress(congress_num, api_key)

    def _gpu_process_bills_dataframe(self, df):
        """Process bills dataframe on GPU"""
        # Text processing on GPU
        if 'title' in df.columns:
            df['title_length'] = df['title'].str.len()
            df['title_words'] = df['title'].str.count(' ') + 1

        # Date processing
        if 'introduced_date' in df.columns:
            df['introduced_date'] = cudf.to_datetime(df['introduced_date'])

        # Categorize bill types
        if 'bill_type' in df.columns:
            df['is_resolution'] = df['bill_type'].str.contains('res', case=False)
            df['is_joint'] = df['bill_type'].str.contains('jres|sres', case=False)

        return df

    async def _cpu_ingest_congress(self, congress_num: int, api_key: str = None) -> IngestionResult:
        """CPU-based congress data ingestion"""
        try:
            # Fetch bills data
            bills_data = await self._fetch_congress_bills(congress_num, api_key)

            if not bills_data:
                return IngestionResult(records_processed=0)

            # Process in batches
            total_inserted = 0
            for i in range(0, len(bills_data), self.batch_size):
                batch = bills_data[i:i + self.batch_size]
                inserted = await self._insert_bills_batch(batch)
                total_inserted += inserted

            return IngestionResult(records_processed=total_inserted)

        except Exception as e:
            logger.error(f"CPU congress ingestion failed: {e}")
            raise

    async def _fetch_congress_bills(self, congress_num: int, api_key: str = None) -> List[Dict]:
        """Fetch bills data from Congress.gov API"""
        base_url = f"https://api.congress.gov/v3/bill/{congress_num}"
        params = {'format': 'json'}
        if api_key:
            params['api_key'] = api_key

        try:
            async with self.aiohttp_session.get(base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('bills', [])
                else:
                    logger.warning(f"API request failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Failed to fetch congress {congress_num} bills: {e}")
            return []

    async def _insert_bills_batch(self, bills: List[Dict]) -> int:
        """Insert a batch of bills into the database"""
        # This would integrate with your database layer
        # For now, just return the count
        return len(bills)

    async def ingest_federal_members(self) -> IngestionResult:
        """Ingest federal members data"""
        start_time = time.time()
        monitor_id = await self.performance_monitor.start_monitoring("members_ingestion")

        try:
            logger.info("Starting federal members ingestion")

            # Fetch members data
            members_data = await self._fetch_federal_members()

            if not members_data:
                return IngestionResult(records_processed=0)

            # Process with parallel execution if enabled
            if self.enable_parallel and len(members_data) > self.batch_size:
                # Split into chunks for parallel processing
                chunks = [members_data[i:i + self.batch_size]
                         for i in range(0, len(members_data), self.batch_size)]

                # Process chunks in parallel
                loop = asyncio.get_event_loop()
                tasks = []

                for chunk in chunks:
                    if self.enable_gpu:
                        task = loop.run_in_executor(
                            self.process_executor,
                            self._gpu_process_members_chunk,
                            chunk
                        )
                    else:
                        task = self._process_members_chunk_async(chunk)
                    tasks.append(task)

                results = await asyncio.gather(*tasks)
                total_processed = sum(results)
            else:
                # Sequential processing
                total_processed = await self._process_members_chunk_async(members_data)

            duration = time.time() - start_time
            perf_metrics = await self.performance_monitor.stop_monitoring(monitor_id)

            return IngestionResult(
                records_processed=total_processed,
                duration=duration,
                performance_metrics=perf_metrics
            )

        except Exception as e:
            await self.performance_monitor.stop_monitoring(monitor_id)
            logger.error(f"Federal members ingestion failed: {e}")
            return IngestionResult(success=False, errors=[str(e)])

    async def _fetch_federal_members(self) -> List[Dict]:
        """Fetch federal members data"""
        # Implementation for fetching members data
        # This would call the Congress.gov members API
        return []

    async def _process_members_chunk_async(self, members: List[Dict]) -> int:
        """Process a chunk of members data"""
        # Process and insert members data
        return len(members)

    def _gpu_process_members_chunk(self, members: List[Dict]) -> int:
        """Process members chunk on GPU"""
        # GPU-accelerated processing
        return len(members)

    async def ingest_govinfo_bills(self, collection: str = 'BILLS') -> IngestionResult:
        """Ingest bills from GovInfo.gov"""
        start_time = time.time()
        monitor_id = await self.performance_monitor.start_monitoring("govinfo_ingestion")

        try:
            logger.info(f"Starting GovInfo bills ingestion: {collection}")

            # Fetch GovInfo data
            bills_data = await self._fetch_govinfo_bills(collection)

            if not bills_data:
                return IngestionResult(records_processed=0)

            # Process with GPU acceleration if available
            if self.enable_gpu and RAPIDS_AVAILABLE:
                total_processed = await self._gpu_process_govinfo_bills(bills_data)
            else:
                total_processed = await self._cpu_process_govinfo_bills(bills_data)

            duration = time.time() - start_time
            perf_metrics = await self.performance_monitor.stop_monitoring(monitor_id)

            return IngestionResult(
                records_processed=total_processed,
                duration=duration,
                performance_metrics=perf_metrics
            )

        except Exception as e:
            await self.performance_monitor.stop_monitoring(monitor_id)
            logger.error(f"GovInfo bills ingestion failed: {e}")
            return IngestionResult(success=False, errors=[str(e)])

    async def _fetch_govinfo_bills(self, collection: str) -> List[Dict]:
        """Fetch bills from GovInfo.gov API"""
        # Implementation for GovInfo API
        return []

    async def _gpu_process_govinfo_bills(self, bills: List[Dict]) -> int:
        """Process GovInfo bills on GPU"""
        try:
            # Convert to GPU DataFrame
            df = cudf.DataFrame(bills)

            # GPU processing
            df = self._gpu_process_bills_dataframe(df)

            # Insert to database
            cpu_data = df.to_pandas().to_dict('records')
            return await self._insert_bills_batch(cpu_data)

        except Exception as e:
            logger.error(f"GPU GovInfo processing failed: {e}")
            # Fallback to CPU
            return await self._cpu_process_govinfo_bills(bills)

    async def _cpu_process_govinfo_bills(self, bills: List[Dict]) -> int:
        """Process GovInfo bills on CPU"""
        # Process in batches
        total_inserted = 0
        for i in range(0, len(bills), self.batch_size):
            batch = bills[i:i + self.batch_size]
            inserted = await self._insert_bills_batch(batch)
            total_inserted += inserted

        return total_inserted

    async def ingest_custom_data(self, parameters: Dict[str, Any]) -> IngestionResult:
        """Ingest custom data based on parameters"""
        # Implementation for custom data ingestion
        return IngestionResult(records_processed=0)


class PerformanceMonitor:
    """Performance monitoring for ingestion operations"""

    def __init__(self):
        self.monitors = {}
        self.gpu_available = GPU_AVAILABLE

    async def start_monitoring(self, monitor_id: str) -> str:
        """Start performance monitoring"""
        self.monitors[monitor_id] = {
            'start_time': time.time(),
            'start_cpu': psutil.cpu_percent(),
            'start_memory': psutil.virtual_memory().percent,
            'gpu_start': torch.cuda.memory_allocated() if self.gpu_available else 0,
            'network_start': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        }
        return monitor_id

    async def stop_monitoring(self, monitor_id: str) -> Dict[str, Any]:
        """Stop performance monitoring and return metrics"""
        if monitor_id not in self.monitors:
            return {}

        start_data = self.monitors[monitor_id]
        end_time = time.time()

        # Calculate metrics
        cpu_end = psutil.cpu_percent()
        memory_end = psutil.virtual_memory().percent
        network_end = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

        metrics = {
            'duration_seconds': end_time - start_data['start_time'],
            'cpu_usage_percent': cpu_end,
            'memory_usage_percent': memory_end,
            'memory_peak_percent': psutil.virtual_memory().percent,
            'network_io_mb': (network_end - start_data['network_start']) / (1024 * 1024),
            'gpu_available': self.gpu_available,
            'gpu_memory_used_mb': 0,
            'throughput_records_per_second': 0  # Will be set by caller
        }

        if self.gpu_available:
            gpu_end = torch.cuda.memory_allocated()
            metrics['gpu_memory_used_mb'] = (gpu_end - start_data['gpu_start']) // (1024 * 1024)
            metrics['gpu_utilization_percent'] = torch.cuda.utilization() if hasattr(torch.cuda, 'utilization') else 0

        del self.monitors[monitor_id]
        return metrics


class GPUManager:
    """GPU resource management"""

    def __init__(self):
        self.devices = list(range(GPU_COUNT)) if GPU_AVAILABLE else []
        self.memory_limits = {}

    def get_available_device(self) -> Optional[int]:
        """Get the most available GPU device"""
        if not self.devices:
            return None

        # Find device with most free memory
        best_device = None
        max_free_memory = 0

        for device_id in self.devices:
            if torch.cuda.get_device_properties(device_id).total_memory > max_free_memory:
                free_memory = torch.cuda.get_device_properties(device_id).total_memory - torch.cuda.memory_allocated(device_id)
                if free_memory > max_free_memory:
                    max_free_memory = free_memory
                    best_device = device_id

        return best_device

    def set_memory_limit(self, device_id: int, memory_mb: int):
        """Set memory limit for a device"""
        if device_id in self.devices:
            total_memory = torch.cuda.get_device_properties(device_id).total_memory
            limit_fraction = memory_mb / total_memory
            torch.cuda.set_per_process_memory_fraction(limit_fraction, device_id)
            self.memory_limits[device_id] = memory_mb


# Global instances
_gpu_manager = GPUManager()

def get_gpu_manager() -> GPUManager:
    """Get global GPU manager instance"""
    return _gpu_manager


async def create_ingestion_engine(enable_parallel: bool = True, max_workers: int = 4,
                                 enable_gpu: bool = False, gpu_memory_limit: int = None) -> IngestionEngine:
    """Factory function to create an ingestion engine"""
    engine = IngestionEngine(
        enable_parallel=enable_parallel,
        max_workers=max_workers,
        enable_gpu=enable_gpu,
        gpu_memory_limit=gpu_memory_limit
    )

    # Initialize async context
    await engine.__aenter__()
    return engine


if __name__ == '__main__':
    # Example usage
    async def main():
        async with await create_ingestion_engine(enable_parallel=True, enable_gpu=True) as engine:
            # Test congress data ingestion
            result = await engine.ingest_congress_data(
                api_key="your_api_key",
                start_congress=117,
                end_congress=118
            )

            print(f"Ingestion result: {result.records_processed} records processed in {result.duration:.2f}s")

    asyncio.run(main())
