-- Flyway migration: Create comprehensive federal data model tables
-- This migration creates all necessary tables for federal legislative data ingestion

-- Federal Members Table
CREATE TABLE IF NOT EXISTS master.federal_members (
    id BIGSERIAL PRIMARY KEY,
    bioguide_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    chamber VARCHAR(20) NOT NULL CHECK (chamber IN ('HOUSE', 'SENATE', 'JOINT')),
    state VARCHAR(2),
    district VARCHAR(10),
    party VARCHAR(1),
    current_member BOOLEAN NOT NULL DEFAULT true,
    office_address TEXT,
    office_phone VARCHAR(20),
    office_fax VARCHAR(20),
    website_url VARCHAR(500),
    leadership_positions TEXT[],
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    updated_at DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Federal Member Terms Table
CREATE TABLE IF NOT EXISTS master.federal_member_terms (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL REFERENCES master.federal_members(id) ON DELETE CASCADE,
    congress INTEGER NOT NULL,
    start_year INTEGER NOT NULL,
    end_year INTEGER,
    party VARCHAR(1),
    state VARCHAR(2),
    district VARCHAR(10),
    chamber VARCHAR(20) NOT NULL,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE(member_id, congress, chamber)
);

-- Federal Member Committees Table
CREATE TABLE IF NOT EXISTS master.federal_member_committees (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL REFERENCES master.federal_members(id) ON DELETE CASCADE,
    committee_name VARCHAR(255) NOT NULL,
    committee_code VARCHAR(50),
    chamber VARCHAR(20),
    role VARCHAR(50),
    start_date DATE,
    end_date DATE,
    subcommittee VARCHAR(255),
    created_at DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Federal Member Social Media Table
CREATE TABLE IF NOT EXISTS master.federal_member_social_media (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL REFERENCES master.federal_members(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    handle VARCHAR(100),
    url VARCHAR(500),
    follower_count INTEGER,
    following_count INTEGER,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    is_official BOOLEAN NOT NULL DEFAULT true,
    last_updated DATE,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE(member_id, platform)
);

-- Federal Committees Table
CREATE TABLE IF NOT EXISTS master.federal_committees (
    id BIGSERIAL PRIMARY KEY,
    committee_code VARCHAR(50) UNIQUE NOT NULL,
    committee_name VARCHAR(255) NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    committee_type VARCHAR(50), -- standing, select, joint, etc.
    jurisdiction TEXT,
    established_date DATE,
    dissolved_date DATE,
    current_committee BOOLEAN NOT NULL DEFAULT true,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    updated_at DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Federal Committee Members Table (for committee membership tracking)
CREATE TABLE IF NOT EXISTS master.federal_committee_members (
    id BIGSERIAL PRIMARY KEY,
    committee_id BIGINT NOT NULL REFERENCES master.federal_committees(id) ON DELETE CASCADE,
    member_id BIGINT NOT NULL REFERENCES master.federal_members(id) ON DELETE CASCADE,
    role VARCHAR(50), -- chair, ranking member, member, etc.
    start_date DATE,
    end_date DATE,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE(committee_id, member_id, start_date)
);

-- Federal Bills Table (extended from existing bills table)
-- Note: This assumes the existing bills table will be extended with federal fields
-- If not already done, add these columns:
-- ALTER TABLE master.bills ADD COLUMN IF NOT EXISTS federal_congress INTEGER;
-- ALTER TABLE master.bills ADD COLUMN IF NOT EXISTS federal_source VARCHAR(50) DEFAULT 'unknown';

-- Federal Laws Table
CREATE TABLE IF NOT EXISTS master.federal_laws (
    id BIGSERIAL PRIMARY KEY,
    law_id VARCHAR(50) UNIQUE NOT NULL, -- e.g., "PUB-L-1"
    congress INTEGER NOT NULL,
    law_number VARCHAR(20) NOT NULL,
    law_type VARCHAR(20) NOT NULL, -- public, private
    title TEXT,
    effective_date DATE,
    enacted_date DATE,
    president VARCHAR(255), -- who signed it
    metadata JSONB, -- full law metadata
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Federal Law Sections Table
CREATE TABLE IF NOT EXISTS master.federal_law_sections (
    id BIGSERIAL PRIMARY KEY,
    law_id BIGINT NOT NULL REFERENCES master.federal_laws(id) ON DELETE CASCADE,
    section_number VARCHAR(20),
    section_title VARCHAR(500),
    content TEXT,
    section_order INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Federal Reports Table
CREATE TABLE IF NOT EXISTS master.federal_reports (
    id BIGSERIAL PRIMARY KEY,
    report_id VARCHAR(50) UNIQUE NOT NULL, -- e.g., "HRPT-1"
    congress INTEGER NOT NULL,
    report_number VARCHAR(20) NOT NULL,
    report_type VARCHAR(20) NOT NULL, -- house, senate
    title TEXT,
    committee VARCHAR(255),
    report_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Federal Congressional Record Table
CREATE TABLE IF NOT EXISTS master.federal_congressional_records (
    id BIGSERIAL PRIMARY KEY,
    record_id VARCHAR(50) UNIQUE NOT NULL, -- e.g., "CREC-2025-01-03"
    date DATE NOT NULL,
    volume INTEGER,
    part INTEGER, -- part 1, part 2, etc.
    chamber VARCHAR(20),
    record_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Federal Hearings Table
CREATE TABLE IF NOT EXISTS master.federal_hearings (
    id BIGSERIAL PRIMARY KEY,
    hearing_id VARCHAR(50) UNIQUE NOT NULL, -- e.g., "CHRG-119hhrg12345"
    congress INTEGER NOT NULL,
    committee VARCHAR(255),
    subcommittee VARCHAR(255),
    hearing_date DATE,
    title TEXT,
    location TEXT,
    hearing_text TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Federal Register Table
CREATE TABLE IF NOT EXISTS master.federal_register (
    id BIGSERIAL PRIMARY KEY,
    doc_number VARCHAR(50) UNIQUE NOT NULL, -- e.g., "2025-01-01;R1"
    publication_date DATE NOT NULL,
    agency VARCHAR(255),
    document_type VARCHAR(50), -- rule, notice, proposed rule, etc.
    title TEXT,
    abstract TEXT,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Federal Social Media Posts Table
CREATE TABLE IF NOT EXISTS master.federal_social_media_posts (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT REFERENCES master.federal_members(id) ON DELETE CASCADE,
    platform VARCHAR(20) NOT NULL,
    post_id VARCHAR(100) NOT NULL,
    content TEXT,
    posted_at TIMESTAMP NOT NULL,
    url VARCHAR(500),
    engagement_metrics JSONB, -- likes, retweets, shares, etc.
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
    topics TEXT[],
    hashtags TEXT[],
    mentions TEXT[],
    media_urls TEXT[],
    is_reply BOOLEAN DEFAULT false,
    reply_to_id VARCHAR(100),
    is_retweet BOOLEAN DEFAULT false,
    retweet_of_id VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, post_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_federal_members_chamber ON master.federal_members(chamber);
CREATE INDEX IF NOT EXISTS idx_federal_members_state ON master.federal_members(state);
CREATE INDEX IF NOT EXISTS idx_federal_members_party ON master.federal_members(party);
CREATE INDEX IF NOT EXISTS idx_federal_members_current ON master.federal_members(current_member);
CREATE INDEX IF NOT EXISTS idx_federal_members_bioguide ON master.federal_members(bioguide_id);

CREATE INDEX IF NOT EXISTS idx_federal_member_terms_member ON master.federal_member_terms(member_id);
CREATE INDEX IF NOT EXISTS idx_federal_member_terms_congress ON master.federal_member_terms(congress);
CREATE INDEX IF NOT EXISTS idx_federal_member_terms_active ON master.federal_member_terms(start_year, end_year);

CREATE INDEX IF NOT EXISTS idx_federal_member_committees_member ON master.federal_member_committees(member_id);
CREATE INDEX IF NOT EXISTS idx_federal_member_committees_committee ON master.federal_member_committees(committee_name);
CREATE INDEX IF NOT EXISTS idx_federal_member_committees_active ON master.federal_member_committees(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_federal_member_social_member ON master.federal_member_social_media(member_id);
CREATE INDEX IF NOT EXISTS idx_federal_member_social_platform ON master.federal_member_social_media(platform);
CREATE INDEX IF NOT EXISTS idx_federal_member_social_updated ON master.federal_member_social_media(last_updated);

CREATE INDEX IF NOT EXISTS idx_federal_committees_chamber ON master.federal_committees(chamber);
CREATE INDEX IF NOT EXISTS idx_federal_committees_current ON master.federal_committees(current_committee);

CREATE INDEX IF NOT EXISTS idx_federal_committee_members_committee ON master.federal_committee_members(committee_id);
CREATE INDEX IF NOT EXISTS idx_federal_committee_members_member ON master.federal_committee_members(member_id);

CREATE INDEX IF NOT EXISTS idx_federal_laws_congress ON master.federal_laws(congress);
CREATE INDEX IF NOT EXISTS idx_federal_laws_law_id ON master.federal_laws(law_id);

CREATE INDEX IF NOT EXISTS idx_federal_law_sections_law ON master.federal_law_sections(law_id);
CREATE INDEX IF NOT EXISTS idx_federal_law_sections_order ON master.federal_law_sections(section_order);

CREATE INDEX IF NOT EXISTS idx_federal_reports_congress ON master.federal_reports(congress);
CREATE INDEX IF NOT EXISTS idx_federal_reports_report_id ON master.federal_reports(report_id);

CREATE INDEX IF NOT EXISTS idx_federal_records_date ON master.federal_congressional_records(date);
CREATE INDEX IF NOT EXISTS idx_federal_records_record_id ON master.federal_congressional_records(record_id);

CREATE INDEX IF NOT EXISTS idx_federal_hearings_congress ON master.federal_hearings(congress);
CREATE INDEX IF NOT EXISTS idx_federal_hearings_date ON master.federal_hearings(hearing_date);

CREATE INDEX IF NOT EXISTS idx_federal_register_date ON master.federal_register(publication_date);
CREATE INDEX IF NOT EXISTS idx_federal_register_agency ON master.federal_register(agency);
CREATE INDEX IF NOT EXISTS idx_federal_register_type ON master.federal_register(document_type);

CREATE INDEX IF NOT EXISTS idx_federal_social_posts_member ON master.federal_social_media_posts(member_id);
CREATE INDEX IF NOT EXISTS idx_federal_social_posts_platform ON master.federal_social_media_posts(platform);
CREATE INDEX IF NOT EXISTS idx_federal_social_posts_date ON master.federal_social_media_posts(posted_at);
CREATE INDEX IF NOT EXISTS idx_federal_social_posts_sentiment ON master.federal_social_media_posts(sentiment_score);
CREATE INDEX IF NOT EXISTS idx_federal_social_posts_topics ON master.federal_social_media_posts USING GIN(topics);

-- Comments for documentation
COMMENT ON TABLE master.federal_members IS 'Federal legislators (Senators and Representatives) with biographical and political information';
COMMENT ON TABLE master.federal_member_terms IS 'Terms served by federal legislators';
COMMENT ON TABLE master.federal_member_committees IS 'Committee assignments for federal legislators';
COMMENT ON TABLE master.federal_member_social_media IS 'Social media accounts for federal legislators';
COMMENT ON TABLE master.federal_committees IS 'Federal committees and subcommittees';
COMMENT ON TABLE master.federal_committee_members IS 'Members of federal committees';
COMMENT ON TABLE master.federal_laws IS 'Federal laws and statutes';
COMMENT ON TABLE master.federal_law_sections IS 'Sections within federal laws';
COMMENT ON TABLE master.federal_reports IS 'Committee reports on federal legislation';
COMMENT ON TABLE master.federal_congressional_records IS 'Daily congressional record entries';
COMMENT ON TABLE master.federal_hearings IS 'Federal committee hearings and testimonies';
COMMENT ON TABLE master.federal_register IS 'Federal Register documents (rules, notices, etc.)';
COMMENT ON TABLE master.federal_social_media_posts IS 'Social media posts from federal legislators with analytics';