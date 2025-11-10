#!/usr/bin/env python3
"""
Demo: GPU-Accelerated Parallel Legislative Data Ingestion

This script demonstrates the parallel processing capabilities we've built,
showing how the system would orchestrate ingestion from multiple data sources
using async programming, multi-threading, and GPU acceleration.

Run this to see the orchestration in action!
"""

import asyncio
import threading
import time
import random
import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
import psutil
import os

# Simulate GPU detection
try:
    import GPUtil
    GPU_AVAILABLE = len(GPUtil.getAvailable()) > 0
    GPU_COUNT = len(GPUtil.getAvailable())
except:
    GPU_AVAILABLE = False
    GPU_COUNT = 0

# System capabilities
CPU_COUNT = psutil.cpu_count(logical=True)
MEMORY_GB = psutil.virtual_memory().total / (1024**3)

class MockIngestionTask:
    """Mock ingestion task to demonstrate parallel processing"""

    def __init__(self, task_id: str, source: str, data_type: str, gpu_device: int = None):
        self.task_id = task_id
        self.source = source
        self.data_type = data_type
        self.gpu_device = gpu_device
        self.start_time = None
        self.end_time = None
        self.records_processed = 0
        self.status = "pending"

    async def execute_async(self):
        """Execute task asynchronously with simulated processing"""
        self.start_time = time.time()
        self.status = "running"

        print(f"🚀 [{self.task_id}] Starting {self.source} {self.data_type} ingestion"
              f"{' (GPU:' + str(self.gpu_device) + ')' if self.gpu_device is not None else ''}")

        # Simulate API calls, database operations, etc.
        await self._simulate_processing()

        self.end_time = time.time()
        self.status = "completed"
        processing_time = self.end_time - self.start_time

        print(".2f"
              f"{' (GPU:' + str(self.gpu_device) + ')' if self.gpu_device is not None else ''}")

        return {
            'task_id': self.task_id,
            'source': self.source,
            'data_type': self.data_type,
            'records_processed': self.records_processed,
            'processing_time': processing_time,
            'gpu_device': self.gpu_device
        }

    async def _simulate_processing(self):
        """Simulate realistic processing with async operations"""
        # Simulate API rate limiting and network I/O
        await asyncio.sleep(random.uniform(0.1, 0.5))

        # Simulate batch processing
        batch_size = random.randint(50, 200)
        batches = random.randint(3, 10)

        for batch in range(batches):
            # Simulate database I/O
            await asyncio.sleep(random.uniform(0.05, 0.2))

            # Simulate GPU processing if available
            if self.gpu_device is not None:
                await asyncio.sleep(random.uniform(0.02, 0.1))  # Faster with GPU

            self.records_processed += batch_size

            # Simulate occasional errors (5% failure rate)
            if random.random() < 0.05:
                await asyncio.sleep(0.1)  # Error recovery time
                continue

        # Final validation step
        await asyncio.sleep(random.uniform(0.1, 0.3))


