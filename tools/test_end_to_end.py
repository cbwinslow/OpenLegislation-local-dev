#!/usr/bin/env python3

"""
End-to-end test script for federal members ingestion.
Fetches small sample from congress.gov, maps, optionally inserts to remote DB.

Usage:
    python3 test_end_to_end.py --api_key YOUR_KEY [--insert] [--congress 118]

Requirements:
    pip install requests psycopg2-binary

Tests:
- Fetch 5 members (senate).
- Map to entities.
- If --insert: Connect to remote DB (100.90.23.59), insert to federal_members table (creates if not exists).
- Verify: Print count, sample; check DB if inserted.
"""

import argparse
import json
import sys
from tools.fetch_congress_members import fetch_all_members, map_to_entity
import psycopg2
from tools.db_config import get_connection_params


def create_table_if_not_exists():
    """Create federal_members table on remote DB if missing."""
    params = get_connection_params()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS federal_members (
            guid VARCHAR PRIMARY KEY,
            fullName VARCHAR(255),
            chamber VARCHAR(50),
            party VARCHAR(50),
            state VARCHAR(50),
            json_data JSONB
        );
    """
    )
    conn.commit()
    cur.close()
    conn.close()
    print("Table federal_members ensured.")


def insert_sample(entities):
    """Insert entities to DB."""
    create_table_if_not_exists()
    params = get_connection_params()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()

    inserted = 0
    for entity in entities:
        guid = entity["guid"]
        json_data = json.dumps({k: v for k, v in entity.items() if k not in ["guid"]})
        cur.execute(
            """
            INSERT INTO federal_members (guid, fullName, chamber, party, state, json_data)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (guid) DO UPDATE SET json_data = EXCLUDED.json_data
        """,
            (
                guid,
                entity.get("fullName"),
                entity.get("chamber"),
                entity.get("party"),
                entity.get("state"),
                json_data,
            ),
        )
        inserted += 1

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM federal_members;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"Inserted/updated {inserted} members. Total in DB: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end test for members ingestion"
    )
    parser.add_argument("--api_key", required=True, help="Congress.gov API key")
    parser.add_argument("--insert", action="store_true", help="Insert to remote DB")
    parser.add_argument("--congress", type=int, default=118, help="Congress number")
    parser.add_argument("--limit", type=int, default=5, help="Sample size (default 5)")

    args = parser.parse_args()

    print("Step 1: Fetching sample members...")
    # Modify fetch to limit (hack: set LIMIT in script or here)
    with patch.dict("tools.fetch_congress_members.__dict__", {"LIMIT": args.limit}):
        members = fetch_all_members(
            args.congress, chamber="senate", api_key=args.api_key
        )

    if not members:
        print("No members fetched. Check API key/network.")
        sys.exit(1)

    print(f"Fetched {len(members)} members.")

    print("Step 2: Mapping to entities...")
    entities = []
    for member in members:
        # Basic map (add details if needed)
        basic_data = {"basic": member}
        entity = map_to_entity(basic_data)
        entities.append(entity)

    print(f"Mapped {len(entities)} entities.")
    print("Sample entity:")
    print(json.dumps(entities[0], indent=2))

    if args.insert:
        print("Step 3: Inserting to remote DB...")
        try:
            insert_sample(entities)
            print("End-to-end success: Fetched, mapped, inserted!")
        except Exception as e:
            print(f"DB insert failed: {e}")
            print("Check Tailscale connection, DB creds, table schema.")
    else:
        print("End-to-end test complete (fetch/map). Run with --insert for DB.")


if __name__ == "__main__":
    main()
