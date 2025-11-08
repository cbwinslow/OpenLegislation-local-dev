#!/bin/bash

# Production Congress.gov Data Ingestion Script
# Designed for homelab server with NVIDIA K80/K40 GPUs
# Run full ingestion of all congresses and collections

set -e

# Configuration - Modify these for your environment
CONGRESS_RANGE=${CONGRESS_RANGE:-"93-119"}  # Full historical range
COLLECTIONS=${COLLECTIONS:-"BILLS BILLSTATUS BILLSUM"}
SESSIONS=${SESSIONS:-"1 2"}
OUTPUT_BASE=${OUTPUT_BASE:-"/data/govinfo_bulk"}  # Large storage location
DB_CONFIG=${DB_CONFIG:-"/home/ubuntu/openleg/tools/db_config.json"}
LOG_DIR=${LOG_DIR:-"/var/log/govinfo_ingest"}
BATCH_SIZE=${BATCH_SIZE:-500}
USE_GPU=${USE_GPU:-true}
PARALLEL_JOBS=${PARALLEL_JOBS:-4}  # Number of parallel processing jobs

echo "=== Production Congress.gov Data Ingestion ==="
echo "Congress Range: $CONGRESS_RANGE"
echo "Collections: $COLLECTIONS"
echo "Sessions: $SESSIONS"
echo "Output Base: $OUTPUT_BASE"
echo "Batch Size: $BATCH_SIZE"
echo "GPU Enabled: $USE_GPU"
echo "Parallel Jobs: $PARALLEL_JOBS"
echo

# Create directories
sudo mkdir -p "$OUTPUT_BASE"
sudo mkdir -p "$LOG_DIR"
sudo chown -R ubuntu:ubuntu "$OUTPUT_BASE" "$LOG_DIR"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_DIR/production_ingest.log"
}

# Check prerequisites
log "Checking prerequisites..."

# Check database connection
if ! python3 -c "
import json
import psycopg2
with open('$DB_CONFIG') as f:
    config = json.load(f)
conn = psycopg2.connect(**config)
conn.close()
print('Database connection OK')
"; then
    log "ERROR: Database connection failed"
    exit 1
fi

# Check GPU if enabled
if [ "$USE_GPU" = "true" ]; then
    if ! command -v nvidia-smi &> /dev/null; then
        log "ERROR: GPU requested but nvidia-smi not found"
        exit 1
    fi
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    log "GPU check passed"
fi

# Check available disk space (need at least 2TB free)
AVAILABLE_SPACE=$(df "$OUTPUT_BASE" | tail -1 | awk '{print $4}')
if [ $AVAILABLE_SPACE -lt 2000000000 ]; then  # 2TB in KB
    log "ERROR: Insufficient disk space. Need at least 2TB free."
    exit 1
fi

log "Prerequisites check passed"

# Phase 1: Download all data
log "Phase 1: Starting bulk data download..."

DOWNLOAD_START=$(date +%s)
python3 tools/fetch_govinfo_bulk.py \
    --collections $COLLECTIONS \
    --congress-range $CONGRESS_RANGE \
    --sessions $SESSIONS \
    --out "$OUTPUT_BASE" \
    --full \
    --log-level INFO 2>&1 | tee -a "$LOG_DIR/download.log"

DOWNLOAD_END=$(date +%s)
DOWNLOAD_TIME=$((DOWNLOAD_END - DOWNLOAD_START))
log "Download completed in $DOWNLOAD_TIME seconds"

# Count downloaded files
TOTAL_XML=$(find "$OUTPUT_BASE" -name "*.xml" | wc -l)
log "Total XML files downloaded: $TOTAL_XML"

# Phase 2: Process collections in parallel
log "Phase 2: Starting parallel data processing..."

PROCESS_START=$(date +%s)

# Function to process a single collection
process_collection() {
    local collection=$1
    local collection_dir="$OUTPUT_BASE/${collection,,}"
    local log_file="$LOG_DIR/process_${collection}.log"

    log "Processing collection: $collection"

    if [ -d "$collection_dir" ]; then
        local xml_count=$(find "$collection_dir" -name "*.xml" | wc -l)
        log "Found $xml_count XML files in $collection"

        if [ $xml_count -gt 0 ]; then
            python3 tools/govinfo_data_connector.py \
                --input-dir "$collection_dir" \
                --db-config "$DB_CONFIG" \
                --batch-size $BATCH_SIZE \
                --log-level INFO \
                --continue-on-error true \
                2>&1 | tee "$log_file"
        fi
    else
        log "Collection directory not found: $collection_dir"
    fi
}

