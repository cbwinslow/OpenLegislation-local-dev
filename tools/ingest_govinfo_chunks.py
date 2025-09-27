#!/usr/bin/env python3
# Ingest GovInfo data in chunks by congress/collection, with resume capability.

import json
import os
import time
from typing import Dict, List, Optional
import requests
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

LOG_FILE = Path("ingestion_log.json")
BATCH_SIZE = 50  # API limit per call
DELAY = 1  # Sec between calls to respect rate limits

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'openlegdb'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASS', 'defaultpass')
    )

def load_progress() -> Dict:
    """Load progress from log file."""
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    return {"congress": 113, "collection": "BILLS", "offset": 0, "completed": {}, "total_ingested": 0}

def save_progress(progress: Dict):
    """Save progress to log file."""
    with open(LOG_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def ingest_collection(congress: int, collection: str, limit: int = BATCH_SIZE, api_key: str = os.getenv('GOVINFO_API_KEY')):
    """Ingest one chunk for congress/collection."""
    url = f"https://api.govinfo.gov/v1/search?collection={collection}&congress={congress}&limit={limit}&offset=0&api_key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            results = data.get("search", {}).get("results", [])
            ingested = 0
            with get_db_connection() as conn:
                cur = conn.cursor()
                for result in results:
                    pkgid = result.get('pkgid')
                    title = result.get('title', '')
                    if pkgid:
                        # Upsert check
                        cur.execute("SELECT 1 FROM bill WHERE govinfo_pkg_id = %s LIMIT 1;", (pkgid,))
                        if not cur.fetchone():
                            # Insert (map to bill table)
                            cur.execute("""
                                INSERT INTO bill (govinfo_pkg_id, title, congress_number, data_source) 
                                VALUES (%s, %s, %s, 'GOVINFO') 
                                ON CONFLICT (govinfo_pkg_id) DO NOTHING;
                            """, (pkgid, title, congress))
                            ingested += 1
                conn.commit()
            return ingested
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return 0
    except Exception as e:
        print(f"Exception: {e}")
        return 0

def main(start_congress: int = 113, end_congress: int = 119, collection: str = "BILLS"):
    api_key = os.getenv('GOVINFO_API_KEY')
    if not api_key or api_key == 'dummy':
        print("Warning: GOVINFO_API_KEY not set or dummy; using public metadata only.")
    progress = load_progress()
    current_congress = progress.get("congress", start_congress)
    current_offset = progress.get("offset", 0)
    completed = progress.get("completed", {})
    total_ingested = progress.get("total_ingested", 0)

    for congress in range(max(start_congress, current_congress), end_congress + 1):
        if congress in completed:
            print(f"Congress {congress} completed, skipping.")
            continue

        offset = current_offset if congress == current_congress else 0
        congress_ingested = 0

        while True:
            count = ingest_collection(congress, collection, BATCH_SIZE, api_key)
            if count == 0:
                break
            congress_ingested += count
            total_ingested += count
            offset += BATCH_SIZE
            time.sleep(DELAY)  # Rate limit

        completed[congress] = {"total": congress_ingested, "offset": offset}
        progress = {"congress": congress + 1, "collection": collection, "offset": 0, "completed": completed, "total_ingested": total_ingested}
        save_progress(progress)
        print(f"Completed congress {congress}: {congress_ingested} new items. Total: {total_ingested}")

    print(f"Ingestion complete! Total ingested: {total_ingested}")

if __name__ == "__main__":
    main()
