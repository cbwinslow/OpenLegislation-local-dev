#!/usr/bin/env python3
"""
Ingestion Scheduler using Redis Queue
Enqueues ingestion jobs (e.g., bills for congress 118) for asynchronous/scheduled execution.
Supports scheduling (e.g., run at night); worker (separate script) polls and executes.
Uses .env for Redis/DB/API config.
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any

import redis
from dotenv import load_dotenv
from dateutil.parser import parse as parse_datetime

load_dotenv()  # Load .env from project root

# Redis config from .env
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

QUEUE_NAME = 'ingestion_queue'
DEAD_LETTER_QUEUE = 'ingestion_dlq'
PROCESSED_QUEUE = 'ingestion_processed'

def enqueue_job(job_type: str, params: Dict[str, Any], schedule_time: Optional[str] = None, priority: int = 0):
    """Enqueue job to Redis list (LPUSH for FIFO; score for priority if needed).
    schedule_time: ISO string or 'now' or 'nightly' (e.g., tomorrow 2AM).
    """
    job_id = f"job_{int(datetime.utcnow().timestamp())}"
    schedule_dt = None
    if schedule_time:
        if schedule_time.lower() == 'now':
            schedule_dt = datetime.utcnow()
        elif schedule_time.lower() == 'nightly':
            # Schedule for 2AM next day
            schedule_dt = (datetime.utcnow() + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
        else:
            schedule_dt = parse_datetime(schedule_time)

    job = {
        'id': job_id,
        'type': job_type,
        'params': params,
        'priority': priority,
        'enqueued_at': datetime.utcnow().isoformat(),
        'schedule_time': schedule_dt.isoformat() if schedule_dt else None,
        'status': 'pending'
    }

    # Use sorted set for scheduled/priority (ZADD with score = timestamp or priority)
    if schedule_dt:
        score = schedule_dt.timestamp()
        redis_client.zadd(QUEUE_NAME, {json.dumps(job): score})
    else:
        redis_client.lpush(QUEUE_NAME, json.dumps(job))

    print(f"Enqueued job {job_id} ({job_type}) for {schedule_time or 'immediate'}")

def list_jobs():
    """List pending jobs."""
    jobs = []
    # For list queue
    pending = redis_client.lrange(QUEUE_NAME, 0, -1)
    for p in pending:
        jobs.append(json.loads(p))
    # For sorted set (scheduled)
    scheduled = redis_client.zrange(QUEUE_NAME, 0, -1)
    for s in scheduled:
        jobs.append(json.loads(s))
    return jobs

def main():
    parser = argparse.ArgumentParser(description="Schedule Federal Ingestion Jobs")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Enqueue
    enqueue_parser = subparsers.add_parser('enqueue', help='Enqueue a job')
    enqueue_parser.add_argument('--type', choices=['bills', 'committees'], required=True)
    enqueue_parser.add_argument('--congress', type=int, default=118)
    enqueue_parser.add_argument('--schedule', default='now', help="Schedule time: 'now', 'nightly', or ISO datetime")
    enqueue_parser.add_argument('--priority', type=int, default=0)

    # List
    subparsers.add_parser('list', help='List pending jobs')

    args = parser.parse_args()

    if args.command == 'enqueue':
        params = {'start_congress': args.congress, 'batch_size': 250}
        enqueue_job(args.type, params, args.schedule, args.priority)
    elif args.command == 'list':
        jobs = list_jobs()
        print(json.dumps(jobs, indent=2, default=str))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()