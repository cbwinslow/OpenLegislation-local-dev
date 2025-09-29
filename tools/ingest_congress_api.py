#!/usr/bin/env python3
"""
Extended congress.gov/OpenStates API ingestion script.
Now supports --source congress/openstates (US federal/states), --endpoint member/bill.
For OpenStates: /legislators?state=ca → map to federal_member (source='state', country='US').
Configurable: --congress 119 (federal), --state ca (OpenStates), --batch 50, --dry-run.
Trackable: ingestion_log.json per source.
Measurable: Pre/post counts, rate.
Repeatable: Resume from offset (log.json per source).
Uses psycopg2 upsert to federal_member/bills.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
import logging

# Config from .env
API_KEYS = {
    'congress': os.getenv('CONGRESS_API_KEY', 'DEMO_KEY'),
    'openstates': os.getenv('OPENSTATES_API_KEY', '')  # Get from https://openstates.org/register/apikey/
}
DB_URL = os.getenv('DB_URL', 'postgresql://user:pass@localhost:5432/openleg')
LOG_FILE = Path('tools/ingestion_log.json')
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '50'))

ENDPOINTS = {
    'congress': {
        'member': {'url': '/member', 'table': 'master.federal_member', 'pk_col': 'bioguide_id', 'map_func': _map_congress_member},
        'bill': {'url': '/bill', 'table': 'master.bills', 'pk_col': 'print_no', 'map_func': _map_congress_bill}  # Composite PK in SQL
    },
    'openstates': {
        'legislator': {'url': '/legislators/', 'table': 'master.federal_member', 'pk_col': 'openstates_id', 'map_func': _map_openstates_legislator},
        'bill': {'url': '/bills/', 'table': 'master.bills', 'pk_col': 'bill_id', 'map_func': _map_openstates_bill}
    }
}

BASE_URLS = {
    'congress': 'https://api.congress.gov/v3',
    'openstates': 'https://openstates.org/api/v1'
}

def _map_congress_member(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map congress.gov /member JSON to federal_member schema."""
    member = data['member']
    return {
        'bioguide_id': member.get('bioguideId'),
        'full_name': member.get('name'),
        'first_name': member.get('firstName'),
        'last_name': member.get('lastName'),
        'party': member.get('party'),
        'state': member.get('state'),
        'chamber': member.get('chamber', 'member').lower() if member.get('chamber') else None,
        'current_member': member.get('currentMember', False),
        'terms': json.dumps(member.get('terms', [])),
        'committees': json.dumps(member.get('committees', [])),
        'social_media': json.dumps({
            'twitter': member.get('twitterAccount'),
            'facebook': member.get('facebookAccount'),
            'youtube': member.get('youtubeAccount')
        }),
        'source': 'federal'  # From congress.gov
    }

