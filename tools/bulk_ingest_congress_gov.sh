#!/bin/bash

# Bulk Ingestion Workflow for Congress.gov Data - Universal Database
# This script orchestrates the complete pipeline:
# 1. Download govinfo bulk data (samples or full)
# 2. Transform and map data using Python connector
# 3. Ingest into unified OpenLegislation database schema

set -e  # Exit on any error

# Configuration
CONGRESS_RANGE=${CONGRESS_RANGE:-119}
COLLECTIONS=${COLLECTIONS:-"BILLS BILLSTATUS BILLSUM"}
SESSIONS=${SESSIONS:-"1"}
OUTPUT_DIR=${OUTPUT_DIR:-/tmp/govinfo_ingest}
FULL_DOWNLOAD=${FULL_DOWNLOAD:-false}
BATCH_SIZE=${BATCH_SIZE:-100}
DB_CONFIG=${DB_CONFIG:-tools/db_config.json}
LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "=== Congress.gov Bulk Data Ingestion Workflow (Universal Database) ==="
echo "Congress Range: $CONGRESS_RANGE"
echo "Collections: $COLLECTIONS"
echo "Sessions: $SESSION"
echo "Output Directory: $OUTPUT_DIR"
echo "Full Download: $FULL_DOWNLOAD"
echo "Batch Size: $BATCH_SIZE"
echo "Database Config: $DB_CONFIG"
echo

# Check if database config exists
if [ ! -f "$DB_CONFIG" ]; then
    echo "ERROR: Database config file not found: $DB_CONFIG"
    echo "Copy tools/db_config_template.json to $DB_CONFIG and configure your database settings"
    exit 1
fi

# Check for GPU support if requested
if [ "$USE_GPU" = "true" ]; then
    echo "GPU acceleration enabled - checking NVIDIA drivers..."
    if ! command -v nvidia-smi &> /dev/null; then
        echo "ERROR: NVIDIA drivers not found. Install NVIDIA drivers and CUDA toolkit."
        exit 1
    fi
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
fi

# Step 1: Download data
echo "Step 1: Downloading govinfo bulk data..."

DOWNLOAD_ARGS="--congress-range $CONGRESS_RANGE --collections $COLLECTIONS --sessions $SESSIONS --out $OUTPUT_DIR"

if [ "$FULL_DOWNLOAD" = "true" ]; then
    DOWNLOAD_ARGS="$DOWNLOAD_ARGS --full"
else
    DOWNLOAD_ARGS="$DOWNLOAD_ARGS --samples 5"
fi

python3 tools/fetch_govinfo_bulk.py $DOWNLOAD_ARGS

echo "Downloaded files to: $OUTPUT_DIR"
echo

# Step 2: Verify downloads
echo "Step 2: Verifying downloaded files..."
find "$OUTPUT_DIR" -name "*.xml" | head -10
XML_COUNT=$(find "$OUTPUT_DIR" -name "*.xml" | wc -l)
echo "Found $XML_COUNT XML files total"
echo

# Step 3: Process each collection
echo "Step 3: Processing collections..."

for collection in $COLLECTIONS; do
    collection_dir="$OUTPUT_DIR/${collection,,}"
    if [ -d "$collection_dir" ]; then
        echo "Processing collection: $collection"
        xml_count=$(find "$collection_dir" -name "*.xml" | wc -l)
        echo "Found $xml_count XML files in $collection"

        if [ $xml_count -gt 0 ]; then
            python3 tools/govinfo_data_connector.py \
                --input-dir "$collection_dir" \
                --db-config "$DB_CONFIG" \
                --batch-size "$BATCH_SIZE" \
                --log-level "$LOG_LEVEL"
        fi
    else
        echo "Collection directory not found: $collection_dir"
    fi
done

echo
echo "Step 4: Ingestion complete!"
echo "Processed collections: $COLLECTIONS"
echo

# Step 5: Verification
echo "Step 5: Verifying data ingestion..."

# Check if we can connect to database and run queries
python3 -c "
import json
import psycopg2
import psycopg2.extras

with open('$DB_CONFIG', 'r') as f:
    config = json.load(f)

conn = psycopg2.connect(**config)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Count federal bills by congress
cursor.execute('''
    SELECT congress, COUNT(*) as count
    FROM master.bill
    WHERE data_source = 'federal'
    GROUP BY congress
    ORDER BY congress
''')
congress_counts = cursor.fetchall()

print('Federal bills by congress:')
for row in congress_counts:
    print(f'  Congress {row[\"congress\"]}: {row[\"count\"]} bills')

# Total federal bills
cursor.execute(\"SELECT COUNT(*) as federal_count FROM master.bill WHERE data_source = 'federal'\")
federal_result = cursor.fetchone()
print(f'Total federal bills ingested: {federal_result[\"federal_count\"]}')

# Sample federal bill
cursor.execute('''
    SELECT bill_print_no, title, congress, bill_type
    FROM master.bill
    WHERE data_source = 'federal'
    ORDER BY congress DESC, bill_print_no
    LIMIT 1
''')
sample_bill = cursor.fetchone()
if sample_bill:
    print(f'Sample federal bill: {sample_bill[\"bill_print_no\"]} - {sample_bill[\"title\"][:50]}...')

cursor.close()
conn.close()
"

echo
echo "Next steps:"
echo "1. Review ingested data for accuracy"
echo "2. Run full application to test integration"
echo "3. Monitor database performance with federal data"
echo "4. For production: set FULL_DOWNLOAD=true and adjust congress ranges"
echo "5. Implement federal member ID mapping for sponsors/cosponsors"
echo "6. Enable GPU acceleration with USE_GPU=true for text processing"

echo
echo "=== Universal Database Ingestion Complete ==="