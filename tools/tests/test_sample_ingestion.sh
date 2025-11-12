#!/bin/bash

# Test Script: Sample GovInfo Data Ingestion
# Downloads sample data for Congress 119, ingests it, and validates results

set -e

echo "=== GovInfo Sample Data Ingestion Test ==="

# Configuration
CONGRESS=119
COLLECTION=BILLS
OUTPUT_DIR=/tmp/govinfo_test_sample
DB_CONFIG=${DB_CONFIG:-tools/db_config.json}
SAMPLES=3

echo "Congress: $CONGRESS"
echo "Collection: $COLLECTION"
echo "Output: $OUTPUT_DIR"
echo "Samples: $SAMPLES"
echo

# Check database config
if [ ! -f "$DB_CONFIG" ]; then
    echo "ERROR: Database config not found: $DB_CONFIG"
    echo "Please create $DB_CONFIG with database connection details"
    exit 1
fi

# Clean previous test data
echo "Cleaning previous test data..."
rm -rf "$OUTPUT_DIR"

# Step 1: Download sample data
echo "Step 1: Downloading sample data..."
python3 tools/fetch_govinfo_bulk.py \
    --collections "$COLLECTION" \
    --congress-range "$CONGRESS" \
    --sessions 1 \
    --out "$OUTPUT_DIR" \
    --samples "$SAMPLES"

echo "Downloaded to: $OUTPUT_DIR"
echo

# Step 2: Verify downloads
echo "Step 2: Verifying downloads..."
XML_COUNT=$(find "$OUTPUT_DIR" -name "*.xml" | wc -l)
echo "Found $XML_COUNT XML files"

if [ $XML_COUNT -eq 0 ]; then
    echo "ERROR: No XML files downloaded"
    exit 1
fi

echo

# Step 3: Clean existing test data
echo "Step 3: Cleaning existing federal test data..."
python3 -c "
import json
import psycopg2

with open('$DB_CONFIG', 'r') as f:
    config = json.load(f)

conn = psycopg2.connect(**config)
cursor = conn.cursor()

# Delete test data
cursor.execute('DELETE FROM master.bill WHERE congress = $CONGRESS AND data_source = \"federal\"')
conn.commit()

cursor.close()
conn.close()
print('Cleaned existing test data')
"

echo

# Step 4: Ingest data
echo "Step 4: Ingesting data..."
python3 tools/govinfo_data_connector.py \
    --input-dir "$OUTPUT_DIR" \
    --db-config "$DB_CONFIG" \
    --batch-size 10 \
    --log-level INFO

echo

# Step 5: Validate ingestion
echo "Step 5: Validating ingestion results..."
python3 -c "
import json
import psycopg2
import psycopg2.extras

with open('$DB_CONFIG', 'r') as f:
    config = json.load(f)

conn = psycopg2.connect(**config)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

print('=== Ingestion Validation Results ===')

# Count federal bills for congress
cursor.execute('''
    SELECT COUNT(*) as count
    FROM master.bill
    WHERE congress = %s AND data_source = 'federal'
''', ($CONGRESS,))

bill_count = cursor.fetchone()['count']
print(f'Federal bills ingested for Congress {CONGRESS}: {bill_count}')

# Expected should be close to XML_COUNT
xml_count = $XML_COUNT
if abs(bill_count - xml_count) > 2:  # Allow some tolerance for parsing errors
    print(f'WARNING: Bill count ({bill_count}) differs significantly from XML count ({xml_count})')
else:
    print('✓ Bill count matches expected range')

# Check sample bill details
cursor.execute('''
    SELECT bill_print_no, title, bill_type, sponsor_party
    FROM master.bill
    WHERE congress = %s AND data_source = 'federal'
    LIMIT 3
''', ($CONGRESS,))

sample_bills = cursor.fetchall()
print(f'\\nSample bills ({len(sample_bills)}):')
for bill in sample_bills:
    print(f'  {bill[\"bill_print_no\"]}: {bill[\"title\"][:50]}...')

# Check actions
cursor.execute('''
    SELECT COUNT(*) as action_count
    FROM master.bill_amendment_action
    WHERE bill_session_year = %s AND data_source = 'federal'
''', ($CONGRESS,))

action_count = cursor.fetchone()['action_count']
print(f'\\nTotal actions: {action_count}')

# Check sponsors
cursor.execute('''
    SELECT COUNT(*) as sponsor_count
    FROM master.bill_sponsor
    WHERE bill_session_year = %s AND data_source = 'federal'
''', ($CONGRESS,))

sponsor_count = cursor.fetchone()['sponsor_count']
print(f'Total sponsors: {sponsor_count}')

cursor.close()
conn.close()

print('\\n=== Test Summary ===')
if bill_count > 0:
    print('✓ SUCCESS: Sample ingestion test passed')
    print(f'  - Ingested {bill_count} bills')
    print(f'  - Recorded {action_count} actions')
    print(f'  - Recorded {sponsor_count} sponsors')
else:
    print('✗ FAILED: No bills ingested')
    exit(1)
"

echo
echo "=== Sample Ingestion Test Complete ==="