class GPUParallelIngestionDemo:
    """Demo of GPU-accelerated parallel ingestion"""

    def __init__(self):
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_records = 0
        self.start_time = None

        print("🎯 GPU-Accelerated Parallel Legislative Data Ingestion Demo")
        print("=" * 70)
        print(f"Hardware Detection: {GPU_COUNT} GPUs, {CPU_COUNT} CPUs, {MEMORY_GB:.1f}GB RAM")
        print(f"GPU Acceleration: {'✅ Available' if GPU_AVAILABLE else '❌ Not Available'}")
        print()

    async def run_demo_ingestion(self, num_workers: int = 6, duration_seconds: int = 30):
        """Run the parallel ingestion demo"""
        print(f"🚀 Starting parallel ingestion demo with {num_workers} workers")
        print(f"Duration: {duration_seconds} seconds")
        print()

        self.start_time = time.time()

        # Start telemetry monitoring
        telemetry_task = asyncio.create_task(self._monitor_telemetry())

        # Start worker tasks
        workers = []
        for i in range(num_workers):
            gpu_device = i % GPU_COUNT if GPU_AVAILABLE else None
            worker = asyncio.create_task(self._run_worker(i, gpu_device, duration_seconds))
            workers.append(worker)

        # Wait for all workers to complete
        results = await asyncio.gather(*workers, return_exceptions=True)
        telemetry_task.cancel()

        # Process results
        await self._process_results(results)

    async def _run_worker(self, worker_id: int, gpu_device: int, duration_seconds: int):
        """Run a single worker that processes tasks"""
        worker_results = []

        end_time = time.time() + duration_seconds

        while time.time() < end_time:
            # Create mock tasks simulating different data sources
            sources = ['congress_api', 'govinfo_bulk', 'openstates', 'openlegislature']
            data_types = ['bills', 'committees', 'members', 'votes', 'actions']

            source = random.choice(sources)
            data_type = random.choice(data_types)

            task_id = f"worker_{worker_id}_{int(time.time() * 1000)}"

            # Create and execute task
            task = MockIngestionTask(task_id, source, data_type, gpu_device)

            try:
                result = await task.execute_async()
                worker_results.append(result)
                self.tasks_completed += 1
                self.total_records += result['records_processed']

            except Exception as e:
                print(f"❌ Worker {worker_id} task failed: {e}")
                self.tasks_failed += 1

            # Small delay between tasks
            await asyncio.sleep(random.uniform(0.1, 0.3))

        return worker_results

    async def _monitor_telemetry(self):
        """Monitor system telemetry during execution"""
        while True:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent

                gpu_info = ""
                if GPU_AVAILABLE:
                    try:
                        gpus = GPUtil.getGPUs()
                        gpu_utils = [f"GPU{i}:{gpu.load*100:.1f}%" for i, gpu in enumerate(gpus)]
                        gpu_info = f" | {' '.join(gpu_utils)}"
                    except:
                        gpu_info = " | GPU: monitoring..."

                elapsed = time.time() - self.start_time
                print(f"📊 [{elapsed:.1f}s] CPU:{cpu_percent:.1f}% MEM:{memory_percent:.1f}%{gpu_info} | "
                      f"Tasks: {self.tasks_completed} completed, {self.total_records} records")

                await asyncio.sleep(5)  # Update every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Telemetry error: {e}")
                await asyncio.sleep(5)

    async def _process_results(self, results):
        """Process and display final results"""
        print("\n" + "=" * 70)
        print("🎉 INGESTION DEMO COMPLETED")
        print("=" * 70)

        total_time = time.time() - self.start_time

        # Flatten results
        all_results = []
        for worker_results in results:
            if isinstance(worker_results, list):
                all_results.extend(worker_results)

        # Analyze results by source
        source_stats = {}
        gpu_stats = {}

        for result in all_results:
            source = result['source']
            if source not in source_stats:
                source_stats[source] = {'tasks': 0, 'records': 0, 'time': 0}

            source_stats[source]['tasks'] += 1
            source_stats[source]['records'] += result['records_processed']
            source_stats[source]['time'] += result['processing_time']

            # GPU usage stats
            gpu_device = result.get('gpu_device')
            if gpu_device is not None:
                if gpu_device not in gpu_stats:
                    gpu_stats[gpu_device] = {'tasks': 0, 'records': 0}
                gpu_stats[gpu_device]['tasks'] += 1
                gpu_stats[gpu_device]['records'] += result['records_processed']

        # Display results
        print(f"⏱️  Total Runtime: {total_time:.2f} seconds")
        print(f"📈 Tasks Completed: {self.tasks_completed}")
        print(f"❌ Tasks Failed: {self.tasks_failed}")
        print(f"📊 Records Processed: {self.total_records:,}")
        print(f"⚡ Throughput: {self.total_records / total_time:.0f} records/second")
        print()

        print("📋 Source Breakdown:")
        for source, stats in source_stats.items():
            avg_time = stats['time'] / stats['tasks'] if stats['tasks'] > 0 else 0
            print(f"  {source}: {stats['tasks']} tasks, {stats['records']:,} records, "
                  f"{avg_time:.2f}s avg")

        if gpu_stats:
            print("\n🎮 GPU Utilization:")
            for gpu_id, stats in gpu_stats.items():
                print(f"  GPU {gpu_id}: {stats['tasks']} tasks, {stats['records']:,} records")

        print("\n✅ Demo completed successfully!")
        print("💡 The real GPU orchestrator would process actual legislative data")
        print("   from Congress.gov API, GovInfo bulk data, OpenStates, and OpenLegislature")


async def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="GPU-Accelerated Parallel Ingestion Demo")
    parser.add_argument('--workers', type=int, default=6,
                       help='Number of parallel workers')
    parser.add_argument('--duration', type=int, default=30,
                       help='Demo duration in seconds')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')

    args = parser.parse_args()

    demo = GPUParallelIngestionDemo()
    await demo.run_demo_ingestion(args.workers, args.duration)


if __name__ == "__main__":
    print("🎯 GPU-Accelerated Parallel Legislative Data Ingestion Demo")
    print("This demo shows how the system processes legislative data using:")
    print("  • Async programming with asyncio")
    print("  • Multi-threading for I/O operations")
    print("  • GPU acceleration for data processing")
    print("  • Real-time telemetry and monitoring")
    print()

    asyncio.run(main())
