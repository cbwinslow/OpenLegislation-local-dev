# Member Data Ingestion Procedures

## Overview

This document details the ingestion of legislator/member data into OpenLegislation's database from federal and state sources. It builds on the project summary by providing step-by-step procedures, schema extensions, and automation for comprehensive member profiles including biography, contacts, and social media.

### Key Goals
- Unify data from Congress.gov, OpenStates, and secondary sources.
- Extend schema for social media and biography.
- Ensure deduplication across federal/state levels.
- Enable resumeable, monitored ingestion.

## Data Sources

### Primary Sources
- **Congress.gov API**: Current/historical federal members (https://api.congress.gov/v3/member). Requires API key; rate limits: 1000/hr.
- **OpenStates API**: State legislators (https://openstates.org/api/v1/legislators/). Free tier: 1000/day.

### Secondary Sources
- **Biographical Directory of Congress**: Detailed bios/photos (https://bioguide.congress.gov/) via scraping.
- **State Websites**: State-specific data via scraping/APIs.

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

-- Indexes
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

## Ingestion Flow Diagram

```mermaid
flowchart TD
    A[Sources<br/>Congress.gov API<br/>OpenStates API] --> B[Fetch Scripts<br/>requests.get with params<br/>Rate limiting (time.sleep)]
    B --> C[Transform Functions<br/>Map API JSON to schema<br/>Extract social media]
    C --> D[Deduplication<br/>Name/state matching<br/>Fuzzy if needed]
    D --> E[Load to DB<br/>psycopg2 INSERT ON CONFLICT<br/>Social/biography inserts]
    E --> F[Validation<br/>Completeness checks<br/>Freshness monitors]
    F --> G[Social Collection<br/>Twitter API (tweepy)<br/>Periodic cron]
    B -.->|Progress JSON| H[Tracker<br/>BaseIngestionProcess]
    E -.->|Alerts| I[Monitoring<br/>Stale data notifications]
```

## Procedures

### Procedure 1: Congress.gov API Ingestion

#### Setup
```bash
export CONGRESS_API_KEY="your_key"
mkdir -p data/member_ingestion
cd data/member_ingestion
```

#### Fetch Current Members
```python
import requests
import json
import time
from pathlib import Path

API_KEY = "your_key"
BASE_URL = "https://api.congress.gov/v3"
OUTPUT_DIR = Path("data/member_ingestion")

def fetch_current_members():
    url = f"{BASE_URL}/member"
    params = {'api_key': API_KEY, 'format': 'json', 'currentMember': 'true', 'limit': 250}
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
        time.sleep(1)  # Rate limit
    with open(OUTPUT_DIR / 'current_members.json', 'w') as f:
        json.dump(all_members, f, indent=2)
    return all_members

if __name__ == '__main__':
    fetch_current_members()
```

#### Fetch/Details & Transform/Load
(Refer to original doc for full code; includes fetch_member_details, transform_member_data with party/state/chamber, load_members_to_db with upsert for person and social_media tables.)

### Procedure 2: OpenStates API Integration
Similar fetch/transform for state data, adding contacts, social from API fields.

#### Transform Example
```python
def transform_openstates_data(data):
    return {
        'openstates_id': data.get('id'),
        'first_name': data.get('first_name'),
        'last_name': data.get('last_name'),
        'full_name': data.get('full_name'),
        'party': data.get('party'),
        'state': data.get('state').upper(),
        'district': data.get('district'),
        'chamber': data.get('chamber'),
        'current_member': True,
        'member_type': 'state',
        'social_media': [  # Extract twitter, facebook, etc.
            {'platform': 'twitter', 'handle': data.get('twitter'), 'url': f"https://twitter.com/{data['twitter']}"}
        ]
    }
```

### Procedure 3: Deduplication & Matching
```python
def find_duplicates(federal, state):
    duplicates = []
    for fed in federal:
        fed_name = f"{fed['first_name']} {fed['last_name']}".lower()
        for st in state:
            if fed_name == f"{st['first_name']} {st['last_name']}".lower() and fed['state'] == st['state']:
                duplicates.append({'federal_id': fed['bioguide_id'], 'state_id': st['openstates_id']})
    return duplicates
```

### Procedure 4: Social Media Integration
Use tweepy for Twitter collection:
```python
import tweepy
from datetime import timedelta

def collect_tweets(member_id, handle, days_back=30):
    client = tweepy.Client(bearer_token="token")  # Setup
    user = client.get_user(username=handle)
    tweets = client.get_users_tweets(id=user.data.id, start_time=datetime.now() - timedelta(days=days_back))
    # Process to member_social_media or separate content table
```

## Automation & Monitoring

### Cron Examples
```bash
# Daily updates
0 2 * * * python3 tools/ingest_federal_members.py --daily

# Social collection
0 9-17 * * 1-5 python3 tools/collect_social.py
```

### Monitoring Script Snippet
Check last_updated in member_social_media; alert if >7 days stale.

## Quality Assurance
- **Validation**: Ensure required fields, cross-source accuracy.
- **Performance**: Monitor API times, DB queries.
- **Coverage**: Track federal/state member counts.

This procedure integrates with the generic ingestion framework (base_ingestion_process.py) for tracking/resume.
