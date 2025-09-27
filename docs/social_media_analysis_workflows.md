# Social Media Analysis and Ingestion Workflows

## Overview

This document outlines workflows for collecting, analyzing, and ingesting social media data from legislators and government accounts. The system provides insights into constituent engagement, policy communication, and public sentiment analysis.

## Architecture Components

### Data Collection Layer
- **Account Discovery**: Identify official social media accounts
- **Content Harvesting**: Collect posts, tweets, videos, and engagement metrics
- **Rate Limiting**: Respect platform API limits and terms of service
- **Data Storage**: Time-series storage of social media content

### Analysis Layer
- **Natural Language Processing**: Sentiment analysis, topic modeling
- **Engagement Analytics**: Track likes, shares, comments, reach
- **Network Analysis**: Identify influencers and communication patterns
- **Constituent Interaction**: Analyze public engagement patterns

### Integration Layer
- **Unified Schema**: Store social media data alongside legislative data
- **Cross-Referencing**: Link social media activity to legislative actions
- **Real-time Updates**: Streaming ingestion for active monitoring

## Data Sources & APIs

### Primary Platforms

#### 1. Twitter (X) API
- **API Version**: Twitter API v2
- **Authentication**: Bearer token + OAuth 2.0
- **Rate Limits**:
  - User tweets: 900 requests/15min (per user)
  - Recent search: 450 requests/15min
  - Academic access: Higher limits available
- **Data Available**: Tweets, retweets, likes, user profiles, engagement metrics

#### 2. Facebook Graph API
- **API Version**: Graph API v16+
- **Authentication**: App access token or user tokens
- **Rate Limits**: App-level (200 calls/hour) + user-level
- **Data Available**: Posts, comments, reactions, page insights, live videos

#### 3. YouTube Data API
- **API Version**: v3
- **Authentication**: API key + OAuth
- **Rate Limits**: 10,000 units/day (free), higher with billing
- **Data Available**: Videos, comments, channel statistics, live streams

#### 4. Instagram Basic Display API
- **API Version**: Basic Display API
- **Authentication**: Access tokens
- **Rate Limits**: 200 calls/hour per user
- **Data Available**: Posts, stories, profile information

## Database Schema

### Social Media Posts Table
```sql
CREATE TABLE IF NOT EXISTS social_media_post (
    id BIGSERIAL PRIMARY KEY,
    member_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('twitter', 'facebook', 'youtube', 'instagram')),
    post_id TEXT NOT NULL,
    content TEXT,
    posted_at TIMESTAMP NOT NULL,
    url TEXT,
    engagement_metrics JSONB,
    sentiment_score DECIMAL(3,2),
    topics TEXT[],
    hashtags TEXT[],
    mentions TEXT[],
    media_urls TEXT[],
    is_reply BOOLEAN DEFAULT false,
    reply_to_id TEXT,
    is_retweet BOOLEAN DEFAULT false,
    retweet_of_id TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(platform, post_id)
);

-- Indexes for performance
CREATE INDEX idx_social_member_platform ON social_media_post(member_id, platform);
CREATE INDEX idx_social_posted_at ON social_media_post(posted_at);
CREATE INDEX idx_social_platform_posted ON social_media_post(platform, posted_at);
CREATE INDEX idx_social_sentiment ON social_media_post(sentiment_score);
CREATE INDEX idx_social_topics ON social_media_post USING GIN(topics);
```

### Social Media Analytics Table
```sql
CREATE TABLE IF NOT EXISTS social_media_analytics (
    id BIGSERIAL PRIMARY KEY,
    member_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    date DATE NOT NULL,
    follower_count INTEGER,
    following_count INTEGER,
    total_posts INTEGER,
    engagement_rate DECIMAL(5,4),
    avg_likes INTEGER,
    avg_retweets INTEGER,
    avg_replies INTEGER,
    top_hashtags TEXT[],
    top_topics TEXT[],
    sentiment_trend DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(member_id, platform, date)
);
```

## Ingestion Workflows

### Workflow 1: Account Discovery & Validation

