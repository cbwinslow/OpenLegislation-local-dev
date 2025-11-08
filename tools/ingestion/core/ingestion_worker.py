#!/usr/bin/env python3
"""
Ingestion Worker: Polls Redis queue and executes jobs asynchronously.
Runs as daemon/service; processes pending/scheduled jobs.
Integrates with ingest_federal_data.py via subprocess or direct call.
"""

import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, Any

import redis
from dotenv import load_dotenv
from dateutil.parser import parse as parse_datetime

load_dotenv()

# Redis config
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

QUEUE_NAME = 'ingestion_queue'
DEAD_LETTER_QUEUE = 'ingestion_dlq'
PROCESSED_QUEUE = 'ingestion_processed'

def process_job(job_str: str):
    """Execute a single job from queue."""
    job = json.loads(job_str)
    job_id = job['id']
    job_type = job['type']
    params = job['params']
    schedule_time = job.get('schedule_time')

    if schedule_time and datetime.utcnow() < parse_datetime(schedule_time):
        return False  # Not ready

    try:
        # Update status
        job['status'] = 'processing'
        job['started_at'] = datetime.utcnow().isoformat()
        redis_client.lpush(PROCESSED_QUEUE, json.dumps(job))  # Move to processed for tracking

        # Execute ingestion
        cmd = ['python3', 'tools/ingest_federal_data.py', '--type', job_type]
        for k, v in params.items():
            cmd.extend([f'--{k.replace("_", "-")}', str(v)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1hr timeout

        job['status'] = 'completed' if result.returncode == 0 else 'failed'
        job['ended_at'] = datetime.utcnow().isoformat()
        job['output'] = result.stdout
        job['error'] = result.stderr if result.returncode != 0 else None

        # Log to processed
        redis_client.lpush(PROCESSED_QUEUE, json.dumps(job))

        print(f"Job {job_id} ({job_type}) {'completed' if job['status'] == 'completed' else 'failed'}")

        return True

    except subprocess.TimeoutExpired:
        job['status'] = 'timeout'
        redis_client.lpush(DEAD_LETTER_QUEUE, json.dumps(job))
        print(f"Job {job_id} timed out")
        return False
    except Exception as e:
        job['status'] = 'error'
        job['error'] = str(e)
        redis_client.lpush(DEAD_LETTER_QUEUE, json.dumps(job))
        print(f"Job {job_id} error: {e}")
        return False

def worker_loop(poll_interval: int = 30):
    """Main worker loop: Poll queue every poll_interval seconds."""
    while True:
        # Check list queue (immediate)
        job_str = redis_client.brpop(QUEUE_NAME, timeout=poll_interval)
        if job_str:
            _, job_str = job_str  # brpop returns (key, value)
            process_job(job_str)

        # Check sorted set for scheduled (ZPOPMIN for earliest)
        scheduled = redis_client.zpopmin(QUEUE_NAME, count=1)
        if scheduled:
            for score, job_str in scheduled:
                process_job(job_str)

        time.sleep(poll_interval)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingestion Worker")
    parser.add_argument('--poll-interval', type=int, default=30, help="Poll interval in seconds")
    args = parser.parse_args()

    print(f"Starting ingestion worker (poll: {args.poll_interval}s)")
    worker_loop(args.poll_interval)