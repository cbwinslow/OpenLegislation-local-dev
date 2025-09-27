# Member Data Ingestion Procedures

## Overview

This document outlines procedures for ingesting legislator/member data from multiple government sources into the unified OpenLegislation database schema. The goal is to create comprehensive member profiles that include biographical information, contact details, committee assignments, and social media presence.

## Data Sources & Priorities

### Primary Sources (High Priority)

#### 1. Congress.gov Member API
- **Endpoint**: `https://api.congress.gov/v3/member`
- **Authentication**: API key required
- **Rate Limits**: 1000 requests/hour, 5000/day
- **Data Coverage**: All current and historical members

#### 2. OpenStates API
- **Endpoint**: `https://openstates.org/api/v1/legislators/`
- **Authentication**: API key (free tier available)
- **Rate Limits**: 1000/day free
- **Data Coverage**: 50 states + DC

### Secondary Sources (Medium Priority)

#### 3. Biographical Directory of Congress
- **URL**: `https://bioguide.congress.gov/`
- **Data**: Detailed biographies, photos, extended history
- **Format**: HTML scraping with structured data

#### 4. State Legislature Websites
- **Data**: State-specific member information
- **Format**: HTML scraping, some APIs
- **Coverage**: Individual state data

## Database Schema Extensions

### Member Social Media Table
```sql
CREATE TABLE IF NOT EXISTS member_social_media (
    id BIGSERIAL PRIMARY KEY,
    member_id TEXT NOT NULL, -- References person.id or external ID
    platform TEXT NOT NULL CHECK (platform IN ('twitter', 'facebook', 'youtube', 'instagram', 'website')),
    handle TEXT,
    url TEXT,
    follower_count INTEGER,
    is_verified BOOLEAN DEFAULT false,
    is_official BOOLEAN DEFAULT true,
    last_updated TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(member_id, platform)
);

-- Index for performance
CREATE INDEX idx_member_social_platform ON member_social_media(member_id, platform);
CREATE INDEX idx_member_social_updated ON member_social_media(last_updated);
```

### Extended Member Biography Table
```sql
CREATE TABLE IF NOT EXISTS member_biography (
    id BIGSERIAL PRIMARY KEY,
    member_id TEXT NOT NULL,
    biography_text TEXT,
    birth_date DATE,
    death_date DATE,
    education TEXT[],
    profession TEXT[],
    military_service TEXT,
    awards TEXT[],
    family_info TEXT,
    source_url TEXT,
    last_updated TIMESTAMP DEFAULT now(),
    UNIQUE(member_id)
);
```

## Ingestion Procedures

### Procedure 1: Congress.gov Member API Ingestion

#### Step 1: Initial Setup
```bash
# Set API key
export CONGRESS_API_KEY="your_api_key_here"

# Create working directory
mkdir -p data/member_ingestion
cd data/member_ingestion
```

#### Step 2: Fetch Current Members
```python
#!/usr/bin/env python3
"""
Fetch current Congress members from Congress.gov API
"""
import requests
import json
import time
from pathlib import Path

API_KEY = "your_api_key_here"
BASE_URL = "https://api.congress.gov/v3"
OUTPUT_DIR = Path("data/member_ingestion")

def fetch_current_members():
    """Fetch all current members of Congress"""
    url = f"{BASE_URL}/member"
    params = {
        'api_key': API_KEY,
        'format': 'json',
        'currentMember': 'true',
        'limit': 250  # Max per page
    }

    all_members = []
    offset = 0

    while True:
        params['offset'] = offset
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        members = data.get('members', [])

        if not members:
            break

        all_members.extend(members)
        offset += len(members)

        # Rate limiting
        time.sleep(1)

        print(f"Fetched {len(all_members)} members so far...")

    # Save to file
    with open(OUTPUT_DIR / 'current_members.json', 'w') as f:
        json.dump(all_members, f, indent=2)

    print(f"Saved {len(all_members)} current members")
    return all_members

if __name__ == '__main__':
    fetch_current_members()
```

