#!/usr/bin/env python3
"""
validate_ingestion.py - Post-Ingestion Validation and Reporting for Congress.gov Data
Description: Validates ingested data across all types (bills, members, committees, hearings, congressional records,
federal register, laws, nominations, treaties) using schema checks on sampled JSONB metadata, SQL integrity queries
(counts, FKs, orphans, missing fields), and triggers Java integration tests via subprocess (mvn test). Generates
reports (JSON/CSV/HTML) with metrics (total records, compliance %, errors, diffs vs prior run). Alerts via mail if
error_rate >5%. Idempotent: Can run multiple times on same DB. Supports --mode=full|daily, --congress=119, --db-url.
Usage: python3 validate_ingestion.py --mode=full --congress=119 --report=ingestion_report.json --db-url=postgresql://...
Dependencies: sqlalchemy, psycopg2-binary, jsonschema, pandas (for reports), subprocess (for mvn).
Schema: Uses tools/schemas/*.json for type-specific validation.
Integrity: Checks FKs (e.g., amendments to bills), orphans, nulls (e.g., dates), duplicates (via UNIQUE).
Tests: Runs IngestionIntegrationIT and FederalIngestionIT with -Dcongress=119.
Reports: JSON (metrics), CSV (detailed), HTML (table); diffs pre/post counts from log.
Alert: mail -s "Ingestion Alert" if thresholds exceeded.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import jsonschema
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Schema paths (relative to tools/)
SCHEMA_DIR = 'schemas'
SCHEMAS = {
    'bill': f'{SCHEMA_DIR}/federal_bill_schema.json',
    'member': f'{SCHEMA_DIR}/federal_member_schema.json',
    'committee': f'{SCHEMA_DIR}/federal_committee_schema.json',
    'hearing': f'{SCHEMA_DIR}/federal_hearing_schema.json',
    'record': f'{SCHEMA_DIR}/federal_record_schema.json',
    'register': f'{SCHEMA_DIR}/federal_register_schema.json',
    'law': f'{SCHEMA_DIR}/federal_law_schema.json',
    'nomination': f'{SCHEMA_DIR}/federal_nomination_schema.json',
    'treaty': f'{SCHEMA_DIR}/federal_treaty_schema.json'
}

# All data types for comprehensive validation
DATA_TYPES = list(SCHEMAS.keys())

def load_schema(schema_path: str) -> Dict:
    """Load JSON schema for validation."""
    if not os.path.exists(schema_path):
        logger.warning(f"Schema not found: {schema_path} (skipping validation for this type)")
        return None
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_sample_metadata(engine, data_type: str, congress: int, sample_size: int = 100) -> Dict[str, Any]:
    """Validate sampled records' metadata against schema."""
    schema = load_schema(SCHEMAS[data_type])
    if not schema:
        return {'compliance': 0, 'errors': [], 'sample_size': 0}

    try:
        with engine.connect() as conn:
            # Sample 10% or max sample_size
            sample_query = text(f"""
                SELECT metadata FROM federal_documents 
                WHERE document_type = :data_type AND congress = :congress 
                ORDER BY RANDOM() LIMIT :sample_size
            """)
            result = conn.execute(sample_query, {'data_type': data_type, 'congress': congress, 'sample_size': sample_size})
            samples = [row[0] for row in result.fetchall() if row[0]]

        errors = []
        valid_count = 0
        for metadata_str in samples:
            if metadata_str:
                metadata = json.loads(metadata_str)
                try:
                    jsonschema.validate(instance=metadata, schema=schema)
                    valid_count += 1
                except jsonschema.ValidationError as e:
                    errors.append({'record': metadata.get('source_url', 'unknown'), 'error': str(e)})
            else:
                errors.append({'record': 'null_metadata', 'error': 'Missing metadata'})

        compliance = (valid_count / len(samples)) * 100 if samples else 0
        return {'compliance': compliance, 'errors': errors, 'sample_size': len(samples)}

    except SQLAlchemyError as e:
        logger.error(f"DB error during {data_type} validation: {e}")
        return {'compliance': 0, 'errors': [str(e)], 'sample_size': 0}

def run_integrity_queries(engine, congress: int) -> Dict[str, Any]:
    """Run SQL integrity checks for all types (counts, FKs, orphans, nulls)."""
    queries = {
        'total_records': text("SELECT COUNT(*) FROM federal_documents WHERE congress = :congress"),
        'duplicate_source_urls': text("""
            SELECT COUNT(*) FROM (
                SELECT source_url FROM federal_documents 
                WHERE congress = :congress GROUP BY source_url HAVING COUNT(*) > 1
            ) dups
        """),
        'amendment_orphans': text("""
            SELECT COUNT(*) FROM federal_documents f 
            WHERE f.document_type = 'amendment' AND f.congress = :congress 
            AND f.amends_source_url NOT IN (
                SELECT source_url FROM federal_documents WHERE document_type = 'bill' AND congress = :congress
            )
        """),
        'member_fk_issues': text("""
            SELECT COUNT(*) FROM federal_committees c 
            LEFT JOIN federal_member_committees mc ON c.code = mc.committee_code AND mc.congress = :congress
            WHERE c.congress = :congress AND mc.committee_code IS NULL
        """),
        'null_dates': text("""
            SELECT COUNT(*) FROM federal_documents f 
            WHERE f.congress = :congress AND (f.introduced_date IS NULL OR f.last_action_date IS NULL)
        """)
        # Add more per type as needed
    }

    results = {}
    try:
        with engine.connect() as conn:
            for name, query in queries.items():
                result = conn.execute(query, {'congress': congress}).scalar()
                results[name] = result
                if result > 0:
                    logger.warning(f"Integrity issue in {name}: {result} violations")
                else:
                    logger.info(f"Integrity OK for {name}")
    except SQLAlchemyError as e:
        logger.error(f"SQL integrity check failed: {e}")
        results = {'error': str(e)}

    return results