#### Step 1: Extract Accounts from Member Data
```python
#!/usr/bin/env python3
"""
Discover and validate social media accounts for legislators
"""
import psycopg2
import psycopg2.extras
import requests
import time
from urllib.parse import urlparse

def get_member_social_accounts(db_config):
    """Get all social media accounts from member data"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT member_id, platform, handle, url
        FROM member_social_media
        WHERE is_official = true
        ORDER BY member_id, platform
    """)

    accounts = cursor.fetchall()
    cursor.close()
    conn.close()

    return accounts

def validate_twitter_account(handle):
    """Validate Twitter account exists and get follower count"""
    # Use Twitter API to validate account
    # This is a simplified version - actual implementation would use API
    try:
        # Mock validation - replace with actual API call
        response = requests.get(f"https://twitter.com/{handle}", timeout=10)
        if response.status_code == 200:
            return {'valid': True, 'followers': 0}  # Would extract from API
        else:
            return {'valid': False, 'error': 'Account not found'}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def validate_facebook_account(url):
    """Validate Facebook page exists"""
    try:
        response = requests.get(url, timeout=10)
        return {'valid': response.status_code == 200}
    except:
        return {'valid': False}

def update_account_validation(db_config, member_id, platform, validation_result):
    """Update account validation status in database"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE member_social_media
        SET follower_count = %s,
            last_updated = now()
        WHERE member_id = %s AND platform = %s
    """, (
        validation_result.get('followers', 0),
        member_id,
        platform
    ))

    conn.commit()
    cursor.close()
    conn.close()

def validate_all_accounts(db_config):
    """Validate all social media accounts"""
    accounts = get_member_social_accounts(db_config)

    for account in accounts:
        member_id = account['member_id']
        platform = account['platform']
        handle = account['handle']
        url = account['url']

        print(f"Validating {platform} account for {member_id}: {handle}")

        if platform == 'twitter':
            result = validate_twitter_account(handle)
        elif platform == 'facebook':
            result = validate_facebook_account(url)
        else:
            result = {'valid': True}  # Assume valid for other platforms

        if result.get('valid'):
            update_account_validation(db_config, member_id, platform, result)
            print(f"✓ Valid: {handle}")
        else:
            print(f"✗ Invalid: {handle} - {result.get('error', 'Unknown error')}")

        time.sleep(1)  # Rate limiting

if __name__ == '__main__':
    db_config = {
        'host': 'localhost',
        'database': 'openleg',
        'user': 'openleg',
        'password': 'password'
    }

    validate_all_accounts(db_config)
```

### Workflow 2: Content Collection Pipeline

#### Step 1: Twitter Content Collection
```python
#!/usr/bin/env python3
"""
Collect Twitter content for legislators
"""
import tweepy
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
import time
import json

class TwitterCollector:
    def __init__(self, api_keys, db_config):
        self.client = tweepy.Client(
            bearer_token=api_keys['bearer_token'],
            consumer_key=api_keys['consumer_key'],
            consumer_secret=api_keys['consumer_secret'],
            access_token=api_keys['access_token'],
            access_token_secret=api_keys['access_token_secret']
        )
        self.db_config = db_config

    def get_member_twitter_handles(self):
        """Get all validated Twitter handles"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT msm.member_id, msm.handle,
                   p.full_name, p.state, p.party
            FROM member_social_media msm
            JOIN person p ON msm.member_id = p.id
            WHERE msm.platform = 'twitter'
            AND msm.handle IS NOT NULL
            ORDER BY msm.last_updated
        """)

        handles = cursor.fetchall()
        cursor.close()
        conn.close()

        return handles

    def collect_tweets_for_member(self, member_id, handle, days_back=7):
        """Collect recent tweets for a member"""
        try:
            # Get user ID from handle
            user = self.client.get_user(username=handle)
            if not user.data:
                return []

            user_id = user.data.id

            # Get recent tweets
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=100,
                start_time=datetime.now() - timedelta(days=days_back),
                tweet_fields=['created_at', 'public_metrics', 'context_annotations']
            )

            collected_tweets = []
            if tweets.data:
                for tweet in tweets.data:
                    collected_tweets.append({
                        'member_id': member_id,
                        'platform': 'twitter',
                        'post_id': str(tweet.id),
                        'content': tweet.text,
                        'posted_at': tweet.created_at,
                        'engagement_metrics': {
                            'retweets': tweet.public_metrics['retweet_count'],
                            'likes': tweet.public_metrics['like_count'],
                            'replies': tweet.public_metrics['reply_count'],
                            'quotes': tweet.public_metrics.get('quote_count', 0)
                        },
                        'url': f"https://twitter.com/{handle}/status/{tweet.id}"
                    })

            return collected_tweets

        except Exception as e:
            print(f"Error collecting tweets for {handle}: {e}")
            return []

    def save_tweets_to_db(self, tweets):
        """Save collected tweets to database"""
        if not tweets:
            return

        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        for tweet in tweets:
            try:
                cursor.execute("""
                    INSERT INTO social_media_post (
                        member_id, platform, post_id, content, posted_at,
                        url, engagement_metrics, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, now())
                    ON CONFLICT (platform, post_id) DO UPDATE SET
                        engagement_metrics = EXCLUDED.engagement_metrics,
                        updated_at = now()
                """, (
                    tweet['member_id'],
                    tweet['platform'],
                    tweet['post_id'],
                    tweet['content'],
                    tweet['posted_at'],
                    tweet['url'],
                    json.dumps(tweet['engagement_metrics'])
                ))
            except Exception as e:
                print(f"Error saving tweet {tweet['post_id']}: {e}")

        conn.commit()
        cursor.close()
        conn.close()

    def collect_all_tweets(self, days_back=7):
        """Collect tweets for all members"""
        handles = self.get_member_twitter_handles()

        total_collected = 0
        for handle_info in handles:
            member_id = handle_info['member_id']
            handle = handle_info['handle']
            full_name = handle_info['full_name']

            print(f"Collecting tweets for {full_name} (@{handle})")

            tweets = self.collect_tweets_for_member(member_id, handle, days_back)
            self.save_tweets_to_db(tweets)

            total_collected += len(tweets)
            print(f"Collected {len(tweets)} tweets")

            # Rate limiting - Twitter allows 900 requests per 15 minutes
            time.sleep(2)

        print(f"Total tweets collected: {total_collected}")

# Usage
if __name__ == '__main__':
    api_keys = {
        'bearer_token': 'your_bearer_token',
        'consumer_key': 'your_consumer_key',
        'consumer_secret': 'your_consumer_secret',
        'access_token': 'your_access_token',
        'access_token_secret': 'your_access_token_secret'
    }

    db_config = {
        'host': 'localhost',
        'database': 'openleg',
        'user': 'openleg'
    }

    collector = TwitterCollector(api_keys, db_config)
    collector.collect_all_tweets(days_back=7)
```

