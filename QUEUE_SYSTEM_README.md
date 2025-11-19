# OpenLegislation PostgreSQL Queue System

A comprehensive job queue system for PostgreSQL with GPU acceleration, parallel processing, and advanced monitoring capabilities.

## 🚀 Features

- **Job Queue Management**: Schedule and execute batch ingestion jobs, backups, and SQL queries
- **GPU Acceleration**: Leverage NVIDIA GPUs for data processing with RAPIDS cuDF
- **Parallel Processing**: Multi-threading and multiprocessing for maximum performance
- **Async Operations**: Full async/await support for high concurrency
- **Audit Logging**: Complete audit trail of all queue operations
- **Telemetry**: Structured event logging with severity levels
- **Performance Monitoring**: Real-time metrics collection and benchmarking
- **Job Dependencies**: Support for complex job dependency chains
- **Scheduled Execution**: pg_cron integration for automated job scheduling
- **Error Handling**: Comprehensive error recovery and retry logic

## 📋 Table of Contents

- [Installation](#installation)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Performance Tuning](#performance-tuning)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## 🛠️ Installation

### Prerequisites

- PostgreSQL 12+ with extensions:
  - `uuid-ossp`
  - `pg_cron`
  - `pg_stat_statements`
- Python 3.8+
- Optional GPU support:
  - NVIDIA GPU with CUDA
  - RAPIDS cuDF and CuPy libraries

### Python Dependencies

```bash
pip install asyncpg psycopg2-binary aiohttp tqdm psutil torch cudf cupy
```

### Database Setup

1. Run the database schema setup:

```bash
psql -d your_database -f database_queue_system.sql
```

This creates:
- `queue_system` schema with all necessary tables
- Indexes for performance
- Triggers for audit logging
- Scheduled jobs with pg_cron
- Sample saved queries

## ⚙️ Configuration

### Environment Variables

```bash
# Database Configuration
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_NAME=openlegislation

# API Keys
export CONGRESS_API_KEY=your_congress_api_key

# GPU Configuration (optional)
export CUDA_VISIBLE_DEVICES=0,1  # GPU device IDs
export GPU_MEMORY_LIMIT=4096     # Memory limit in MB
```

### Database Configuration

```python
db_config = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'your_password',
    'database': 'openlegislation'
}
```

## 📖 Usage

### Basic Job Submission

```python
import asyncio
from queue_manager import submit_ingestion_job, submit_query_job

async def main():
    # Submit an ingestion job
    job_id = await submit_ingestion_job(
        job_name="Congress Data Ingestion",
        ingestion_type="congress",
        parameters={
            'start_congress': 110,
            'end_congress': 118,
            'api_key': 'your_api_key'
        },
        enable_parallel=True,
        enable_gpu=True
    )
    print(f"Submitted job: {job_id}")

    # Submit a query job
    query_job_id = await submit_query_job(
        job_name="Bill Count Query",
        sql_query="SELECT COUNT(*) FROM master.bill WHERE congress >= 117"
    )
    print(f"Submitted query job: {query_job_id}")

asyncio.run(main())
```

### Advanced Job Configuration

```python
from queue_manager import QueueManager, JobConfig
from datetime import datetime, timedelta

async def advanced_jobs():
    manager = QueueManager(db_config)

    # Create a custom job configuration
    config = JobConfig(
        job_id='',  # Auto-generated
        job_type='ingestion',
        job_name='Custom Congress Ingestion',
        parameters={
            'start_congress': 80,
            'end_congress': 118,
            'api_key': 'your_key'
        },
        config={
            'description': 'Full historical congress data',
            'priority': 'high'
        },
        enable_parallel=True,
        max_parallel_workers=8,
        enable_gpu=True,
        gpu_memory_mb=2048,
        timeout_seconds=7200  # 2 hours
    )

    # Schedule job to run in 1 hour
    scheduled_time = datetime.now() + timedelta(hours=1)

    job_id = await manager.submit_job(config, scheduled_at=scheduled_time)
    print(f"Scheduled job: {job_id} for {scheduled_time}")

asyncio.run(advanced_jobs())
```

### Job Dependencies

```python
from queue_manager import JobConfig

async def dependent_jobs():
    manager = QueueManager(db_config)

    # Submit parent job
    parent_config = JobConfig(
        job_type='ingestion',
        job_name='Parent Data Load',
        parameters={'source': 'congress', 'congress': 118}
    )
    parent_job = await manager.submit_job(parent_config)

    # Submit dependent job
    dependent_config = JobConfig(
        job_type='query',
        job_name='Post-Load Analysis',
        sql_query='SELECT COUNT(*) FROM master.bill WHERE congress = 118'
    )
    dependent_job = await manager.submit_job(
        dependent_config,
        depends_on=[parent_job]
    )

    print(f"Dependent job {dependent_job} will run after {parent_job}")
```

### GPU-Accelerated Processing

```python
from tools.ingestion.core.ingestion_engine import create_ingestion_engine

async def gpu_processing():
    # Create engine with GPU support
    async with await create_ingestion_engine(
        enable_parallel=True,
        max_workers=4,
        enable_gpu=True,
        gpu_memory_limit=4096  # 4GB GPU memory
    ) as engine:

        result = await engine.ingest_congress_data(
            api_key='your_key',
            start_congress=117,
            end_congress=118
        )

        print(f"Processed {result.records_processed} records in {result.duration:.2f}s")
        print(f"GPU time: {result.performance_metrics.get('gpu_processing_time', 0):.2f}s")
```

## 🔍 Monitoring and Telemetry

### Queue Statistics

```python
from queue_manager import get_queue_manager

async def check_queue_status():
    manager = get_queue_manager()

    # Get current queue statistics
    stats = await manager.get_queue_stats()
    print(f"Pending jobs: {stats.get('pending', 0)}")
    print(f"Running jobs: {stats.get('running', 0)}")
    print(f"Failed jobs: {stats.get('failed', 0)}")

    # Get job status
    job_status = await manager.get_job_status('your-job-id')
    print(f"Job status: {job_status}")
```

### Telemetry Events

```python
# Get telemetry history for a job
telemetry = await manager.telemetry.get_job_history('job-id')
for event in telemetry:
    print(f"{event['timestamp']}: {event['event_type']} - {event['event_data']}")
```

### Performance Benchmarks

```python
# View performance benchmarks
# Check the queue_system.performance_benchmarks table
# or use the monitoring views
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_queue_system.py
```

This will test:
- Job submission and execution
- GPU acceleration
- Parallel processing
- Error handling
- Performance benchmarking
- Queue monitoring

## 📊 Database Schema

### Core Tables

- **`queue_system.job_queue`**: Main job queue
- **`queue_system.saved_queries`**: Reusable SQL queries
- **`queue_system.job_execution_history`**: Execution history
- **`queue_system.audit_log`**: Complete audit trail
- **`queue_system.telemetry_events`**: Event logging
- **`queue_system.performance_benchmarks`**: Performance metrics

### Key Views

- **`queue_system.active_jobs`**: Currently running/pending jobs
- **`queue_system.job_statistics`**: Job type statistics
- **`queue_system.system_health`**: System health metrics

## 🔧 Performance Tuning

### GPU Optimization

1. **Memory Management**:
   ```python
   # Set GPU memory limits
   engine = create_ingestion_engine(gpu_memory_limit=2048)  # 2GB limit
   ```

2. **Multi-GPU Support**:
   ```bash
   export CUDA_VISIBLE_DEVICES=0,1,2,3  # Use GPUs 0-3
   ```

### Parallel Processing

1. **Worker Configuration**:
   ```python
   engine = create_ingestion_engine(
       max_workers=8,  # 8 parallel workers
       enable_parallel=True
   )
   ```

2. **Batch Size Tuning**:
   ```python
   engine = create_ingestion_engine(batch_size=5000)  # Larger batches
   ```

### Database Optimization

1. **Connection Pooling**:
   ```python
   # Configure connection pool sizes
   db_config = {
       'minconn': 5,
       'maxconn': 20
   }
   ```

2. **Indexing**:
   - The schema includes optimized indexes
   - Monitor slow queries with `pg_stat_statements`

## 🚨 Troubleshooting

### Common Issues

1. **GPU Not Available**:
   ```
   ERROR: GPU requested but not available
   ```
   - Install CUDA and RAPIDS
   - Check GPU drivers
   - Set `enable_gpu=False`

2. **Database Connection Failed**:
   ```
   ERROR: Failed to initialize connection pools
   ```
   - Check database credentials
   - Verify PostgreSQL is running
   - Check network connectivity

3. **Job Stuck in Pending**:
   - Check job dependencies
   - Verify scheduled time
   - Check queue processor status

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

```sql
-- Check queue health
SELECT * FROM queue_system.system_health;

-- View active jobs
SELECT * FROM queue_system.active_jobs;

-- Check recent errors
SELECT * FROM queue_system.telemetry_events
WHERE severity = 'error'
AND timestamp > NOW() - INTERVAL '1 hour';
```

## 📈 API Reference

### QueueManager

#### Methods

- `submit_job(config, scheduled_at=None, depends_on=None)`: Submit a job
- `execute_job(job_id)`: Execute a specific job
- `get_job_status(job_id)`: Get job status
- `cancel_job(job_id)`: Cancel a job
- `get_queue_stats()`: Get queue statistics
- `cleanup_old_jobs(days=30)`: Clean up old jobs

### IngestionEngine

#### Methods

- `ingest_congress_data(api_key, start_congress, end_congress)`: Ingest congress data
- `ingest_federal_members()`: Ingest members data
- `ingest_govinfo_bills(collection)`: Ingest GovInfo bills
- `ingest_custom_data(parameters)`: Custom data ingestion

### JobConfig

#### Attributes

- `job_type`: 'ingestion', 'query', 'backup', 'maintenance'
- `job_name`: Human-readable job name
- `sql_query`: Raw SQL query (optional)
- `saved_query_id`: Reference to saved query (optional)
- `parameters`: Job parameters (dict)
- `enable_parallel`: Enable parallel processing
- `max_parallel_workers`: Number of parallel workers
- `enable_gpu`: Enable GPU acceleration
- `gpu_memory_mb`: GPU memory limit

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the troubleshooting section
2. Review the test suite output
3. Check database logs and telemetry
4. Create an issue with detailed information

---

**Note**: This system is designed for high-performance batch processing of legislative data. Always monitor resource usage and adjust configuration based on your hardware capabilities.
