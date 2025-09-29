-- Migration to create federal_bills table for ingesting federal legislation data

CREATE TABLE IF NOT EXISTS federal_bills (
    id BIGSERIAL PRIMARY KEY,
    congress_number INTEGER NOT NULL,
    bill_type VARCHAR(10) NOT NULL,
    number INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    status VARCHAR(50),
    introduced_date TIMESTAMP,
    sponsor_id VARCHAR(50),
    text_content TEXT,
    metadata JSONB,
    source_url VARCHAR(500) UNIQUE NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_federal_bills_congress ON federal_bills(congress_number);
CREATE INDEX IF NOT EXISTS idx_federal_bills_status ON federal_bills(status);
CREATE INDEX IF NOT EXISTS idx_federal_bills_source_url ON federal_bills(source_url);