### Workflow 3: Content Analysis Pipeline

#### Step 1: Sentiment Analysis
```python
#!/usr/bin/env python3
"""
Analyze sentiment and topics in social media posts
"""
import psycopg2
import psycopg2.extras
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import re
from collections import Counter

class SocialMediaAnalyzer:
    def __init__(self, db_config, use_gpu=True):
        self.db_config = db_config
        self.device = 0 if use_gpu and torch.cuda.is_available() else -1

        # Load sentiment analysis model
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
            device=self.device
        )

        # Load topic modeling (simplified - could use BERTopic or similar)
        self.topic_keywords = {
            'healthcare': ['health', 'medicare', 'medicaid', 'hospital', 'doctor'],
            'economy': ['economy', 'jobs', 'tax', 'budget', 'spending', 'deficit'],
            'education': ['education', 'school', 'student', 'teacher', 'college'],
            'environment': ['climate', 'environment', 'energy', 'clean', 'green'],
            'immigration': ['immigration', 'border', 'migrant', 'visa', 'asylum'],
            'foreign_policy': ['foreign', 'china', 'russia', 'nato', 'diplomacy']
        }

    def get_unanalyzed_posts(self, limit=1000):
        """Get posts that haven't been analyzed yet"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("""
            SELECT id, content, platform
            FROM social_media_post
            WHERE sentiment_score IS NULL
            AND content IS NOT NULL
            ORDER BY posted_at DESC
            LIMIT %s
        """, (limit,))

        posts = cursor.fetchall()
        cursor.close()
        conn.close()

        return posts

    def analyze_sentiment(self, text):
        """Analyze sentiment of text"""
        try:
            result = self.sentiment_analyzer(text[:512])  # Limit text length
            sentiment_map = {'LABEL_0': -1.0, 'LABEL_1': 0.0, 'LABEL_2': 1.0}
            return sentiment_map.get(result[0]['label'], 0.0)
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return 0.0

    def extract_topics(self, text):
        """Extract topics from text using keyword matching"""
        text_lower = text.lower()
        topics = []

        for topic, keywords in self.topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)

        return topics if topics else ['general']

    def extract_hashtags_mentions(self, text, platform):
        """Extract hashtags and mentions from text"""
        hashtags = []
        mentions = []

        if platform == 'twitter':
            # Extract hashtags
            hashtag_pattern = r'#(\w+)'
            hashtags = re.findall(hashtag_pattern, text)

            # Extract mentions
            mention_pattern = r'@(\w+)'
            mentions = re.findall(mention_pattern, text)

        return hashtags, mentions

    def analyze_post(self, post):
        """Analyze a single post"""
        content = post['content']
        platform = post['platform']

        # Sentiment analysis
        sentiment = self.analyze_sentiment(content)

        # Topic extraction
        topics = self.extract_topics(content)

        # Hashtags and mentions
        hashtags, mentions = self.extract_hashtags_mentions(content, platform)

        return {
            'sentiment_score': sentiment,
            'topics': topics,
            'hashtags': hashtags,
            'mentions': mentions
        }

    def update_post_analysis(self, post_id, analysis):
        """Update post with analysis results"""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE social_media_post
            SET sentiment_score = %s,
                topics = %s,
                hashtags = %s,
                mentions = %s,
                updated_at = now()
            WHERE id = %s
        """, (
            analysis['sentiment_score'],
            analysis['topics'],
            analysis['hashtags'],
            analysis['mentions'],
            post_id
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def analyze_unanalyzed_posts(self):
        """Analyze all unanalyzed posts"""
        posts = self.get_unanalyzed_posts()

        print(f"Analyzing {len(posts)} posts...")

        for i, post in enumerate(posts):
            if (i + 1) % 100 == 0:
                print(f"Analyzed {i + 1}/{len(posts)} posts")

            analysis = self.analyze_post(post)
            self.update_post_analysis(post['id'], analysis)

        print("Analysis complete!")

# Usage
if __name__ == '__main__':
    db_config = {
        'host': 'localhost',
        'database': 'openleg',
        'user': 'openleg'
    }

    analyzer = SocialMediaAnalyzer(db_config, use_gpu=True)
    analyzer.analyze_unanalyzed_posts()
```

