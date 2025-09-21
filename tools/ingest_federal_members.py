#!/usr/bin/env python3
"""
Federal Member Data Ingestion from Congress.gov API

Fetches comprehensive member data from congress.gov and populates federal member tables.
Includes biographical info, terms served, committees, social media, and contact details.

Usage:
    python3 tools/ingest_federal_members.py --api-key YOUR_API_KEY --db-config tools/db_config.json

Requirements:
    - Congress.gov API key (get from https://api.congress.gov/)
    - Database with federal member schema applied
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import psycopg2
import psycopg2.extras
import requests


class CongressMemberIngestor:
    """Ingests federal member data from Congress.gov API"""

    def __init__(self, api_key: str, db_config: Dict[str, Any]):
        self.api_key = api_key
        self.db_config = db_config
        self.base_url = "https://api.congress.gov/v3"
        self.session = requests.Session()

        # Connect to database
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Rate limiting: 1000 requests/hour, 5000/day
        self.request_count = 0
        self.last_request_time = time.time()

    def _rate_limit(self):
        """Implement rate limiting"""
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
            response = self.session.get(url, params=request_params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            print(f"API request failed for {endpoint}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode failed for {endpoint}: {e}")
            return None

    def get_current_members(self) -> List[Dict]:
        """Fetch all current members of Congress"""
        print("Fetching current members...")

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

            members.extend(batch)
            offset += len(batch)

            print(f"Fetched {len(members)} members so far...")

            # Small delay between batches
            time.sleep(0.5)

        print(f"Total current members: {len(members)}")
        return members

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
            chamber = member_data.get('chamber', '').lower()
            state = member_data.get('state')
            district = member_data.get('district')
            party = member_data.get('partyName', member_data.get('party'))
            current_member = member_data.get('currentMember', True)

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
                state = term.get('state')
                district = term.get('district')
                chamber = term.get('chamber', '').lower()

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
        pass  # Implementation depends on available contact data structure

    def process_member(self, member_summary: Dict):
        """Process a single member: fetch details and insert all data"""
        bioguide_id = member_summary.get('bioguideId')
        if not bioguide_id:
            return False

        print(f"Processing member: {bioguide_id}")

        # Get detailed member info
        member_details = self.get_member_details(bioguide_id)
        if not member_details:
            print(f"Could not fetch details for {bioguide_id}")
            return False

        # Insert person
        person_id = self.insert_person(member_details)
        if not person_id:
            print(f"Failed to insert person for {bioguide_id}")
            return False

        # Insert member
        member_id = self.insert_member(person_id, member_details)
        if not member_id:
            print(f"Failed to insert member for {bioguide_id}")
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

    def ingest_all_members(self):
        """Main ingestion process"""
        print("Starting federal member data ingestion...")

        # Get all current members
        current_members = self.get_current_members()

        if not current_members:
            print("No members found!")
            return

        successful = 0
        failed = 0
        progress_log = {'batches': [], 'quality': {}}

        # Process each member
        for i, member_summary in enumerate(current_members):
            try:
                if self.process_member(member_summary):
                    successful += 1
                else:
                    failed += 1

                # Log progress every 10
                if (i + 1) % 10 == 0:
                    self.conn.commit()
                    batch_progress = {'batch_num': (i // 10) + 1, 'successful': successful, 'failed': failed}
                    progress_log['batches'].append(batch_progress)
                    print(f"Progress: {successful} successful, {failed} failed")

                    # Save log
                    with open('ingestion_log.json', 'w') as log_file:
                        json.dump(progress_log, log_file, indent=2, default=str)

                # Small delay
                time.sleep(0.5)

            except Exception as e:
                print(f"Unexpected error processing member: {e}")
                failed += 1
                self.conn.rollback()

        # Quality metrics
        try:
            self.cursor.execute("SELECT COUNT(*) as total FROM master.federal_member")
            total = self.cursor.fetchone()['total']

            self.cursor.execute("SELECT COUNT(*) as complete FROM master.federal_member WHERE full_name IS NOT NULL AND party IS NOT NULL AND state IS NOT NULL")
            complete = self.cursor.fetchone()['complete']
            progress_log['quality']['complete_pct'] = (complete / total * 100) if total > 0 else 0

            self.cursor.execute("SELECT COUNT(*) as duplicates FROM master.federal_person WHERE updated_at > now() - interval '1 hour'")
            dups = self.cursor.fetchone()['duplicates']
            progress_log['quality']['potential_duplicates'] = dups

        except Exception as e:
            progress_log['quality']['error'] = str(e)

        with open('ingestion_log.json', 'w') as log_file:
            json.dump(progress_log, log_file, indent=2, default=str)

        # Example retry decorator for API calls (uncomment and apply to methods as needed)
        # def retry(max_attempts=3, delay=1):
        #     def decorator(func):
        #         def wrapper(*args, **kwargs):
        #             for attempt in range(max_attempts):
        #                 try:
        #                     return func(*args, **kwargs)
        #                 except Exception as e:
        #                     if attempt == max_attempts - 1:
        #                         raise e
        #                     print(f"Retry {attempt + 1}/{max_attempts} after {delay}s: {e}")
        #                     time.sleep(delay * (2 ** attempt))
        #         return wrapper
        #     return decorator
        # self._api_request = retry()(self._api_request)

        print("Progress and quality logged to ingestion_log.json")

        # Final commit
        self.conn.commit()

        print("Ingestion complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total processed: {successful + failed}")

        # Summary statistics
        self.print_summary_stats()

    def print_summary_stats(self):
        """Print summary statistics of ingested data"""
        try:
            # Count by chamber
            self.cursor.execute("""
                SELECT chamber, COUNT(*) as count
                FROM master.federal_member
                WHERE current_member = true
                GROUP BY chamber
                ORDER BY chamber
            """)
            chamber_counts = self.cursor.fetchall()

            print("\n=== INGESTION SUMMARY ===")
            for row in chamber_counts:
                print(f"{row['chamber'].title()}: {row['count']}")

            # Count with social media
            self.cursor.execute("""
                SELECT COUNT(DISTINCT member_id) as with_social
                FROM master.federal_member_social_media
            """)
            social_count = self.cursor.fetchone()['with_social']
            print(f"Members with social media: {social_count}")

            # Total terms
            self.cursor.execute("""
                SELECT COUNT(*) as term_count
                FROM master.federal_member_term
            """)
            term_count = self.cursor.fetchone()['term_count']
            print(f"Total terms recorded: {term_count}")

            # Data quality (join person for full_name)
            self.cursor.execute("""
                SELECT COUNT(*) as total_members 
                FROM master.federal_member m 
                JOIN master.federal_person p ON m.person_id = p.id
            """)
            total_members = self.cursor.fetchone()['total_members']
            self.cursor.execute("""
                SELECT COUNT(*) as incomplete 
                FROM master.federal_member m 
                JOIN master.federal_person p ON m.person_id = p.id 
                WHERE p.full_name IS NULL OR m.party IS NULL
            """)
            incomplete = self.cursor.fetchone()['incomplete']
            quality_pct = ((total_members - incomplete) / total_members * 100) if total_members > 0 else 0
            print(f"Data quality (complete profiles): {quality_pct:.1f}%")

        except Exception as e:
            print(f"Error generating summary: {e}")

    def close(self):
        """Clean up database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Ingest federal member data from Congress.gov API')
    parser.add_argument('--api-key', required=True, help='Congress.gov API key')
    parser.add_argument('--db-config', required=True, help='Database config JSON file')
    parser.add_argument('--limit', type=int, help='Limit number of members to process (for testing)')

    args = parser.parse_args()

    # Load database config
    try:
        with open(args.db_config, 'r') as f:
            db_config = json.load(f)
    except Exception as e:
        print(f"Error loading database config: {e}")
        sys.exit(1)

    # Create ingestor and run
    ingestor = CongressMemberIngestor(args.api_key, db_config)

    try:
        ingestor.ingest_all_members()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Ingestion failed: {e}")
    finally:
        ingestor.close()


if __name__ == '__main__':
    main()