def _map_congress_bill(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map congress.gov /bill JSON to bills schema."""
    bill = data['bill']
    return {
        'print_no': f"{bill.get('type', 'HR')}{bill.get('number', '')}",
        'session_year': 2025,  # Map congress to year (e.g., 119 → 2025)
        'title': bill.get('title'),
        'sponsors': json.dumps([{'name': s.get('name')} for s in bill.get('sponsors', [])]),
        'actions': json.dumps([{'text': a.get('text')} for a in bill.get('actions', [])]),
        'federal_congress': data.get('congress'),  # From endpoint
        'source': 'federal'
    }

def _map_openstates_legislator(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map OpenStates /legislators JSON to federal_member (state focus)."""
    legislator = data
    return {
        'openstates_id': legislator.get('id'),  # PK for states
        'full_name': legislator.get('name'),
        'first_name': legislator.get('given_name'),
        'last_name': legislator.get('family_name'),
        'party': legislator.get('party'),
        'state': legislator.get('state').upper(),
        'chamber': legislator.get('chamber').lower() if legislator.get('chamber') else None,
        'current_member': legislator.get('active', True),
        'terms': json.dumps([{'state': t.get('state')} for t in legislator.get('roles', []) if t.get('type') == 'member']),  # Simplified
        'committees': json.dumps(legislator.get('committees', [])),
        'social_media': json.dumps({
            'twitter': legislator.get('twitter_id'),
            'facebook': legislator.get('facebook_id'),
            'website': legislator.get('url')
        }),
        'source': 'state'  # From OpenStates (US states)
    }

def _map_openstates_bill(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map OpenStates /bills JSON to bills schema (state focus)."""
    bill = data
    return {
        'bill_id': bill.get('id'),  # PK for OpenStates
        'print_no': bill.get('bill_id'),
        'session_year': int(bill.get('session')),
        'title': bill.get('title'),
        'sponsors': json.dumps([{'name': s.get('name')} for s in bill.get('sponsors', [])]),
        'actions': json.dumps([{'text': a.get('description')} for a in bill.get('actions', [])]),
        'source': 'state'
    }

class CongressAPIIngester:
    def __init__(self, source: str, endpoint: str, params: Dict[str, Any], batch_size: int, dry_run: bool = False):
        if source not in ENDPOINTS:
            raise ValueError(f"Source '{source}' not supported (use 'congress' or 'openstates')")
        if endpoint not in ENDPOINTS[source]:
            raise ValueError(f"Endpoint '{endpoint}' not supported for source '{source}'")
        self.source = source
        self.endpoint_config = ENDPOINTS[source][endpoint]
        self.params = params  # e.g., {'congress': 119} or {'state': 'ca'}
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.base_url = BASE_URLS[source]
        self.session = self._get_requests_session()
        self.api_key = API_KEYS[source]
        self.log = self._load_log(source)
        self.metrics = {'start': datetime.now(), 'batches': 0, 'ingested': 0, 'errors': 0, 'rate': 0.0}

    def _get_requests_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _load_log(self, source: str) -> Dict[str, Any]:
        log = {'runs': [], 'checkpoints': {'offset': 0}}
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r') as f:
                try:
                    log = json.load(f)
                    # Per-source log if multiple runs
                    source_logs = log.get('sources', {})
                    return source_logs.get(source, {'offset': 0})
                except json.JSONDecodeError:
                    print("Corrupted log.json; starting fresh.")
        return {'offset': 0}

    def _save_log(self, source: str, offset: int):
        run_end = datetime.now().isoformat()
        duration = (datetime.now() - datetime.fromisoformat(self.metrics['start'])).total_seconds()
        self.metrics['end'] = run_end
        self.metrics['duration_s'] = int(duration)
        self.metrics['success_rate'] = (self.metrics['ingested'] / self.metrics['total'] * 100) if self.metrics['total'] > 0 else 0

        run_entry = {
            'run_id': datetime.now().isoformat(),
            'source': source,
            'endpoint': self.endpoint_config['url'].split('/')[-1],
            **self.params,  # congress/state etc.
            'offset_end': offset,
            'ingested': self.metrics['ingested'],
            'errors': self.metrics['errors'],
            'rate': self.metrics['success_rate'],
            'duration_s': self.metrics['duration_s']
        }

        if LOG_FILE.exists():
            with open(LOG_FILE, 'r') as f:
                log = json.load(f)
        else:
            log = {'runs': [], 'sources': {}}
        log['runs'] = log.get('runs', []) + [run_entry]
        log['sources'][source] = {'offset': offset}
        with open(LOG_FILE, 'w') as f:
            json.dump(log, f, indent=2)
        print(f"Log saved ({source}): ingested={self.metrics['ingested']}, rate={self.metrics['success_rate']:.1f}%, time={duration:.0f}s")

    def _pre_count(self, table: str, extra_filters: Dict[str, Any] = {}) -> int:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                where_parts = [f"congress = %(congress)s"] if self.source == 'congress' else [f"state = %(state)s"]
                for k, v in extra_filters.items():
                    where_parts.append(f"{k} = %({k})s")
                where_clause = ' AND '.join(where_parts) if where_parts else ''
                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {where_clause}", {**self.params, **extra_filters})
                return cur.fetchone()[0]

    def _post_count(self, table: str, extra_filters: Dict[str, Any] = {}) -> int:
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                where_parts = [f"congress = %(congress)s"] if self.source == 'congress' else [f"state = %(state)s"]
                for k, v in extra_filters.items():
                    where_parts.append(f"{k} = %({k})s")
                where_clause = ' AND '.join(where_parts) if where_parts else ''
                cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {where_clause}", {**self.params, **extra_filters})
                return cur.fetchone()[0]

    def _upsert_batch(self, batch_data: List[Dict[str, Any]]) -> bool:
        if self.dry_run:
            print(f"[DRY-RUN] Would upsert {len(batch_data)} rows to {self.endpoint_config['table']}.")
            return True

        table = self.endpoint_config['table']
        # Columns based on schema (extend for bills: composite PK on bills)
        if table == 'master.federal_member':
            columns = ['bioguide_id', 'full_name', 'first_name', 'last_name', 'party', 'state', 'chamber', 'current_member', 'terms', 'committees', 'social_media', 'source']
        elif table == 'master.bills':
            columns = ['print_no', 'session_year', 'title', 'sponsors', 'actions', 'federal_congress', 'source']
        else:
            raise ValueError(f"Table {table} not supported.")

        try:
            with psycopg2.connect(DB_URL) as conn:
                with conn.cursor() as cur:
                    values = [tuple(row.get(col) for col in columns) for row in batch_data if row[self.endpoint_config['pk_col']]]
                    if not values:
                        return True
                    where_clause = f"{self.endpoint_config['pk_col']} = EXCLUDED.{self.endpoint_config['pk_col']}"
                    update_clause = ', '.join([f"{col}=EXCLUDED.{col}" for col in columns if col != self.endpoint_config['pk_col']])
                    execute_values(cur, f"""
                        INSERT INTO {table} ({', '.join(columns)})
                        VALUES %s
                        ON CONFLICT ({self.endpoint_config['pk_col']}) DO UPDATE SET {update_clause}
                    """, values)
                    conn.commit()
            return True
        except Exception as e:
            print(f"DB upsert error: {e}")
            self.metrics['errors'] += len(batch_data)
            return False

    def ingest(self):
        url = f"{self.base_url}{self.endpoint_config['url']}"
        params = {'api_key': self.api_key, **self.params, 'format': 'json', 'limit': self.batch_size, 'offset': self.log['offset']}
        self.metrics['pre_count'] = self._pre_count(self.endpoint_config['table'])
        self.metrics['total'] = 0

        while True:
            print(f"Fetching batch ({self.source}): offset={self.log['offset']}")
            resp = self.session.get(url, params=params)
            if resp.status_code != 200:
                print(f"API error ({resp.status_code}): {resp.text[:200]}...")
                self.metrics['errors'] += self.batch_size
                break

            data = resp.json()
            items_key = self.endpoint_config['url'].lstrip('/').rstrip('s')  # e.g., 'member' or 'legislator'
            items = data.get(items_key, [])
            self.metrics['total'] += len(items)
            if not items:
                print("No more items; complete.")
                break

            batch_data = [self.endpoint_config['map_func'](item) for item in items]

            success = self._upsert_batch(batch_data)
            ingested_delta = len(items) if success else 0
            self.metrics['ingested'] += ingested_delta
            self.metrics['batches'] += 1
            print(f"Batch ({self.source}): {len(items)} fetched ({ingested_delta} mapped), success={success}")

            self.log['offset'] += self.batch_size
            self._save_log(self.source, self.log['offset'])
            if self.dry_run:
                print("Dry-run: Stopping after 1 batch.")
                break

        post_count = self._post_count(self.endpoint_config['table'])
        print(f"Pre-count: {self.metrics['pre_count']}, Post-count: {post_count}, Delta: {post_count - self.metrics['pre_count']}")
        self._save_log(self.source, self.log['offset'])  # Final save
        print(f"Completed ({self.source}): {self.metrics}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest from congress.gov or OpenStates API.')
    parser.add_argument('--source', default='congress', choices=list(BASE_URLS.keys()), help='Source API (congress/openstates)')
    parser.add_argument('--endpoint', default='member', choices=['member', 'bill'], help='Endpoint (member/bill)')
    subparsers = parser.add_subparsers(dest='subcommand', help='Subcommands')
    
    congress_parser = subparsers.add_parser('congress', help='Congress options')
    congress_parser.add_argument('--congress', type=int, required=True, help='Congress number (e.g., 119)')
    
    openstates_parser = subparsers.add_parser('openstates', help='OpenStates options')
    openstates_parser.add_argument('--state', required=True, help='State abbr (e.g., ca for California)')
    
    common_parser = parser.add_argument_group('common')
    common_parser.add_argument('--batch', type=int, default=BATCH_SIZE, help='Batch size')
    common_parser.add_argument('--dry-run', action='store_true', help='Simulate ingestion')

    args = parser.parse_args()
    if args.source == 'openstates':
        params = {'state': args.state}
    else:
        params = {'congress': args.congress}

    ingester = CongressAPIIngester(args.source, args.endpoint, params, args.batch, args.dry_run)
    ingester.ingest()
