#!/usr/bin/env python3
"""
Simple Test Ingestion Script for OpenLegislation

Tests the ingestion system with sample data without complex dependencies.
Demonstrates that the constraint removal and full ingestion setup works.
"""

import json
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestIngestionTracker:
    """Simple ingestion tracker for testing"""
    
    def __init__(self):
        self.processed = 0
        self.failed = 0
        self.start_time = datetime.now()
    
    def record_success(self, record_id: str):
        self.processed += 1
        logger.info(f"✅ Successfully processed record: {record_id}")
    
    def record_failure(self, record_id: str, error: str):
        self.failed += 1
        logger.error(f"❌ Failed to process record {record_id}: {error}")
    
    def get_summary(self):
        duration = datetime.now() - self.start_time
        return {
            'processed': self.processed,
            'failed': self.failed,
            'duration': str(duration),
            'success_rate': (self.processed / (self.processed + self.failed) * 100) if (self.processed + self.failed) > 0 else 0
        }

def test_agenda_ingestion():
    """Test agenda ingestion with sample data"""
    logger.info("=== Testing Agenda Ingestion ===")
    
    tracker = TestIngestionTracker()
    agenda_dir = Path("staging/govinfo/agendas")
    
    if not agenda_dir.exists():
        logger.error(f"Agenda directory not found: {agenda_dir}")
        return False
    
    # Find all agenda files
    agenda_files = list(agenda_dir.glob("AGENDAS-*.json"))
    logger.info(f"Found {len(agenda_files)} agenda files")
    
    for file_path in agenda_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate agenda structure
            if 'agendaNumber' not in data:
                tracker.record_failure(file_path.stem, "Missing agendaNumber")
                continue
            
            if 'infoAddenda' not in data:
                tracker.record_failure(file_path.stem, "Missing infoAddenda")
                continue
            
            # Simulate processing
            agenda_no = data['agendaNumber']
            year = data.get('year', 'unknown')
            addenda_count = len(data['infoAddenda'])
            
            logger.info(f"Processing agenda {agenda_no} from {year} with {addenda_count} addenda")
            
            # Simulate database insert (would normally use SQLAlchemy)
            # For now, just validate structure
            for i, addendum in enumerate(data['infoAddenda']):
                if 'committees' not in addendum:
                    tracker.record_failure(f"{file_path.stem}-addendum-{i}", "Missing committees")
                    continue
                
                for j, committee in enumerate(addendum['committees']):
                    if 'committeeName' not in committee:
                        tracker.record_failure(f"{file_path.stem}-addendum-{i}-committee-{j}", "Missing committeeName")
                        continue
                    
                    # Count items
                    items = committee.get('items', [])
                    logger.info(f"  Committee {committee.get('committeeName', 'Unknown')} has {len(items)} items")
            
            tracker.record_success(file_path.stem)
            
        except Exception as e:
            tracker.record_failure(file_path.stem, str(e))
    
    summary = tracker.get_summary()
    logger.info(f"Agenda ingestion summary: {summary}")
    return summary['failed'] == 0

def test_database_connection():
    """Test database connection"""
    logger.info("=== Testing Database Connection ===")
    
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=settings.pghost,
            port=settings.pgport,
            user=settings.pguser,
            password=settings.pgpassword,
            database=settings.pgdatabase
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            logger.info(f"✅ Database connection successful: {version[:50]}...")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_ingestion_configuration():
    """Test that ingestion configuration is properly set up for full ingestion"""
    logger.info("=== Testing Ingestion Configuration ===")
    
    # Test settings
    logger.info(f"Database: {settings.pgdatabase}@{settings.pghost}:{settings.pgport}")
    logger.info(f"Max errors: {settings.max_errors}")
    logger.info(f"Request timeout: {settings.request_timeout}")
    logger.info(f"Rate limit delay: {settings.rate_limit_delay}")
    
    # Check that limits are removed
    if settings.max_errors >= 1000:
        logger.info("✅ Max errors configured for full ingestion")
    else:
        logger.warning("⚠️  Max errors may be too low for full ingestion")
    
    if settings.request_timeout >= 60:
        logger.info("✅ Request timeout configured for large datasets")
    else:
        logger.warning("⚠️  Request timeout may be too low for large datasets")
    
    if settings.rate_limit_delay <= 0.5:
        logger.info("✅ Rate limiting optimized for full ingestion")
    else:
        logger.warning("⚠️  Rate limiting may be too restrictive for full ingestion")
    
    # Check staging directories
    staging_dirs = [
        "staging/govinfo/agendas",
        "staging/govinfo/calendars", 
        "staging/govinfo/votes",
        "staging/members"
    ]
    
    for dir_path in staging_dirs:
        path = Path(dir_path)
        if path.exists():
            logger.info(f"✅ Staging directory exists: {dir_path}")
        else:
            logger.warning(f"⚠️  Staging directory missing: {dir_path}")
    
    return True

def main():
    """Run all tests"""
    logger.info("🚀 Starting OpenLegislation Ingestion System Test")
    logger.info("=" * 60)
    
    results = []
    
    # Test configuration
    results.append(("Configuration", test_ingestion_configuration()))
    
    # Test database connection
    results.append(("Database", test_database_connection()))
    
    # Test agenda ingestion
    results.append(("Agenda Ingestion", test_agenda_ingestion()))
    
    # Summary
    logger.info("=" * 60)
    logger.info("🏁 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All tests passed! Ingestion system is ready for full data processing.")
        return True
    else:
        logger.error("💥 Some tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)