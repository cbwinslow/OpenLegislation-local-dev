#!/usr/bin/env python3

"""
Bulk ingestion script for GovInfo federal data.
Expands to all collections: BILLS, PLAW, CRPT, CREC, CHRT, CCAL, NOM, FR, CFR.
Downloads ZIPs for given congress, extracts to staging, triggers processing.
Supports bills/laws (Phase 2); template for others.

Usage:
    python3 bulk_ingest_govinfo.py --congress 118 --collections BILLS,PLAW --output_dir staging/federal --db_host localhost

Requirements:
    pip install requests psycopg2-binary
"""

import argparse
import os
import requests
import zipfile
import io
from pathlib import Path

from tools.db_config import get_connection_params
import psycopg2

STAGING_BASE = "staging/federal"
COLLECTIONS = {
    'BILLS': 'BILLS',
    'PLAW': 'PLAW',
    'CRPT': 'CRPT',
    'CREC': 'CREC',
    'CHRT': 'CHRT',
    'CCAL': 'CCAL',
    'NOM': 'NOMINATIONS',
    'FR': 'FEDERAL-REGISTER',
    'CFR': 'CFR'
}

def download_collection(congress, collection):
    url = f"https://www.govinfo.gov/bulkdata/LIV/{congress}/{COLLECTIONS[collection]}"
    # List files or direct ZIP; for simplicity, assume known ZIP
    zip_url = f"{url}/{collection}-{congress}thCongress-1stSession.zip"  # Adjust
    resp = requests.get(zip_url)
    resp.raise_for_status()
    return resp.content

def extract_and_process(congress, collection, zip_content, staging_dir):
    with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
        z.extractall(staging_dir / collection.lower())
    # Trigger processing (e.g., call API or processor)
    print(f"Extracted {collection} to {staging_dir / collection.lower()}")

def main():
    parser = argparse.ArgumentParser(description="Bulk ingest GovInfo collections")
    parser.add_argument('--congress', type=int, default=118)
    parser.add_argument('--collections', nargs='+', default=['BILLS', 'PLAW'])
    parser.add_argument('--output_dir', default=STAGING_BASE)
    args = parser.parse_args()

    staging_dir = Path(args.output_dir)
    staging_dir.mkdir(exist_ok=True)

    for collection in args.collections:
        print(f"Downloading {collection} for congress {args.congress}")
        zip_content = download_collection(args.congress, collection)
        extract_and_process(args.congress, collection, zip_content, staging_dir)
        # Process: e.g., for BILLS, call FederalBillXmlProcessor; for PLAW, FederalLawXmlProcessor
        print(f"Processed {collection}")

if __name__ == "__main__":
    main()