### Workflow 4: Analytics & Reporting

#### Step 1: Generate Member Analytics
```python
#!/usr/bin/env python3
"""
Generate social media analytics for legislators
"""
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from collections import Counter
import json

def generate_member_analytics(db_config, member_id, platform, days=30):
    """Generate analytics for a member's social media activity"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    start_date = datetime.now() - timedelta(days=days)

    # Get posts for the period
    cursor.execute("""
        SELECT posted_at, engagement_metrics, sentiment_score,
               topics, hashtags, mentions
        FROM social_media_post
        WHERE member_id = %s
        AND platform = %s
        AND posted_at >= %s
        ORDER BY posted_at
    """, (member_id, platform, start_date))

    posts = cursor.fetchall()

    if not posts:
        cursor.close()
        conn.close()
        return None

    # Calculate metrics
    total_posts = len(posts)

    # Engagement metrics
    total_likes = sum(json.loads(p['engagement_metrics'] or '{}').get('likes', 0) for p in posts)
    total_retweets = sum(json.loads(p['engagement_metrics'] or '{}').get('retweets', 0) for p in posts)
    total_replies = sum(json.loads(p['engagement_metrics'] or '{}').get('replies', 0) for p in posts)

    avg_likes = total_likes / total_posts if total_posts > 0 else 0
    avg_retweets = total_retweets / total_posts if total_posts > 0 else 0
    avg_replies = total_replies / total_posts if total_posts > 0 else 0

    # Engagement rate (simplified)
    engagement_rate = (total_likes + total_retweets + total_replies) / total_posts if total_posts > 0 else 0

    # Sentiment analysis
    sentiment_scores = [p['sentiment_score'] for p in posts if p['sentiment_score'] is not None]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

    # Top topics
    all_topics = []
    for p in posts:
        all_topics.extend(p['topics'] or [])
    top_topics = [topic for topic, count in Counter(all_topics).most_common(5)]

    # Top hashtags
    all_hashtags = []
    for p in posts:
        all_hashtags.extend(p['hashtags'] or [])
    top_hashtags = [tag for tag, count in Counter(all_hashtags).most_common(10)]

    # Get follower count
    cursor.execute("""
        SELECT follower_count
        FROM member_social_media
        WHERE member_id = %s AND platform = %s
    """, (member_id, platform))

    follower_result = cursor.fetchone()
    follower_count = follower_result['follower_count'] if follower_result else 0

    cursor.close()
    conn.close()

    analytics = {
        'member_id': member_id,
        'platform': platform,
        'date': datetime.now().date(),
        'follower_count': follower_count,
        'total_posts': total_posts,
        'engagement_rate': round(engagement_rate, 4),
        'avg_likes': round(avg_likes, 2),
        'avg_retweets': round(avg_retweets, 2),
        'avg_replies': round(avg_replies, 2),
        'sentiment_trend': round(avg_sentiment, 2),
        'top_topics': top_topics,
        'top_hashtags': top_hashtags
    }

    return analytics

def save_analytics_to_db(db_config, analytics):
    """Save analytics to database"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO social_media_analytics (
            member_id, platform, date, follower_count, total_posts,
            engagement_rate, avg_likes, avg_retweets, avg_replies,
            sentiment_trend, top_topics, top_hashtags
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (member_id, platform, date) DO UPDATE SET
            follower_count = EXCLUDED.follower_count,
            total_posts = EXCLUDED.total_posts,
            engagement_rate = EXCLUDED.engagement_rate,
            avg_likes = EXCLUDED.avg_likes,
            avg_retweets = EXCLUDED.avg_retweets,
            avg_replies = EXCLUDED.avg_replies,
            sentiment_trend = EXCLUDED.sentiment_trend,
            top_topics = EXCLUDED.top_topics,
            top_hashtags = EXCLUDED.top_hashtags
    """, (
        analytics['member_id'],
        analytics['platform'],
        analytics['date'],
        analytics['follower_count'],
        analytics['total_posts'],
        analytics['engagement_rate'],
        analytics['avg_likes'],
        analytics['avg_retweets'],
        analytics['avg_replies'],
        analytics['sentiment_trend'],
        analytics['top_topics'],
        analytics['top_hashtags']
    ))

    conn.commit()
    cursor.close()
    conn.close()

def generate_all_analytics(db_config, days=30):
    """Generate analytics for all active members"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get all members with social media accounts
    cursor.execute("""
        SELECT DISTINCT sm.member_id, sm.platform
        FROM member_social_media sm
        JOIN person p ON sm.member_id = p.id
        WHERE sm.handle IS NOT NULL
        AND p.current_member = true
    """)

    members = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"Generating analytics for {len(members)} member-platform combinations...")

    for member in members:
        analytics = generate_member_analytics(
            db_config,
            member['member_id'],
            member['platform'],
            days
        )

        if analytics:
            save_analytics_to_db(db_config, analytics)
            print(f"Generated analytics for {member['member_id']} ({member['platform']})")

# Usage
if __name__ == '__main__':
    db_config = {
        'host': 'localhost',
        'database': 'openleg',
        'user': 'openleg'
    }

    generate_all_analytics(db_config, days=30)
```