# Export function for parallel execution
export -f process_collection
export OUTPUT_BASE DB_CONFIG BATCH_SIZE LOG_DIR
export USE_GPU  # Pass GPU flag to Python scripts

# Process collections in parallel
echo "$COLLECTIONS" | tr ' ' '\n' | parallel -j $PARALLEL_JOBS process_collection

PROCESS_END=$(date +%s)
PROCESS_TIME=$((PROCESS_END - PROCESS_START))
log "Processing completed in $PROCESS_TIME seconds"

# Phase 3: Validation and reporting
log "Phase 3: Final validation and reporting..."

python3 -c "
import json
import psycopg2
import psycopg2.extras
from datetime import datetime

with open('$DB_CONFIG', 'r') as f:
    config = json.load(f)

conn = psycopg2.connect(**config)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print('=== FINAL INGESTION REPORT ===')
print(f'Generated: {datetime.now()}')
print()

# Total federal bills
cursor.execute('SELECT COUNT(*) as total FROM master.bill WHERE data_source = \"federal\"')
total_bills = cursor.fetchone()['total']
print(f'Total Federal Bills Ingested: {total_bills:,}')

# Bills by congress
cursor.execute('''
    SELECT congress, COUNT(*) as count
    FROM master.bill
    WHERE data_source = 'federal'
    GROUP BY congress
    ORDER BY congress
''')
congress_counts = cursor.fetchall()

print('\\nBills by Congress:')
for row in congress_counts:
    print(f'  Congress {row[\"congress\"]:3d}: {row[\"count\"]:6,d} bills')

# Actions count
cursor.execute('SELECT COUNT(*) as count FROM master.bill_amendment_action WHERE data_source = \"federal\"')
action_count = cursor.fetchone()['count']
print(f'\\nTotal Actions: {action_count:,}')

# Sponsors count
cursor.execute('SELECT COUNT(*) as count FROM master.bill_sponsor WHERE data_source = \"federal\"')
sponsor_count = cursor.fetchone()['count']
print(f'Total Sponsors: {sponsor_count:,}')

# Committees count
cursor.execute('SELECT COUNT(*) as count FROM master.bill_committee WHERE data_source = \"federal\"')
committee_count = cursor.fetchone()['count']
print(f'Total Committee References: {committee_count:,}')

# Storage usage
cursor.execute('SELECT pg_size_pretty(pg_database_size(current_database())) as db_size')
db_size = cursor.fetchone()['db_size']
print(f'\\nDatabase Size: {db_size}')

cursor.close()
conn.close()

print('\\n=== INGESTION COMPLETE ===')
print(f'Successfully ingested {total_bills:,} federal bills')
print('Data ready for analysis and integration with state legislative data')
" 2>&1 | tee "$LOG_DIR/final_report.log"

# Phase 4: Cleanup and optimization
log "Phase 4: Post-processing cleanup..."

# Vacuum analyze for performance
log "Running database vacuum analyze..."
psql $(python3 -c "
import json
with open('$DB_CONFIG') as f:
    config = json.load(f)
print(f'postgresql://{config[\"user\"]}:{config[\"password\"]}@{config[\"host\"]}:{config[\"port\"]}/{config[\"database\"]}')
") -c "VACUUM ANALYZE;" 2>&1 | tee -a "$LOG_DIR/vacuum.log"

# Optional: Compress raw XML files to save space
# find "$OUTPUT_BASE" -name "*.xml" -exec gzip {} \;

log "Production ingestion completed successfully!"
log "Check $LOG_DIR for detailed logs"
log "Raw data preserved in $OUTPUT_BASE"

# Send completion notification (customize for your setup)
# curl -X POST -H 'Content-type: application/json' \
#      --data '{"text":"Congress.gov ingestion completed successfully!"}' \
#      YOUR_SLACK_WEBHOOK_URL

echo
echo "=== PRODUCTION INGESTION COMPLETE ==="
echo "Total runtime: $(( $(date +%s) - $(date +%s -d "$(date)") )) seconds"
echo "Check logs in: $LOG_DIR"
echo "Raw data location: $OUTPUT_BASE"