#### Step 3: Fetch Detailed Member Information
```python
def fetch_member_details(bioguide_id):
    """Fetch detailed information for a specific member"""
    url = f"{BASE_URL}/member/{bioguide_id}"
    params = {'api_key': API_KEY, 'format': 'json'}

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()

def process_all_members():
    """Process all members and fetch detailed info"""
    with open(OUTPUT_DIR / 'current_members.json', 'r') as f:
        members = json.load(f)

    detailed_members = []

    for i, member in enumerate(members):
        bioguide_id = member.get('bioguideId')
        if bioguide_id:
            try:
                details = fetch_member_details(bioguide_id)
                detailed_members.append(details)

                # Save progress every 50 members
                if (i + 1) % 50 == 0:
                    with open(OUTPUT_DIR / f'member_details_{i+1}.json', 'w') as f:
                        json.dump(detailed_members, f, indent=2)
                    print(f"Processed {i+1} members...")

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"Error fetching {bioguide_id}: {e}")

    # Final save
    with open(OUTPUT_DIR / 'all_member_details.json', 'w') as f:
        json.dump(detailed_members, f, indent=2)

    print(f"Completed processing {len(detailed_members)} members")
```

#### Step 4: Transform and Load to Database
```python
#!/usr/bin/env python3
"""
Transform Congress member data and load to database
"""
import json
import psycopg2
import psycopg2.extras
from datetime import datetime

def transform_member_data(congress_data):
    """Transform Congress API data to unified schema"""
    member = congress_data.get('member', {})

    # Basic member info
    transformed = {
        'bioguide_id': member.get('bioguideId'),
        'first_name': member.get('firstName'),
        'last_name': member.get('lastName'),
        'full_name': member.get('name'),
        'party': member.get('partyName'),
        'state': member.get('state'),
        'district': member.get('district'),
        'chamber': member.get('chamber').lower() if member.get('chamber') else None,
        'current_member': member.get('currentMember', False),
        'member_type': 'federal'
    }

    # Terms served
    terms = member.get('terms', [])
    if terms:
        latest_term = max(terms, key=lambda x: x.get('startYear', 0))
        transformed.update({
            'start_year': latest_term.get('startYear'),
            'end_year': latest_term.get('endYear'),
            'served_years': len(terms)
        })

    # Social media
    social_media = []
    if member.get('twitterAccount'):
        social_media.append({
            'platform': 'twitter',
            'handle': member['twitterAccount'],
            'url': f"https://twitter.com/{member['twitterAccount']}"
        })

    if member.get('facebookAccount'):
        social_media.append({
            'platform': 'facebook',
            'handle': member['facebookAccount'],
            'url': member['facebookAccount']
        })

    if member.get('youtubeAccount'):
        social_media.append({
            'platform': 'youtube',
            'handle': member['youtubeAccount'],
            'url': f"https://youtube.com/{member['youtubeAccount']}"
        })

    transformed['social_media'] = social_media

    return transformed

def load_members_to_db(members_data, db_config):
    """Load transformed member data to database"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    for member in members_data:
        try:
            # Insert/update main member record
            cursor.execute("""
                INSERT INTO person (
                    id, full_name, first_name, last_name,
                    chamber, state, district, party,
                    member_type, current_member
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    chamber = EXCLUDED.chamber,
                    state = EXCLUDED.state,
                    district = EXCLUDED.district,
                    party = EXCLUDED.party,
                    current_member = EXCLUDED.current_member
            """, (
                member['bioguide_id'],
                member['full_name'],
                member['first_name'],
                member['last_name'],
                member['chamber'],
                member['state'],
                member['district'],
                member['party'],
                member['member_type'],
                member['current_member']
            ))

            # Insert social media accounts
            for sm in member.get('social_media', []):
                cursor.execute("""
                    INSERT INTO member_social_media (
                        member_id, platform, handle, url, is_official
                    ) VALUES (%s, %s, %s, %s, true)
                    ON CONFLICT (member_id, platform) DO UPDATE SET
                        handle = EXCLUDED.handle,
                        url = EXCLUDED.url,
                        last_updated = now()
                """, (
                    member['bioguide_id'],
                    sm['platform'],
                    sm['handle'],
                    sm['url']
                ))

        except Exception as e:
            print(f"Error loading member {member.get('bioguide_id')}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Loaded {len(members_data)} members to database")

# Main execution
if __name__ == '__main__':
    # Load member details
    with open('data/member_ingestion/all_member_details.json', 'r') as f:
        congress_members = json.load(f)

    # Transform data
    transformed_members = []
    for member_data in congress_members:
        transformed = transform_member_data(member_data)
        transformed_members.append(transformed)

    # Database config
    db_config = {
        'host': 'localhost',
        'database': 'openleg',
        'user': 'openleg',
        'password': 'password'
    }

    # Load to database
    load_members_to_db(transformed_members, db_config)
```

