#!/usr/bin/env python3
"""
Ingest Historical Twitter Posts from Federal Members

Fetches all historical tweets for members with Twitter accounts in federal_member_social_media.
Uses Twitter API v2 via tweepy. Starts from most recent and paginates backwards.
Extracts basic entity markings for knowledge graph: people (mentions), events (dates/hashtags), incidents (keywords).

Usage:
    python3 tools/ingest_member_tweets.py --db-config tools/db_config.json

Requirements:
    - Twitter API v2 credentials: TWITTER_BEARER_TOKEN, TWITTER_CONSUMER_KEY, etc. in .env
    - Database with federal_social_media_post table applied
    - tweepy: pip install tweepy
    - python-dateutil: pip install python-dateutil
"""

import os
import json
import sys
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import psycopg2
import psycopg2.extras
import tweepy
from dateutil import parser

from settings import settings
from base_ingestion_process import BaseIngestionProcess, run_ingestion_process


class TwitterIngestionProcess(BaseIngestionProcess):
    """Ingests historical Twitter posts for federal members using the generic framework"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Database connection
        self.conn = psycopg2.connect(**self.db_config)
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Twitter API setup
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN') or settings.twitter_bearer_token
        self.consumer_key = os.getenv('TWITTER_CONSUMER_KEY') or settings.twitter_consumer_key
        self.consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET') or settings.twitter_consumer_secret
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN') or settings.twitter_access_token
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET') or settings.twitter_access_token_secret

        if not self.bearer_token:
            raise ValueError("Twitter Bearer Token must be provided via env or settings")

        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
            wait_on_rate_limit=True  # Auto-handle rate limits
        )

        self.processed_posts = set()
        self.error_count = 0
        self.max_errors = settings.get('max_errors', 10)

    def get_data_source(self) -> str:
        """Return data source identifier"""
        return "twitter_api_v2"

    def get_target_table(self) -> str:
        """Return target table name for tracking"""
        return "master.federal_social_media_post"

    def get_record_id_column(self) -> str:
        """Return record ID column"""
        return "post_id"

    def discover_records(self) -> List[Dict[str, Any]]:
        """Discover Twitter accounts from existing social media data"""
        print("Fetching Twitter handles from database...")

        self.cursor.execute("""
            SELECT fms.id as social_media_id,
                   fm.id as member_id,
                   fp.full_name,
                   fp.bioguide_id,
                   fms.handle
            FROM master.federal_member_social_media fms
            JOIN master.federal_member fm ON fms.member_id = fm.id
            JOIN master.federal_person fp ON fm.person_id = fp.id
            WHERE fms.platform = 'twitter'
            AND fms.handle IS NOT NULL
            AND fms.url IS NOT NULL
            ORDER BY fp.full_name
        """)

        accounts = self.cursor.fetchall()
        records = []

        for account in accounts:
            handle = account['handle']
            if handle.startswith('@'):
                handle = handle[1:]  # Remove @ if present
            records.append({
                "record_id": f"twitter_user_{handle}",  # Unique per user for tracking
                "handle": handle,
                "member_id": account['member_id'],
                "social_media_id": account['social_media_id'],
                "full_name": account['full_name'],
                "bioguide_id": account['bioguide_id'],
                "metadata": account
            })

        print(f"Discovered {len(records)} Twitter accounts")
        return records

    def process_record(self, record: Dict[str, Any]) -> bool:
        """Process historical tweets for a single Twitter account"""
        handle = record["handle"]
        member_id = record["member_id"]
        social_media_id = record["social_media_id"]
        full_name = record["full_name"]

        print(f"\nProcessing tweets for {full_name} (@{handle})...")

        # Get user ID
        user = self.client.get_user(username=handle)
        if not user.data:
            self._handle_error(f"User @{handle} not found on Twitter")
            return False

        user_id = user.data.id
        print(f"User ID: {user_id}")

        # Fetch all historical tweets (paginate backwards from recent)
        tweets = self._fetch_all_tweets(user_id)
        if not tweets:
            print(f"No tweets found for @{handle}")
            return True

        # Process and insert tweets
        inserted_count = 0
        for tweet in tweets:
            if self._insert_tweet(tweet, member_id, social_media_id, handle):
                inserted_count += 1

        print(f"Inserted/updated {inserted_count} tweets for @{handle}")
        return True

    def _fetch_all_tweets(self, user_id: int) -> List[tweepy.Tweet]:
        """Fetch all historical tweets for a user, starting from most recent"""
        all_tweets = []
        pagination_token = None

        while True:
            try:
                tweets = self.client.get_users_tweets(
                    id=user_id,
                    max_results=100,  # Max per page
                    pagination_token=pagination_token,
                    tweet_fields=[
                        'created_at', 'public_metrics', 'context_annotations',
                        'entities', 'geo', 'referenced_tweets', 'attachments'
                    ],
                    expansions=['attachments.media_keys'],
                    media_fields=['type', 'url']
                )

                if not tweets.data:
                    break

                all_tweets.extend(tweets.data)

                if 'meta' in tweets.includes and tweets.includes['meta'].get('next_token'):
                    pagination_token = tweets.includes['meta']['next_token']
                    print(f"Fetching next page... ({len(all_tweets)} tweets so far)")
                    time.sleep(1)  # Rate limit courtesy
                else:
                    break

            except tweepy.TooManyRequests:
                print("Rate limit hit, waiting 15 minutes...")
                time.sleep(900)
            except Exception as e:
                self._handle_error(f"Error fetching tweets for user {user_id}: {e}")
                break

        # Sort by created_at descending (most recent first)
        all_tweets.sort(key=lambda t: t.created_at, reverse=True)
        print(f"Fetched {len(all_tweets)} total historical tweets")
        return all_tweets

    def _insert_tweet(self, tweet: tweepy.Tweet, member_id: int, social_media_id: int, handle: str) -> bool:
        """Insert or update a single tweet with entity extraction"""
        try:
            post_id = str(tweet.id)
            content = tweet.text or ''
            posted_at = tweet.created_at if tweet.created_at else datetime.now(timezone.utc)
            url = f"https://twitter.com/{handle}/status/{post_id}"

            # Engagement metrics
            public_metrics = tweet.public_metrics
            engagement_metrics = {
                'retweets': public_metrics['retweet_count'],
                'likes': public_metrics['like_count'],
                'replies': public_metrics['reply_count'],
                'quotes': public_metrics.get('quote_count', 0),
                'impressions': public_metrics.get('impression_count', 0)
            }

            # Extract entities
            hashtags, mentions, media_urls = self._extract_entities(tweet)

            # Basic KG marking
            kg_entities = self._extract_kg_entities(content)

            # Check if reply or retweet
            is_reply = False
            reply_to_id = None
            is_retweet = False
            retweet_of_id = None

            if tweet.referenced_tweets:
                for ref_tweet in tweet.referenced_tweets:
                    if ref.type == 'replied_to':
                        is_reply = True
                        reply_to_id = str(ref.id)
                    elif ref.type == 'retweeted':
                        is_retweet = True
                        retweet_of_id = str(ref.id)

            # Insert or update
            self.cursor.execute("""
                INSERT INTO master.federal_social_media_post (
                    social_media_id, member_id, platform, post_id, content,
                    posted_at, url, engagement_metrics, kg_entities,
                    hashtags, mentions, media_urls, is_reply, reply_to_id,
                    is_retweet, retweet_of_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (platform, post_id) DO UPDATE SET
                    engagement_metrics = EXCLUDED.engagement_metrics,
                    kg_entities = EXCLUDED.kg_entities,
                    hashtags = EXCLUDED.hashtags,
                    mentions = EXCLUDED.mentions,
                    media_urls = EXCLUDED.media_urls,
                    is_reply = EXCLUDED.is_reply,
                    reply_to_id = EXCLUDED.reply_to_id,
                    is_retweet = EXCLUDED.is_retweet,
                    retweet_of_id = EXCLUDED.retweet_of_id,
                    updated_at = now()
            """, (
                social_media_id, member_id, 'twitter', post_id, content,
                posted_at, url, json.dumps(engagement_metrics), json.dumps(kg_entities),
                hashtags, mentions, media_urls, is_reply, reply_to_id,
                is_retweet, retweet_of_id
            ))

            self.conn.commit()
            return True

        except Exception as e:
            self._handle_error(f"Error inserting tweet {post_id}: {e}")
            self.conn.rollback()
            return False

    def _extract_entities(self, tweet: tweepy.Tweet) -> tuple:
        """Extract hashtags, mentions, media from tweet entities"""
        hashtags = [entity['tag'] for entity in (tweet.entities.get('hashtags', []) or [])]
        mentions = [entity['username'] for entity in (tweet.entities.get('mentions', []) or [])]

        media_urls = []
        if hasattr(tweet, 'attachments') and tweet.attachments:
            # Would need includes for media, but simplify
            media_urls = ['https://twitter.com/media/placeholder']  # Placeholder; expand with includes

        return hashtags, mentions, media_urls

    def _extract_kg_entities(self, content: str) -> Dict[str, List[str]]:
        """Basic extraction for KG: people (mentions), events (dates/hashtags), incidents (keywords)"""
        kg = {'people': [], 'events': [], 'incidents': []}

        # People: already have mentions, but ensure
        mention_pattern = r'@(\w+)'
        people = re.findall(mention_pattern, content)
        if people:
            kg['people'] = list(set(people))  # Unique

        # Events: simple date or hashtag patterns
        date_pattern = r'\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b'
        dates = re.findall(date_pattern, content)
        hashtags = [h.lower() for h in re.findall(r'#(\w+)', content)]
        events = dates + hashtags
        if events:
            kg['events'] = list(set(events))[:10]  # Limit

        # Incidents: keyword matching
        incident_keywords = ['incident', 'scandal', 'protest', 'riot', 'crisis', 'emergency', 'controversy']
        incidents = [kw for kw in incident_keywords if kw.lower() in content.lower()]
        if incidents:
            kg['incidents'] = incidents

        return kg

    def _handle_error(self, message: str, fatal: bool = False):
        """Handle errors"""
        self.error_count += 1
        print(f"✗ {message} (error {self.error_count}/{self.max_errors})")
        if fatal or self.error_count >= self.max_errors:
            self.conn.rollback()
            self.close()
            sys.exit(1)

    def close(self):
        """Cleanup"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()
        super().close()


if __name__ == "__main__":
    run_ingestion_process(TwitterIngestionProcess, "Federal Member Tweets")
