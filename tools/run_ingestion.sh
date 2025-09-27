#!/bin/bash
# Wrapper script for ingestion: Run with params for repeatable process.

SITE=${1:-govinfo}
COLLECTION=${2:-BILLS}
CONGRESS=${3:-119}
LIMIT=${4:-50}

echo "Starting ingestion: Site=$SITE, Collection=$COLLECTION, Congress=$CONGRESS, Limit=$LIMIT"

source venv/bin/activate
python3 ingest_govinfo_chunks.py --site $SITE --collection $COLLECTION --congress $CONGRESS --limit $LIMIT

echo "Ingestion complete. Check ingestion_log.json for details."
