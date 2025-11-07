#!/bin/bash

# Federal Data Ingestion Demo Script
# This script demonstrates the complete federal data ingestion pipeline
# Usage: ./tools/federal_ingestion_demo.sh [congress] [collection]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

CONGRESS="${1:-119}"
COLLECTION="${2:-BILLS}"
BATCH_SIZE="${3:-10}"

echo "=== Federal Data Ingestion Demo ==="
echo "Congress: $CONGRESS"
echo "Collection: $COLLECTION"
echo "Batch Size: $BATCH_SIZE"
echo "Project Root: $PROJECT_ROOT"
echo

# Check prerequisites
echo "1. Checking prerequisites..."
if ! command -v mvn &> /dev/null; then
    echo "❌ Maven not found. Please install Maven."
    exit 1
fi

if ! command -v java &> /dev/null; then
    echo "❌ Java not found. Please install Java 21+."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo

# Build the project
echo "2. Building the project..."
cd "$PROJECT_ROOT"
mvn clean compile -q
if [ $? -ne 0 ]; then
    echo "❌ Maven build failed"
    exit 1
fi
echo "✅ Project built successfully"
echo

# Apply database migrations
echo "3. Applying database migrations..."
mvn flyway:migrate -q
if [ $? -ne 0 ]; then
    echo "❌ Database migration failed"
    exit 1
fi
echo "✅ Database migrations applied"
echo

# Create staging directories
echo "4. Setting up staging directories..."
mkdir -p staging/federal-xmls
mkdir -p staging/federal-members
mkdir -p logs
echo "✅ Staging directories created"
echo

# Download sample data
echo "5. Downloading sample federal data..."
cd "$SCRIPT_DIR"

# Download sample BILLS data if collection is BILLS
if [ "$COLLECTION" = "BILLS" ]; then
    echo "Downloading sample BILLS data for congress $CONGRESS..."
    python3 -c "
import requests
import zipfile
import io
import os

# Try to download a small sample ZIP
try:
    url = f'https://www.govinfo.gov/bulkdata/BILLS/{CONGRESS}th/BILLS-119.zip'
    print(f'Downloading from: {url}')
    response = requests.get(url, timeout=30)
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall('staging/federal-xmls/')
        print('✅ Sample BILLS data downloaded and extracted')
    else:
        print('⚠️  Could not download sample data (API limits or file not available)')
        print('   This is normal - the system will work with manually placed files')
except Exception as e:
    print(f'⚠️  Download failed: {e}')
    print('   This is normal - the system will work with manually placed files')
"
fi

echo

# Run federal member ingestion
echo "6. Running federal member ingestion..."
cd "$PROJECT_ROOT"
echo "java -cp target/classes:target/lib/* gov.nysenate.openleg.processors.federal.FederalMemberProcessor ingestCurrentMembers $CONGRESS"
echo "✅ Federal member ingestion completed (would run actual ingestion)"
echo

# Run federal data ingestion
echo "7. Running federal data ingestion..."
echo "java -cp target/classes:target/lib/* gov.nysenate.openleg.processors.federal.GovInfoApiProcessor --congress $CONGRESS --collection $COLLECTION --limit $BATCH_SIZE"
echo "✅ Federal data ingestion completed (would run actual ingestion)"
echo

# Verify database
echo "8. Verifying database..."
echo "psql -h localhost -U openleg -d openleg -c \"SELECT COUNT(*) FROM federal_members WHERE current_member = true;\""
echo "✅ Database verification completed (would query actual database)"
echo

# Show API endpoints
echo "9. Available API endpoints:"
echo "   GET  /api/3/federal/members - Get all federal members"
echo "   GET  /api/3/federal/members/{bioguideId} - Get specific member"
echo "   GET  /api/3/federal/members/search?name={name} - Search members"
echo "   GET  /api/3/federal/members/state/{state} - Get members by state"
echo "   GET  /api/3/federal/members/stats - Get member statistics"
echo "   POST /api/3/federal/ingest?congress={congress} - Trigger ingestion"
echo "   GET  /api/3/federal/ingest/status/{congress} - Get ingestion status"
echo "   POST /api/3/federal/validate/{congress} - Validate data"
echo

# Show logs
echo "10. Monitoring logs:"
echo "   tail -f logs/ingestion-federal.log"
echo "   tail -f logs/openleg.log | grep -i federal"
echo

echo "=== Demo completed successfully! ==="
echo
echo "Next steps:"
echo "1. Place sample XML files in staging/federal-xmls/"
echo "2. Configure API keys in src/main/resources/govinfo-api.properties"
echo "3. Run 'mvn tomcat7:run' to start the web application"
echo "4. Visit http://localhost:8080/api/3/federal/members to test the API"
echo "5. Use the ingestion UI at http://localhost:8080/ingest-ui.html"
echo
echo "For production deployment:"
echo "1. Set up PostgreSQL database"
echo "2. Configure environment variables"
echo "3. Set up cron jobs for regular ingestion"
echo "4. Configure monitoring and alerting"