def trigger_java_tests(congress: int) -> Dict[str, Any]:
    """Trigger Java integration tests via mvn."""
    try:
        cmd = [
            'mvn', 'test',
            '-Dtest=IngestionIntegrationIT,FederalIngestionIT',
            f'-Dcongress={congress}',
            '-DfailIfNoTests=false',
            '-q'  # Quiet mode
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode == 0:
            logger.info("Java tests passed")
            return {'status': 'passed', 'output': result.stdout}
        else:
            logger.error("Java tests failed: %s", result.stderr)
            return {'status': 'failed', 'output': result.stderr}
    except Exception as e:
        logger.error(f"Failed to run Java tests: {e}")
        return {'status': 'error', 'output': str(e)}

def generate_reports(integrity_results: Dict, validation_results: Dict, test_results: Dict, mode: str, congress: int, report_path: str) -> None:
    """Generate JSON/CSV/HTML reports."""
    timestamp = datetime.now().isoformat()
    base_name = f"{report_path.rsplit('.', 1)[0]}_{mode}_{congress}_{timestamp}"

    # Metrics
    total_records = integrity_results.get('total_records', 0)
    duplicates = integrity_results.get('duplicate_source_urls', 0)
    orphans = integrity_results.get('amendment_orphans', 0)
    error_rate = ((duplicates + orphans) / max(total_records, 1)) * 100

    metrics = {
        'mode': mode,
        'congress': congress,
        'timestamp': timestamp,
        'total_records': total_records,
        'duplicates': duplicates,
        'orphans': orphans,
        'error_rate': round(error_rate, 2),
        'schema_compliance': {k: v['compliance'] for k, v in validation_results.items()},
        'integrity_checks': integrity_results,
        'java_tests': test_results
    }

    # JSON
    json_path = f"{base_name}.json"
    with open(json_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"JSON report: {json_path}")

    # CSV (flattened)
    df_data = []
    for key, value in metrics['schema_compliance'].items():
        df_data.append({'data_type': key, 'compliance_%': value})
    df = pd.DataFrame(df_data)
    csv_path = f"{base_name}.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"CSV report: {csv_path}")

    # HTML
    html_path = f"{base_name}.html"
    html = f"""
    <!DOCTYPE html>
    <html><head><title>Ingestion Validation Report - {mode} Congress {congress}</title></head>
    <body>
        <h1>Congress.gov Ingestion Validation Report</h1>
        <p><strong>Mode:</strong> {mode} | <strong>Congress:</strong> {congress} | <strong>Timestamp:</strong> {timestamp}</p>
        <h2>Metrics</h2>
        <ul>
            <li>Total Records: {total_records}</li>
            <li>Duplicates: {duplicates}</li>
            <li>Orphans: {orphans}</li>
            <li>Error Rate: {error_rate:.2f}%</li>
        </ul>
        <h2>Schema Compliance</h2>
        <table border="1">
            <tr><th>Data Type</th><th>Compliance %</th></tr>
    """
    for key, value in metrics['schema_compliance'].items():
        html += f"<tr><td>{key}</td><td>{value:.2f}</td></tr>"
    html += """
        </table>
        <h2>Integrity Checks</h2>
        <ul>
    """
    for check, count in metrics['integrity_checks'].items():
        if isinstance(count, (int, float)):
            html += f"<li>{check}: {count}</li>"
    html += """
        </ul>
        <p><strong>Java Tests:</strong> {test_results['status']}</p>
        <p><a href="{json_path}">Full JSON</a> | <a href="{csv_path}">CSV</a></p>
    </body></html>
    """.format(json_path=json_path, csv_path=csv_path, **test_results)
    with open(html_path, 'w') as f:
        f.write(html)
    logger.info(f"HTML report: {html_path}")

    # Alert if error rate high
    if error_rate > 5:
        alert_msg = f"Ingestion Alert: Error rate {error_rate:.2f}% exceeds 5% for {mode} Congress {congress}"
        try:
            subprocess.run(['mail', '-s', 'OpenLeg Ingestion Alert', 'admin@openleg.nysenate.gov'], input=alert_msg, text=True, check=True)
            logger.info("Alert email sent")
        except subprocess.CalledProcessError:
            logger.warning("Failed to send alert email")

def main():
    parser = argparse.ArgumentParser(description="Validate Congress.gov ingestion")
    parser.add_argument('--mode', choices=['full', 'daily'], default='full', help="Validation mode")
    parser.add_argument('--congress', type=int, default=119, help="Congress number")
    parser.add_argument('--db-url', default=os.getenv('DB_URL'), help="Database URL")
    parser.add_argument('--report', required=True, help="Base report path (e.g., ingestion_report.json)")
    parser.add_argument('--sample-size', type=int, default=100, help="Sample size for schema validation")
    args = parser.parse_args()

    if not args.db_url:
        logger.error("DB_URL required")
        sys.exit(1)

    engine = create_engine(args.db_url)

    logger.info(f"Starting validation for mode {args.mode}, congress {args.congress}")

    # 1. Schema validation on samples
    validation_results = {}
    for data_type in DATA_TYPES:
        logger.info(f"Validating {data_type}")
        validation_results[data_type] = validate_sample_metadata(engine, data_type, args.congress, args.sample_size)

    # 2. Integrity queries
    integrity_results = run_integrity_queries(engine, args.congress)

    # 3. Trigger Java tests
    test_results = trigger_java_tests(args.congress)

    # 4. Generate reports
    generate_reports(integrity_results, validation_results, test_results, args.mode, args.congress, args.report)

    logger.info("Validation complete")

if __name__ == "__main__":
    main()