### Procedure 2: OpenStates API Integration

#### Step 1: Fetch State Legislators
```python
#!/usr/bin/env python3
"""
Fetch state legislators from OpenStates API
"""
import requests
import json
import time

API_KEY = "your_openstates_api_key"
BASE_URL = "https://openstates.org/api/v1"

def fetch_state_legislators(state_abbr):
    """Fetch legislators for a specific state"""
    url = f"{BASE_URL}/legislators/"
    params = {
        'apikey': API_KEY,
        'state': state_abbr,
        'active': 'true'
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()

def fetch_all_states():
    """Fetch legislators from multiple states"""
    states = ['ca', 'tx', 'fl', 'ny', 'il', 'pa', 'oh', 'ga', 'nc', 'mi']  # Top 10 by population

    all_legislators = []

    for state in states:
        try:
            legislators = fetch_state_legislators(state)
            all_legislators.extend(legislators)
            print(f"Fetched {len(legislators)} legislators from {state.upper()}")

            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"Error fetching {state}: {e}")

    # Save to file
    with open('data/member_ingestion/state_legislators.json', 'w') as f:
        json.dump(all_legislators, f, indent=2)

    print(f"Saved {len(all_legislators)} state legislators")
    return all_legislators

if __name__ == '__main__':
    fetch_all_states()
```

#### Step 2: Transform OpenStates Data
```python
def transform_openstates_data(openstates_data):
    """Transform OpenStates data to unified schema"""
    transformed = {
        'openstates_id': openstates_data.get('id'),
        'first_name': openstates_data.get('first_name'),
        'last_name': openstates_data.get('last_name'),
        'full_name': openstates_data.get('full_name'),
        'party': openstates_data.get('party'),
        'state': openstates_data.get('state').upper(),
        'district': openstates_data.get('district'),
        'chamber': openstates_data.get('chamber'),
        'current_member': True,
        'member_type': 'state'
    }

    # Contact information
    contacts = openstates_data.get('contact_details', [])
    if contacts:
        primary_contact = contacts[0]
        transformed.update({
            'email': primary_contact.get('email'),
            'phone': primary_contact.get('phone'),
            'address': primary_contact.get('address')
        })

    # Social media
    social_media = []
    if openstates_data.get('twitter'):
        social_media.append({
            'platform': 'twitter',
            'handle': openstates_data['twitter'],
            'url': f"https://twitter.com/{openstates_data['twitter']}"
        })

    if openstates_data.get('facebook'):
        social_media.append({
            'platform': 'facebook',
            'url': openstates_data['facebook']
        })

    if openstates_data.get('youtube'):
        social_media.append({
            'platform': 'youtube',
            'url': openstates_data['youtube']
        })

    transformed['social_media'] = social_media

    return transformed
```

### Procedure 3: Member Deduplication & Matching

#### Step 1: Cross-Reference Members
```python
def find_duplicate_members(federal_members, state_members):
    """Find potential duplicate members across federal/state"""
    duplicates = []

    for fed in federal_members:
        fed_name = f"{fed['first_name']} {fed['last_name']}".lower()
        fed_state = fed['state']

        for state in state_members:
            state_name = f"{state['first_name']} {state['last_name']}".lower()
            state_state = state['state']

            # Simple name matching (could be enhanced with fuzzy matching)
            if fed_name == state_name and fed_state == state_state:
                duplicates.append({
                    'federal_id': fed['bioguide_id'],
                    'state_id': state['openstates_id'],
                    'name': fed_name.title(),
                    'state': fed_state
                })

    return duplicates

def merge_member_records(master_member, duplicate_member):
    """Merge duplicate member records"""
    # Prefer federal data for federal members, state data for state members
    # Combine social media accounts
    # Update contact information
    pass
```

