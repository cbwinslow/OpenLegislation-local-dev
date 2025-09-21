-- Migration: Create expanded govinfo bill tables for congress.gov bulk data ingestion
-- Based on govinfo-119-mapping-detailed.md

-- Main govinfo bill table
CREATE TABLE IF NOT EXISTS govinfo_bill (
    id BIGSERIAL PRIMARY KEY,
    congress INTEGER NOT NULL,
    bill_number VARCHAR(64) NOT NULL,
    bill_type VARCHAR(8),
    document_number VARCHAR(64),
    package_number VARCHAR(64),
    title TEXT,
    short_title TEXT,
    introduced_date TIMESTAMP,
    latest_action_date TIMESTAMP,
    sponsor_name VARCHAR(255),
    sponsor_party VARCHAR(8),
    sponsor_state VARCHAR(8),
    sponsor_district VARCHAR(8),
    created_at TIMESTAMP DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_govinfo_bill_congress_number ON govinfo_bill(congress, bill_number);

-- Cosponsors table
CREATE TABLE IF NOT EXISTS govinfo_bill_cosponsor (
    id BIGSERIAL PRIMARY KEY,
    govinfo_bill_id BIGINT NOT NULL REFERENCES govinfo_bill(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    party VARCHAR(8),
    state VARCHAR(8),
    district VARCHAR(8),
    sponsor_type VARCHAR(16),
    date_added TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_govinfo_bill_cosponsor_billid ON govinfo_bill_cosponsor(govinfo_bill_id);

-- Actions table
CREATE TABLE IF NOT EXISTS govinfo_bill_action (
    id BIGSERIAL PRIMARY KEY,
    govinfo_bill_id BIGINT NOT NULL REFERENCES govinfo_bill(id) ON DELETE CASCADE,
    action_date TIMESTAMP,
    chamber VARCHAR(16),
    description TEXT,
    action_type VARCHAR(64),
    sequence_no INTEGER,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_govinfo_bill_action_billid ON govinfo_bill_action(govinfo_bill_id);

-- Text versions table
CREATE TABLE IF NOT EXISTS govinfo_bill_text (
    id BIGSERIAL PRIMARY KEY,
    govinfo_bill_id BIGINT NOT NULL REFERENCES govinfo_bill(id) ON DELETE CASCADE,
    version_id VARCHAR(128) NOT NULL,
    text_format VARCHAR(16), -- 'html' or 'plain'
    content TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_govinfo_bill_text_billid ON govinfo_bill_text(govinfo_bill_id);

-- Committees table
CREATE TABLE IF NOT EXISTS govinfo_bill_committee (
    id BIGSERIAL PRIMARY KEY,
    govinfo_bill_id BIGINT NOT NULL REFERENCES govinfo_bill(id) ON DELETE CASCADE,
    committee_name VARCHAR(255),
    referred_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_govinfo_bill_committee_billid ON govinfo_bill_committee(govinfo_bill_id);

-- Subjects table
CREATE TABLE IF NOT EXISTS govinfo_bill_subject (
    id BIGSERIAL PRIMARY KEY,
    govinfo_bill_id BIGINT NOT NULL REFERENCES govinfo_bill(id) ON DELETE CASCADE,
    subject TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_govinfo_bill_subject_billid ON govinfo_bill_subject(govinfo_bill_id);

-- Document references table
CREATE TABLE IF NOT EXISTS govinfo_doc_refs (
    id BIGSERIAL PRIMARY KEY,
    govinfo_bill_id BIGINT REFERENCES govinfo_bill(id) ON DELETE CASCADE,
    external_id VARCHAR(255),
    rel_type VARCHAR(32),
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_govinfo_doc_refs_billid ON govinfo_doc_refs(govinfo_bill_id);
CREATE INDEX IF NOT EXISTS idx_govinfo_doc_refs_external_id ON govinfo_doc_refs(external_id);