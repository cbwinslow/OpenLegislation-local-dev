-- Migration: Add federal social media posts table for ingesting historical content
-- Links to federal_member via member_id
-- Includes kg_entities JSONB for knowledge graph marking (people, events, incidents)

-- Create federal social media post table
CREATE TABLE IF NOT EXISTS master.federal_social_media_post (
    id BIGSERIAL PRIMARY KEY,
    social_media_id BIGINT REFERENCES master.federal_member_social_media(id) ON DELETE CASCADE,
    member_id BIGINT REFERENCES master.federal_member(id) ON DELETE CASCADE,  -- Denormalized for queries
    platform TEXT NOT NULL CHECK (platform IN ('twitter', 'facebook', 'youtube', 'instagram')),
    post_id TEXT NOT NULL,
    content TEXT,
    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    url TEXT,
    engagement_metrics JSONB,
    kg_entities JSONB DEFAULT '{}',  -- For KG: {"people": ["@user1"], "events": ["date/hashtag"], "incidents": ["keyword1"]}
    topics TEXT[] DEFAULT '{}',
    hashtags TEXT[] DEFAULT '{}',
    mentions TEXT[] DEFAULT '{}',
    media_urls TEXT[] DEFAULT '{}',
    is_reply BOOLEAN DEFAULT false,
    reply_to_id TEXT,
    is_retweet BOOLEAN DEFAULT false,
    retweet_of_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(platform, post_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_federal_social_member_platform ON master.federal_social_media_post(member_id, platform);
CREATE INDEX IF NOT EXISTS idx_federal_social_posted_at ON master.federal_social_media_post(posted_at);
CREATE INDEX IF NOT EXISTS idx_federal_social_platform_posted ON master.federal_social_media_post(platform, posted_at);
CREATE INDEX IF NOT EXISTS idx_federal_social_kg_entities ON master.federal_social_media_post USING GIN(kg_entities);
CREATE INDEX IF NOT EXISTS idx_federal_social_topics ON master.federal_social_media_post USING GIN(topics);
CREATE INDEX IF NOT EXISTS idx_federal_social_mentions ON master.federal_social_media_post USING GIN(mentions);

-- Optional analytics table (for future use)
CREATE TABLE IF NOT EXISTS master.federal_social_media_analytics (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL REFERENCES master.federal_member(id) ON DELETE CASCADE,
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(member_id, platform, date)
);

-- Index for analytics
CREATE INDEX IF NOT EXISTS idx_federal_social_analytics_member_date ON master.federal_social_media_analytics(member_id, date);

-- View for member social overview (integrate with GraphQL)
CREATE OR REPLACE VIEW master.v_federal_member_social_details AS
SELECT 
    fm.id as member_id,
    fp.bioguide_id,
    fp.full_name,
    fm.chamber,
    fm.state,
    fm.party,
    fms.platform,
    fms.handle,
    fms.url,
    COUNT(fsp.id) as post_count,
    MAX(fsp.posted_at) as latest_post,
    AVG((fsp.kg_entities->'sentiment' or null::numeric)) as avg_sentiment  -- If added later
FROM master.federal_member fm
JOIN master.federal_person fp ON fm.person_id = fp.id
LEFT JOIN master.federal_member_social_media fms ON fm.id = fms.member_id
LEFT JOIN master.federal_social_media_post fsp ON fms.id = fsp.social_media_id
GROUP BY fm.id, fp.bioguide_id, fp.full_name, fm.chamber, fm.state, fm.party, fms.platform, fms.handle, fms.url;