## Automation & Scheduling

### Cron Jobs for Social Media Pipeline

```bash
# Daily content collection (9 AM - 6 PM business hours)
0 9,12,15,18 * * 1-5 /path/to/social_media/collect_content.sh

# Hourly sentiment analysis
0 * * * * /path/to/social_media/analyze_sentiment.sh

# Daily analytics generation
30 2 * * * /path/to/social_media/generate_analytics.sh

# Weekly comprehensive report
0 3 * * 0 /path/to/social_media/weekly_report.sh
```

### Monitoring & Quality Assurance

#### Data Freshness Checks
```python
def check_data_freshness(db_config):
    """Check if social media data is current"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Check latest post date
    cursor.execute("""
        SELECT MAX(posted_at) as latest_post,
               COUNT(*) as total_posts
        FROM social_media_post
        WHERE posted_at >= CURRENT_DATE - INTERVAL '7 days'
    """)

    result = cursor.fetchone()
    latest_post = result[0]
    recent_posts = result[1]

    cursor.close()
    conn.close()

    # Alert if no recent posts
    if recent_posts < 100:  # Arbitrary threshold
        print(f"WARNING: Only {recent_posts} posts in the last 7 days")

    return latest_post, recent_posts
```

#### API Rate Limit Monitoring
```python
def check_api_limits():
    """Monitor API rate limits and usage"""
    # Twitter API limits
    # Facebook API limits
    # YouTube API limits
    # Send alerts when approaching limits
    pass
```

## Integration with Legislative Analysis

### Cross-Reference Social Media with Legislation

```python
def correlate_social_legislation(db_config, member_id, topic):
    """Find correlation between social media topics and legislation"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Find bills by this member on the topic
    cursor.execute("""
        SELECT b.bill_print_no, b.title, b.congress,
               COUNT(smp.id) as social_posts
        FROM master.bill b
        JOIN master.bill_sponsor bs ON b.bill_print_no = bs.bill_print_no
        LEFT JOIN social_media_post smp ON bs.session_member_id = smp.member_id
            AND smp.topics @> ARRAY[%s]
        WHERE bs.session_member_id = %s
        AND b.congress >= 117
        GROUP BY b.bill_print_no, b.title, b.congress
        ORDER BY social_posts DESC
    """, (topic, member_id))

    correlations = cursor.fetchall()
    cursor.close()
    conn.close()

    return correlations
```

This comprehensive social media analysis framework provides deep insights into legislator communication patterns, constituent engagement, and policy discussions across multiple platforms.
