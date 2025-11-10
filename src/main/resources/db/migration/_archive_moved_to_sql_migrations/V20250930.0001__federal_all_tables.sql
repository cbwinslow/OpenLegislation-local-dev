-- V20250930.0001__federal_all_tables.sql
-- Comprehensive Federal Tables Migration for All Congress.gov Data Types
-- Creates tables for bills (incl. amendments/resolutions as subtypes), members, committees, hearings, records,
-- federal register, laws, nominations, treaties. Uses JPA-style schema from existing Java models (FederalBill,
-- FederalMember, etc.). Idempotent: IF NOT EXISTS. Indexes for performance (congress, source_url UNIQUE).
-- Foreign keys for integrity (e.g., amendments to bills). JSONB for flexible metadata. Partition-ready by congress.
-- Run via Flyway: mvn flyway:migrate. Verify: psql -d openleg -c "\dt federal_*"

-- Base federal_documents table (common fields for all types)
CREATE TABLE IF NOT EXISTS federal_documents (
    id BIGSERIAL PRIMARY KEY,
    source_url VARCHAR(500) UNIQUE NOT NULL,  -- Idempotency key from API
    congress INTEGER NOT NULL,
    document_type VARCHAR(50) NOT NULL,  -- bill, amendment, resolution, member, committee, hearing, record, register, law, nomination, treaty
    title TEXT,
    summary TEXT,
    date_local TIMESTAMP,
    metadata JSONB,  -- Raw API payload + extras
    full_text TEXT,
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for base table
CREATE INDEX IF NOT EXISTS idx_federal_documents_congress ON federal_documents(congress);
CREATE INDEX IF NOT EXISTS idx_federal_documents_type ON federal_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_federal_documents_source_url ON federal_documents(source_url);
CREATE INDEX IF NOT EXISTS idx_federal_documents_date ON federal_documents(date_local);

-- Bills/Amendments/Resolutions (subtype of federal_documents; amends FK to self for amendments)
CREATE TABLE IF NOT EXISTS federal_bills (
    id BIGINT PRIMARY KEY REFERENCES federal_documents(id) ON DELETE CASCADE,
    print_no VARCHAR(50) NOT NULL,
    session_year INTEGER NOT NULL,
    bill_type VARCHAR(10),  -- hr, s, hres, sres, etc.
    number INTEGER,
    sponsor VARCHAR(200),
    status VARCHAR(50),
    introduced_date TIMESTAMP,
    last_action_date TIMESTAMP,
    amends_source_url VARCHAR(500) REFERENCES federal_documents(source_url),  -- For amendments
    amendment_number INTEGER,
    UNIQUE(congress, print_no, session_year)  -- Composite for bills/resols
);

-- Indexes for bills
CREATE INDEX IF NOT EXISTS idx_federal_bills_congress_printno ON federal_bills(print_no, session_year);
CREATE INDEX IF NOT EXISTS idx_federal_bills_sponsor ON federal_bills(sponsor);
CREATE INDEX IF NOT EXISTS idx_federal_bills_status ON federal_bills(status);
CREATE INDEX IF NOT EXISTS idx_federal_bills_amends ON federal_bills(amends_source_url);

-- Members
CREATE TABLE IF NOT EXISTS federal_members (
    id BIGSERIAL PRIMARY KEY,
    bioguide_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    party VARCHAR(10),
    state VARCHAR(2),
    chamber VARCHAR(10),  -- house, senate, joint
    current_member BOOLEAN DEFAULT FALSE,
    terms JSONB,  -- Array of term objects
    committees JSONB,  -- Array of committee assignments
    social_media JSONB,  -- {twitter: handle, facebook: id, etc.}
    source_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for members
CREATE INDEX IF NOT EXISTS idx_federal_members_bioguide ON federal_members(bioguide_id);
CREATE INDEX IF NOT EXISTS idx_federal_members_state ON federal_members(state);
CREATE INDEX IF NOT EXISTS idx_federal_members_chamber ON federal_members(chamber);
CREATE INDEX IF NOT EXISTS idx_federal_members_party ON federal_members(party);

-- Committees
CREATE TABLE IF NOT EXISTS federal_committees (
    id BIGSERIAL PRIMARY KEY,
    committee_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    chamber VARCHAR(10),  -- house, senate, joint
    type VARCHAR(50),  -- standing, select, joint
    jurisdiction TEXT,
    members JSONB,  -- Array of {name, role, party}
    source_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for committees
CREATE INDEX IF NOT EXISTS idx_federal_committees_code ON federal_committees(committee_code);
CREATE INDEX IF NOT EXISTS idx_federal_committees_chamber ON federal_committees(chamber);

-- Hearings
CREATE TABLE IF NOT EXISTS federal_hearings (
    id BIGSERIAL PRIMARY KEY,
    hearing_id VARCHAR(100) UNIQUE NOT NULL,
    congress INTEGER NOT NULL,
    committee_code VARCHAR(50) REFERENCES federal_committees(committee_code),
    date TIMESTAMP NOT NULL,
    location VARCHAR(200),
    witnesses JSONB,  -- Array of {name, title, testimony}
    summary TEXT,
    source_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for hearings
CREATE INDEX IF NOT EXISTS idx_federal_hearings_congress ON federal_hearings(congress);
CREATE INDEX IF NOT EXISTS idx_federal_hearings_date ON federal_hearings(date);
CREATE INDEX IF NOT EXISTS idx_federal_hearings_committee ON federal_hearings(committee_code);

-- Congressional Records
CREATE TABLE IF NOT EXISTS federal_records (
    id BIGSERIAL PRIMARY KEY,
    record_id VARCHAR(100) UNIQUE NOT NULL,
    congress INTEGER NOT NULL,
    date DATE NOT NULL,
    chamber VARCHAR(10),
    speakers JSONB,  -- Array of {name, party, state, text}
    text TEXT,
    source_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for records
CREATE INDEX IF NOT EXISTS idx_federal_records_congress_date ON federal_records(congress, date);
CREATE INDEX IF NOT EXISTS idx_federal_records_chamber ON federal_records(chamber);

-- Federal Register Documents
CREATE TABLE IF NOT EXISTS federal_register_docs (
    id BIGSERIAL PRIMARY KEY,
    docket_id VARCHAR(100) UNIQUE NOT NULL,
    congress INTEGER,
    agencies JSONB,  -- Array of {name, type}
    publication_date DATE,
    text TEXT,
    source_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for register
CREATE INDEX IF NOT EXISTS idx_federal_register_docket ON federal_register_docs(docket_id);
CREATE INDEX IF NOT EXISTS idx_federal_register_date ON federal_register_docs(publication_date);

-- Laws
CREATE TABLE IF NOT EXISTS federal_laws (
    id BIGSERIAL PRIMARY KEY,
    public_law_number VARCHAR(50) UNIQUE NOT NULL,
    congress INTEGER NOT NULL,
    sections JSONB,  -- Array of {number, title, text}
    enacted_date DATE,
    source_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for laws
CREATE INDEX IF NOT EXISTS idx_federal_laws_congress ON federal_laws(congress);
CREATE INDEX IF NOT EXISTS idx_federal_laws_enacted ON federal_laws(enacted_date);

-- Nominations
CREATE TABLE IF NOT EXISTS federal_nominations (
    id BIGSERIAL PRIMARY KEY,
    nomination_number VARCHAR(50) UNIQUE NOT NULL,
    congress INTEGER NOT NULL,
    nominee_name VARCHAR(200),
    position VARCHAR(200),
    status VARCHAR(50),
    committee VARCHAR(100),
    source_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for nominations
CREATE INDEX IF NOT EXISTS idx_federal_nominations_congress ON federal_nominations(congress);
CREATE INDEX IF NOT EXISTS idx_federal_nominations_status ON federal_nominations(status);

-- Treaties
CREATE TABLE IF NOT EXISTS federal_treaties (
    id BIGSERIAL PRIMARY KEY,
    treaty_doc_number VARCHAR(50) UNIQUE NOT NULL,
    congress INTEGER NOT NULL,
    title TEXT,
    status VARCHAR(50),
    signatories JSONB,  -- Array of {country, date, representative}
    source_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'federal',
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for treaties
CREATE INDEX IF NOT EXISTS idx_federal_treaties_congress ON federal_treaties(congress);
CREATE INDEX IF NOT EXISTS idx_federal_treaties_status ON federal_treaties(status);

-- Audit log for all federal ingestions (for traceability)
CREATE TABLE IF NOT EXISTS federal_ingestion_audit (
    id BIGSERIAL PRIMARY KEY,
    endpoint VARCHAR(50) NOT NULL,
    congress INTEGER NOT NULL,
    batch_offset INTEGER,
    records_processed INTEGER,
    errors INTEGER DEFAULT 0,
    status VARCHAR(20),  -- pending, completed, failed
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- Indexes for audit
CREATE INDEX IF NOT EXISTS idx_federal_audit_endpoint_congress ON federal_ingestion_audit(endpoint, congress);
CREATE INDEX IF NOT EXISTS idx_federal_audit_timestamp ON federal_ingestion_audit(run_timestamp);

-- Comments for documentation
COMMENT ON TABLE federal_documents IS 'Base table for all federal Congress.gov documents (polymorphic)';
COMMENT ON COLUMN federal_documents.document_type IS 'Discriminator for subtypes: bill, member, hearing, etc.';
COMMENT ON TABLE federal_bills IS 'Bills, amendments, resolutions (amendments link to parent bills)';
COMMENT ON COLUMN federal_bills.amends_source_url IS 'FK to parent bill source_url for amendments';
COMMENT ON TABLE federal_members IS 'Federal legislators with terms, committees, social media';
COMMENT ON TABLE federal_committees IS 'Committees with member assignments';
COMMENT ON TABLE federal_hearings IS 'Public hearings with witnesses';
COMMENT ON TABLE federal_records IS 'Daily congressional records/proceedings';
COMMENT ON TABLE federal_register_docs IS 'Federal Register agency documents';
COMMENT ON TABLE federal_laws IS 'Enacted public laws with sections';
COMMENT ON TABLE federal_nominations IS 'Executive nominations';
COMMENT ON TABLE federal_treaties IS 'International treaties';
COMMENT ON TABLE federal_ingestion_audit IS 'Audit trail for ingestion runs';

-- Verify migration (run after to check)
-- SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'federal_%' ORDER BY table_name;