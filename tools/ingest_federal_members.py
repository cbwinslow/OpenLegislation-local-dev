#!/usr/bin/env python3
"""
Federal Member Data Ingestion from Congress.gov API

Fetches comprehensive member data from congress.gov and populates federal member tables.
Includes biographical info, terms served, committees, social media, and contact details.

Now uses the generic ingestion framework with resume capability.

Usage:
    python3 tools/ingest_federal_members.py --api-key YOUR_API_KEY --db-config tools/db_config.json

Requirements:
    - Congress.gov API key (get from https://api.congress.gov/)
    - Database with federal member schema applied
"""

import json
import sys
from typing import Dict, List, Optional, Any

import psycopg2
import psycopg2.extras
import requests

from settings import settings
from base_ingestion_process import BaseIngestionProcess, run_ingestion_process


class CongressMemberIngestor(BaseIngestionProcess):
    """Ingests federal member data from Congress.gov API using generic framework"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)

        # Database connection for data insertion
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # API configuration
        self.api_key = api_key or settings.congress_api_key
        if not self.api_key:
            raise ValueError("Congress API key must be provided via argument or CONGRESS_API_KEY in .env")

        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()

        # Error counting
        self.error_count = 0
        self.max_errors = settings.max_errors

        # Rate limiting
        self.request_count = 0
        self.last_request_time = 0

    def get_data_source(self) -> str:
        """Return data source identifier"""
        return "congress_api"

    def get_target_table(self) -> str:
        """Return target table name"""
        return "master.federal_person"  # Primary table for tracking

    def get_record_id_column(self) -> str:
        """Return record ID column"""
        return "bioguide_id"

    def discover_records(self) -> List[Dict[str, Any]]:
        """Discover all current members from Congress.gov API"""
        print("Fetching current members from Congress.gov API...")

        members = []
        offset = 0
        limit = 250  # Max per request

        while True:
            params = {
                'currentMember': 'true',
                'limit': limit,
                'offset': offset
            }

            data = self._api_request('/member', params)
            if not data or 'members' not in data:
                break

            batch = data['members']
            if not batch:
                break

            # Convert to record format for tracking
            for member in batch:
                bioguide_id = member.get('bioguideId')
                if bioguide_id:
                    members.append({
                        'record_id': bioguide_id,
                        'name': member.get('name', ''),
                        'chamber': member.get('chamber', '').lower(),
                        'state': member.get('state'),
                        'party': member.get('partyName', member.get('party')),
                        'metadata': member  # Store full member data
                    })

            offset += len(batch)
            print(f"Fetched {len(members)} members so far...")

            # Small delay between batches
            import time
            time.sleep(settings.rate_limit_delay)

        print(f"Total current members discovered: {len(members)}")
        return members

    def process_record(self, record: Dict[str, Any]) -> bool:
        """Process a single member record"""
        bioguide_id = record['record_id']
        member_summary = record['metadata']

        print(f"Processing member: {bioguide_id}")

        # Get detailed member info (if not already in metadata)
        if 'terms' not in member_summary:
            member_details = self.get_member_details(bioguide_id)
            if not member_details:
                self._handle_error(f"Could not fetch details for {bioguide_id}")
                return False
        else:
            member_details = member_summary

        # Insert person
        person_id = self.insert_person(member_details)
        if not person_id:
            self._handle_error(f"Failed to insert person for {bioguide_id}")
            return False

        # Insert member
        member_id = self.insert_member(person_id, member_details)
        if not member_id:
            self._handle_error(f"Failed to insert member for {bioguide_id}")
            return False

        # Insert terms
        terms = member_details.get('terms', [])
        if terms:
            self.insert_member_terms(member_id, terms)

        # Insert social media
        self.insert_social_media(member_id, member_details)

        # Insert contact info (if available)
        self.insert_contact_info(member_id, member_details)

        return True

    # Keep existing methods for API calls and data insertion
    def _handle_error(self, message: str, fatal: bool = False):
        """Increment error count and abort if threshold is reached."""
        self.error_count += 1
        print(f"✗ {message} (error {self.error_count}/{self.max_errors})")
        if fatal or self.error_count >= self.max_errors:
            print(f"Too many errors ({self.error_count}), aborting ingestion.")
            try:
                if hasattr(self, 'conn'):
                    self.conn.rollback()
            except Exception:
                pass
            sys.exit(1)

    def _rate_limit(self):
        """Implement rate limiting"""
        import time
        self.request_count += 1

        # Reset counter hourly
        current_time = time.time()
        if current_time - self.last_request_time > 3600:  # 1 hour
            self.request_count = 1
            self.last_request_time = current_time

        # If approaching limit, slow down
        if self.request_count > 800:  # 80% of hourly limit
            sleep_time = 2  # Extra delay
            print(f"Rate limiting: sleeping {sleep_time}s")
            time.sleep(sleep_time)

    def _api_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with error handling and rate limiting"""
        self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        request_params = {'api_key': self.api_key, 'format': 'json'}
        if params:
            request_params.update(params)

        try:
            response = self.session.get(url, params=request_params, timeout=settings.request_timeout)
            response.raise_for_status()

            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            self._handle_error(f"API request failed for {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            self._handle_error(f"JSON decode failed for {endpoint}: {e}")
            return None

    def get_member_details(self, bioguide_id: str) -> Optional[Dict]:
        """Fetch detailed information for a specific member"""
        data = self._api_request(f'/member/{bioguide_id}')
        return data.get('member') if data else None

    def insert_person(self, member_data: Dict) -> Optional[int]:
        """Insert or update federal person record"""
        try:
            # Extract biographical info
            bioguide_id = member_data.get('bioguideId')
            if not bioguide_id:
                return None

            # Parse name components
            name_info = member_data.get('name', '')
            first_name = member_data.get('firstName', '')
            middle_name = member_data.get('middleName', '')
            last_name = member_data.get('lastName', '')
            suffix = member_data.get('suffix', '')
            nickname = member_data.get('nickname', '')

            # Full name construction
            full_name_parts = []
            if first_name:
                full_name_parts.append(first_name)
            if middle_name:
                full_name_parts.append(middle_name)
            if nickname:
                full_name_parts.append(f'"{nickname}"')
            if last_name:
                full_name_parts.append(last_name)
            if suffix:
                full_name_parts.append(suffix)

            full_name = ' '.join(full_name_parts) if full_name_parts else name_info

            # Birth/death years
            birth_year = None
            death_year = None
            if 'birthYear' in member_data:
                try:
                    birth_year = int(member_data['birthYear'])
                except (ValueError, TypeError):
                    pass

            if 'deathYear' in member_data:
                try:
                    death_year = int(member_data['deathYear'])
                except (ValueError, TypeError):
                    pass

            # Gender
            gender = None
            honorific = member_data.get('honorific', '').lower()
            if 'mrs' in honorific or 'ms' in honorific:
                gender = 'F'
            elif 'mr' in honorific or 'senator' in honorific or 'representative' in honorific:
                gender = 'M'

            # Insert/update person
            self.cursor.execute("""
                INSERT INTO master.federal_person (
                    bioguide_id, full_name, first_name, middle_name,
                    last_name, suffix, nickname, birth_year, death_year, gender
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (bioguide_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    first_name = EXCLUDED.first_name,
                    middle_name = EXCLUDED.middle_name,
                    last_name = EXCLUDED.last_name,
                    suffix = EXCLUDED.suffix,
                    nickname = EXCLUDED.nickname,
                    birth_year = EXCLUDED.birth_year,
                    death_year = EXCLUDED.death_year,
                    gender = EXCLUDED.gender,
                    updated_at = now()
                RETURNING id
            """, (
                bioguide_id, full_name, first_name, middle_name,
                last_name, suffix, nickname, birth_year, death_year, gender
            ))

            result = self.cursor.fetchone()
            return result['id'] if result else None

        except Exception as e:
            print(f"Error inserting person {bioguide_id}: {e}")
            return None

    def insert_member(self, person_id: int, member_data: Dict) -> Optional[int]:
        """Insert or update federal member record"""
        try:
            bioguide_id = member_data.get('bioguideId')
            # Chamber may not be present at the top level of the detailed member
            # object returned by the member details endpoint. Prefer an explicit
            # top-level `chamber`, otherwise derive from the most recent term.
            chamber = member_data.get('chamber', '')
            if not chamber:
                terms = member_data.get('terms', []) or []
                # choose the most recent term by startYear or by last entry
                chosen = None
                try:
                    # pick term with greatest startYear when available
                    chosen = max((t for t in terms if t), key=lambda t: int(t.get('startYear') or 0))
                except Exception:
                    if terms:
                        chosen = terms[-1]

                if chosen:
                    chamber = chosen.get('chamber', '')

            chamber = (chamber or '').lower().strip()
            # Normalize common variations returned by the API
            if 'house' in chamber:
                chamber = 'house'
            elif 'senate' in chamber:
                chamber = 'senate'
            state = member_data.get('state')
            district = member_data.get('district')
            party = member_data.get('partyName', member_data.get('party'))
            current_member = member_data.get('currentMember', True)

            if not chamber or chamber not in ['house', 'senate']:
                print(f"Skipping member {bioguide_id}: invalid chamber '{chamber}'")
                return None

            # Normalize party codes
            if party:
                party = party.upper()
                if party in ['DEMOCRAT', 'DEMOCRATIC']:
                    party = 'D'
                elif party in ['REPUBLICAN']:
                    party = 'R'
                elif party in ['INDEPENDENT']:
                    party = 'I'

            # Insert/update member
            self.cursor.execute("""
                INSERT INTO master.federal_member (
                    person_id, chamber, state, district, party, current_member
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (person_id, chamber, state, district) DO UPDATE SET
                    party = EXCLUDED.party,
                    current_member = EXCLUDED.current_member,
                    updated_at = now()
                RETURNING id
            """, (person_id, chamber, state, district, party, current_member))

            result = self.cursor.fetchone()
            return result['id'] if result else None

        except Exception as e:
            print(f"Error inserting member {bioguide_id}: {e}")
            return None

    def insert_member_terms(self, member_id: int, terms_data: List[Dict]):
        """Insert member terms served"""
        for term in terms_data:
            try:
                congress = term.get('congress')
                start_year = term.get('startYear')
                end_year = term.get('endYear')
                party = term.get('party')
                # Term objects sometimes use different keys for state
                state = term.get('state') or term.get('stateCode') or term.get('stateName')
                district = term.get('district')
                chamber = (term.get('chamber') or '').lower()
                if 'house' in chamber:
                    chamber = 'house'
                elif 'senate' in chamber:
                    chamber = 'senate'

                if not congress:
                    continue

                # Normalize party
                if party:
                    party = party.upper()
                    if party in ['DEMOCRAT', 'DEMOCRATIC']:
                        party = 'D'
                    elif party in ['REPUBLICAN']:
                        party = 'R'
                    elif party in ['INDEPENDENT']:
                        party = 'I'

                self.cursor.execute("""
                    INSERT INTO master.federal_member_term (
                        member_id, congress, start_year, end_year,
                        party, state, district, chamber
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (member_id, congress) DO UPDATE SET
                        start_year = EXCLUDED.start_year,
                        end_year = EXCLUDED.end_year,
                        party = EXCLUDED.party,
                        state = EXCLUDED.state,
                        district = EXCLUDED.district,
                        chamber = EXCLUDED.chamber
                """, (
                    member_id, congress, start_year, end_year,
                    party, state, district, chamber
                ))

            except Exception as e:
                print(f"Error inserting term for member {member_id}: {e}")
                try:
                    if hasattr(self, 'conn'):
                        self.conn.rollback()
                except Exception:
                    pass

    def insert_social_media(self, member_id: int, member_data: Dict):
        """Insert social media accounts"""
        social_platforms = {
            'twitterAccount': 'twitter',
            'facebookAccount': 'facebook',
            'youtubeAccount': 'youtube',
            'instagramAccount': 'instagram'
        }

        for api_field, platform in social_platforms.items():
            account = member_data.get(api_field)
            if account:
                try:
                    # Construct URL
                    if platform == 'twitter':
                        url = f"https://twitter.com/{account}"
                        handle = account
                    elif platform == 'facebook':
                        url = account if account.startswith('http') else f"https://facebook.com/{account}"
                        handle = account.split('/')[-1] if '/' in account else account
                    elif platform == 'youtube':
                        url = f"https://youtube.com/{account}"
                        handle = account
                    elif platform == 'instagram':
                        url = f"https://instagram.com/{account}"
                        handle = account
                    else:
                        url = account
                        handle = account

                    self.cursor.execute("""
                        INSERT INTO master.federal_member_social_media (
                            member_id, platform, handle, url, is_official
                        ) VALUES (%s, %s, %s, %s, true)
                        ON CONFLICT (member_id, platform) DO UPDATE SET
                            handle = EXCLUDED.handle,
                            url = EXCLUDED.url,
                            updated_at = now()
                    """, (member_id, platform, handle, url))

                except Exception as e:
                    print(f"Error inserting {platform} for member {member_id}: {e}")

    def insert_contact_info(self, member_id: int, member_data: Dict, congress: int = 118):
        """Insert contact information"""
        # This would typically come from additional API calls or member detail endpoints
        # For now, we'll store basic info if available
        pass

    def close(self):
        """Clean up database connection and tracker"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        super().close()


if __name__ == '__main__':
    run_ingestion_process(CongressMemberIngestor, "Federal Member")