## Social Media Data Integration

### Procedure 4: Social Media Account Discovery

#### Step 1: Extract Social Media from Member Data
```python
def extract_social_media_accounts(members_data):
    """Extract all social media accounts from member data"""
    social_accounts = []

    for member in members_data:
        member_id = member.get('bioguide_id') or member.get('openstates_id')

        for sm in member.get('social_media', []):
            social_accounts.append({
                'member_id': member_id,
                'platform': sm['platform'],
                'handle': sm['handle'],
                'url': sm['url'],
                'is_official': True
            })

    return social_accounts

def validate_social_accounts(accounts):
    """Validate social media accounts exist and are official"""
    # Check Twitter handles
    # Verify Facebook pages
    # Confirm YouTube channels
    # This would require API calls to each platform
    pass
```

### Procedure 5: Social Media Content Collection

#### Step 1: Twitter API Integration
```python
import tweepy

def setup_twitter_api():
    """Setup Twitter API client"""
    # Use Twitter API v2
    client = tweepy.Client(
        bearer_token="your_bearer_token",
        consumer_key="your_consumer_key",
        consumer_secret="your_consumer_secret",
        access_token="your_access_token",
        access_token_secret="your_access_token_secret"
    )
    return client

def collect_tweets_for_member(member_id, twitter_handle, days_back=30):
    """Collect recent tweets for a legislator"""
    client = setup_twitter_api()

    # Get user ID from handle
    user = client.get_user(username=twitter_handle)
    user_id = user.data.id

    # Get recent tweets
    tweets = client.get_users_tweets(
        id=user_id,
        max_results=100,
        start_time=datetime.now() - timedelta(days=days_back)
    )

    collected_tweets = []
    for tweet in tweets.data:
        collected_tweets.append({
            'member_id': member_id,
            'platform': 'twitter',
            'post_id': tweet.id,
            'content': tweet.text,
            'posted_at': tweet.created_at,
            'engagement_metrics': {
                'retweets': tweet.public_metrics['retweet_count'],
                'likes': tweet.public_metrics['like_count'],
                'replies': tweet.public_metrics['reply_count']
            }
        })

    return collected_tweets
```

## Automation & Scheduling

### Cron Jobs for Regular Updates

```bash
# Daily member data updates
0 2 * * * /path/to/member_ingestion/update_members.sh

# Hourly social media collection during business hours
0 9-17 * * 1-5 /path/to/social_media/collect_tweets.sh

# Weekly social media analysis
0 3 * * 0 /path/to/social_media/analyze_content.sh
```

### Monitoring & Alerts

```bash
#!/bin/bash
# Member data freshness check

DB_CONFIG="/path/to/db_config.json"
THRESHOLD_DAYS=7

# Check when member data was last updated
LAST_UPDATE=$(python3 -c "
import json
import psycopg2
with open('$DB_CONFIG') as f:
    config = json.load(f)
conn = psycopg2.connect(**config)
cursor = conn.cursor()
cursor.execute('SELECT MAX(last_updated) FROM member_social_media')
result = cursor.fetchone()
print(result[0].strftime('%Y-%m-%d') if result[0] else 'never')
cursor.close()
conn.close()
")

# Send alert if data is stale
if [ "$LAST_UPDATE" = "never" ] || [ $(date -d "$LAST_UPDATE" +%s) -lt $(date -d "$THRESHOLD_DAYS days ago" +%s) ]; then
    echo "Member data is stale! Last update: $LAST_UPDATE"
    # Send notification
fi
```

## Quality Assurance

### Data Validation Checks

1. **Completeness**: Ensure all required fields are populated
2. **Accuracy**: Cross-reference data between sources
3. **Freshness**: Monitor update timestamps
4. **Duplicates**: Regular deduplication runs

### Performance Monitoring

- Track API response times
- Monitor database query performance
- Alert on failed ingestion jobs
- Report on data coverage metrics

This comprehensive member data ingestion framework provides the foundation for rich legislator profiles that enhance legislative analysis and constituent engagement tracking.
