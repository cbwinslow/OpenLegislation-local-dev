-- OpenLegislation Database Schema for PostgreSQL
-- Database: opendiscourse
-- Host: 100.90.23.60
-- Port: 5432
-- User: opendiscourse
-- Password: opendiscourse123

-- Create database if it doesn't exist
-- CREATE DATABASE opendiscourse;

-- Connect to the database
-- \c opendiscourse;

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ===========================================
-- TELEMETRY AND AUDIT TABLES
-- ===========================================

-- Telemetry events table
CREATE TABLE IF NOT EXISTS telemetry_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    source VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    function_name VARCHAR(200) NOT NULL,
    execution_time DECIMAL(10,4),
    success BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Feature flags table
CREATE TABLE IF NOT EXISTS feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flag_name VARCHAR(100) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Queue system tables
CREATE TABLE IF NOT EXISTS job_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(100) NOT NULL,
    job_data JSONB,
    priority INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- ===========================================
-- LEGISLATIVE DATA TABLES
-- ===========================================

-- Bills table
CREATE TABLE IF NOT EXISTS bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(20) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    active_version VARCHAR(50),
    data_source VARCHAR(50) DEFAULT 'federal',
    congress INTEGER,
    bill_type VARCHAR(10),
    sponsor_party VARCHAR(20),
    sponsor_state VARCHAR(10),
    status VARCHAR(100),
    status_date DATE,
    short_title TEXT,
    ldblurb TEXT,
    federal_congress INTEGER,
    federal_source VARCHAR(100),
    session_year INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(bill_print_no, bill_session_year)
);

-- Bill sponsors table
CREATE TABLE IF NOT EXISTS bill_sponsors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(20) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    session_member_id UUID,
    budget_bill BOOLEAN DEFAULT FALSE,
    rules_sponsor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bill_print_no, bill_session_year) REFERENCES bills(bill_print_no, bill_session_year) ON DELETE CASCADE,
    UNIQUE(bill_print_no, bill_session_year, session_member_id)
);

-- Bill actions table
CREATE TABLE IF NOT EXISTS bill_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(20) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    bill_amend_version VARCHAR(50),
    effect_date DATE,
    text TEXT,
    sequence_no INTEGER,
    chamber VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bill_print_no, bill_session_year) REFERENCES bills(bill_print_no, bill_session_year) ON DELETE CASCADE,
    UNIQUE(bill_print_no, bill_session_year, bill_amend_version, sequence_no)
);

-- Committees table
CREATE TABLE IF NOT EXISTS committees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    committee_id VARCHAR(50),
    current_session INTEGER,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(name, chamber)
);

-- Committee members table
CREATE TABLE IF NOT EXISTS committee_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    majority BOOLEAN DEFAULT FALSE,
    sequence_no INTEGER,
    title VARCHAR(100),
    committee_name VARCHAR(200) NOT NULL,
    version_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    session_year INTEGER,
    session_member_id UUID,
    chamber VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (committee_name, chamber) REFERENCES committees(name, chamber) ON DELETE CASCADE
);

-- Federal members table
CREATE TABLE IF NOT EXISTS federal_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bioguide_id VARCHAR(10) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name TEXT,
    party VARCHAR(20),
    state VARCHAR(10),
    district VARCHAR(10),
    chamber VARCHAR(20),
    active BOOLEAN DEFAULT TRUE,
    congress INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw payload storage for debugging and reprocessing
CREATE TABLE IF NOT EXISTS raw_payloads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ingestion_type VARCHAR(50) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    payload JSONB,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(ingestion_type, record_id)
);

-- ===========================================
-- MISSING LEGISLATIVE DATA TABLES
-- ===========================================

-- Bill amendments table
CREATE TABLE IF NOT EXISTS bill_amendments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(20) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    bill_amend_version VARCHAR(10) NOT NULL,
    sponsor_memo TEXT,
    full_text TEXT,
    law_code TEXT,
    publish_status VARCHAR(50),
    same_as VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(bill_print_no, bill_session_year, bill_amend_version)
);

-- Bill text versions table
CREATE TABLE IF NOT EXISTS bill_texts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(20) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    bill_amend_version VARCHAR(10) NOT NULL,
    text_format VARCHAR(16),  -- 'html', 'plain', 'xml'
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(bill_print_no, bill_session_year, bill_amend_version)
);

-- Bill amendment cosponsors table
CREATE TABLE IF NOT EXISTS bill_amendment_cosponsors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(20) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    bill_amend_version VARCHAR(10) NOT NULL,
    session_member_id UUID,
    is_lead_cosponsor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(bill_print_no, bill_session_year, bill_amend_version, session_member_id)
);

-- Session members table
CREATE TABLE IF NOT EXISTS session_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id VARCHAR(50) NOT NULL,
    session_year INTEGER NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name TEXT,
    party VARCHAR(20),
    state VARCHAR(10),
    district VARCHAR(10),
    chamber VARCHAR(20),
    position VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(member_id, session_year)
);

-- Bill votes table
CREATE TABLE IF NOT EXISTS bill_votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(20) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    vote_date DATE NOT NULL,
    sequence_no INTEGER NOT NULL,
    vote_type VARCHAR(50),
    committee_name VARCHAR(200),
    committee_chamber VARCHAR(20),
    ayes INTEGER DEFAULT 0,
    nays INTEGER DEFAULT 0,
    absent INTEGER DEFAULT 0,
    excused INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(bill_print_no, bill_session_year, vote_date, sequence_no)
);

-- Committee version IDs table
CREATE TABLE IF NOT EXISTS committee_version_ids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(20) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    committee_name VARCHAR(200) NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    version_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- GOVINFO STAGING TABLES
-- ===========================================

-- GovInfo bills staging table
CREATE TABLE IF NOT EXISTS govinfo_bills (
    id SERIAL PRIMARY KEY,
    congress INTEGER NOT NULL,
    bill_number VARCHAR(64) NOT NULL,
    bill_type VARCHAR(8),
    title TEXT,
    introduced_date TIMESTAMP WITH TIME ZONE,
    sponsor_name VARCHAR(255),
    sponsor_party VARCHAR(8),
    sponsor_state VARCHAR(8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(congress, bill_number)
);

-- GovInfo bill texts staging table
CREATE TABLE IF NOT EXISTS govinfo_bill_texts (
    id SERIAL PRIMARY KEY,
    govinfo_bill_id INTEGER NOT NULL REFERENCES govinfo_bills(id) ON DELETE CASCADE,
    version_id VARCHAR(128) NOT NULL,
    text_format VARCHAR(16),  -- 'html' or 'plain'
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- GovInfo bill actions staging table
CREATE TABLE IF NOT EXISTS govinfo_bill_actions (
    id SERIAL PRIMARY KEY,
    govinfo_bill_id INTEGER NOT NULL REFERENCES govinfo_bills(id) ON DELETE CASCADE,
    action_date TIMESTAMP WITH TIME ZONE,
    chamber VARCHAR(16),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- GovInfo bill cosponsors staging table
CREATE TABLE IF NOT EXISTS govinfo_bill_cosponsors (
    id SERIAL PRIMARY KEY,
    govinfo_bill_id INTEGER NOT NULL REFERENCES govinfo_bills(id) ON DELETE CASCADE,
    cosponsor_name VARCHAR(255),
    cosponsor_party VARCHAR(8),
    cosponsor_state VARCHAR(8),
    is_lead_cosponsor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- GovInfo bill committees staging table
CREATE TABLE IF NOT EXISTS govinfo_bill_committees (
    id SERIAL PRIMARY KEY,
    govinfo_bill_id INTEGER NOT NULL REFERENCES govinfo_bills(id) ON DELETE CASCADE,
    committee_name VARCHAR(200),
    committee_chamber VARCHAR(20),
    subcommittee_name VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- GovInfo bill subjects staging table
CREATE TABLE IF NOT EXISTS govinfo_bill_subjects (
    id SERIAL PRIMARY KEY,
    govinfo_bill_id INTEGER NOT NULL REFERENCES govinfo_bills(id) ON DELETE CASCADE,
    subject VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- GovInfo document references staging table
CREATE TABLE IF NOT EXISTS govinfo_doc_refs (
    id SERIAL PRIMARY KEY,
    govinfo_bill_id INTEGER NOT NULL REFERENCES govinfo_bills(id) ON DELETE CASCADE,
    ref_type VARCHAR(50),
    ref_value VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- OPENSTATES API TABLES
-- ===========================================

-- OpenStates bills staging table
CREATE TABLE IF NOT EXISTS openstates_bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state VARCHAR(2) NOT NULL,  -- Two-letter state code
    session VARCHAR(50) NOT NULL,  -- Legislative session
    bill_id VARCHAR(50) NOT NULL,  -- OpenStates bill identifier
    title TEXT,
    classification JSONB,  -- Array of bill types
    subject JSONB,  -- Array of subjects
    abstract TEXT,
    first_action_date DATE,
    latest_action_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(state, session, bill_id)
);

-- OpenStates bill actions staging table
CREATE TABLE IF NOT EXISTS openstates_bill_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    openstates_bill_id UUID NOT NULL REFERENCES openstates_bills(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    description TEXT,
    chamber VARCHAR(20),
    classification JSONB,  -- Array of action types
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OpenStates legislators staging table
CREATE TABLE IF NOT EXISTS openstates_legislators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state VARCHAR(2) NOT NULL,
    legislator_id VARCHAR(50) NOT NULL,  -- OpenStates legislator ID
    name VARCHAR(255),
    party VARCHAR(20),
    chamber VARCHAR(20),
    district VARCHAR(50),
    email VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(state, legislator_id)
);

-- OpenStates committees staging table
CREATE TABLE IF NOT EXISTS openstates_committees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state VARCHAR(2) NOT NULL,
    committee_id VARCHAR(50) NOT NULL,
    name VARCHAR(255),
    chamber VARCHAR(20),
    parent_id VARCHAR(50),  -- Parent committee ID
    members JSONB,  -- Array of member objects
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(state, committee_id)
);

-- ===========================================
-- OPENLEGISLATURE (NY STATE LBDC) TABLES
-- ===========================================

-- NY State Legislature bills staging table
CREATE TABLE IF NOT EXISTS ny_bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    print_no VARCHAR(20) NOT NULL,
    session_year INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    sponsor VARCHAR(255),
    co_sponsors JSONB,  -- Array of co-sponsor names
    status VARCHAR(100),
    committee VARCHAR(255),
    law_code VARCHAR(50),
    law_section VARCHAR(100),
    full_text_url VARCHAR(500),
    amendment_text_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(print_no, session_year)
);

-- NY State Legislature bill actions staging table
CREATE TABLE IF NOT EXISTS ny_bill_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ny_bill_id UUID NOT NULL REFERENCES ny_bills(id) ON DELETE CASCADE,
    date DATE,
    text TEXT,
    chamber VARCHAR(20),
    sequence_no INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- NY State Legislature members staging table
CREATE TABLE IF NOT EXISTS ny_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id VARCHAR(50) NOT NULL,
    session_year INTEGER NOT NULL,
    full_name VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    party VARCHAR(20),
    chamber VARCHAR(20),
    district VARCHAR(10),
    email VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    committees JSONB,  -- Array of committee memberships
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(member_id, session_year)
);

-- NY State Legislature committees staging table
CREATE TABLE IF NOT EXISTS ny_committees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    committee_name VARCHAR(255) NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    session_year INTEGER NOT NULL,
    chair VARCHAR(255),
    members JSONB,  -- Array of member names
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(committee_name, chamber, session_year)
);

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

-- Bills indexes
CREATE INDEX IF NOT EXISTS idx_bills_print_no_session ON bills(bill_print_no, bill_session_year);
CREATE INDEX IF NOT EXISTS idx_bills_congress ON bills(congress);
CREATE INDEX IF NOT EXISTS idx_bills_type ON bills(bill_type);
CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(status);
CREATE INDEX IF NOT EXISTS idx_bills_data_source ON bills(data_source);

-- Bill sponsors indexes
CREATE INDEX IF NOT EXISTS idx_bill_sponsors_bill ON bill_sponsors(bill_print_no, bill_session_year);

-- Bill actions indexes
CREATE INDEX IF NOT EXISTS idx_bill_actions_bill ON bill_actions(bill_print_no, bill_session_year);
CREATE INDEX IF NOT EXISTS idx_bill_actions_date ON bill_actions(effect_date);

-- Committees indexes
CREATE INDEX IF NOT EXISTS idx_committees_name_chamber ON committees(name, chamber);
CREATE INDEX IF NOT EXISTS idx_committees_session ON committees(current_session);

-- Committee members indexes
CREATE INDEX IF NOT EXISTS idx_committee_members_committee ON committee_members(committee_name, chamber);
CREATE INDEX IF NOT EXISTS idx_committee_members_member ON committee_members(session_member_id);

-- Federal members indexes
CREATE INDEX IF NOT EXISTS idx_federal_members_bioguide ON federal_members(bioguide_id);
CREATE INDEX IF NOT EXISTS idx_federal_members_state ON federal_members(state);
CREATE INDEX IF NOT EXISTS idx_federal_members_party ON federal_members(party);
CREATE INDEX IF NOT EXISTS idx_federal_members_chamber ON federal_members(chamber);
CREATE INDEX IF NOT EXISTS idx_federal_members_congress ON federal_members(congress);

-- Telemetry indexes
CREATE INDEX IF NOT EXISTS idx_telemetry_events_type ON telemetry_events(event_type);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_source ON telemetry_events(source);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_timestamp ON telemetry_events(timestamp);

-- Performance metrics indexes
CREATE INDEX IF NOT EXISTS idx_performance_metrics_function ON performance_metrics(function_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);

-- Queue indexes
CREATE INDEX IF NOT EXISTS idx_job_queue_status ON job_queue(status);
CREATE INDEX IF NOT EXISTS idx_job_queue_type ON job_queue(job_type);
CREATE INDEX IF NOT EXISTS idx_job_queue_priority ON job_queue(priority);
CREATE INDEX IF NOT EXISTS idx_job_queue_created ON job_queue(created_at);

-- Raw payloads indexes
CREATE INDEX IF NOT EXISTS idx_raw_payloads_type ON raw_payloads(ingestion_type);
CREATE INDEX IF NOT EXISTS idx_raw_payloads_record ON raw_payloads(record_id);

-- ===========================================
-- FULL TEXT SEARCH INDEXES
-- ===========================================

-- Bills full text search
CREATE INDEX IF NOT EXISTS idx_bills_title_search ON bills USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_bills_summary_search ON bills USING gin(to_tsvector('english', summary));

-- Committees full text search
CREATE INDEX IF NOT EXISTS idx_committees_name_search ON committees USING gin(to_tsvector('english', name));
CREATE INDEX IF NOT EXISTS idx_committees_full_name_search ON committees USING gin(to_tsvector('english', full_name));

-- ===========================================
-- TRIGGERS FOR UPDATED_AT
-- ===========================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to relevant tables
DROP TRIGGER IF EXISTS update_bills_updated_at ON bills;
CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_committees_updated_at ON committees;
CREATE TRIGGER update_committees_updated_at BEFORE UPDATE ON committees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_federal_members_updated_at ON federal_members;
CREATE TRIGGER update_federal_members_updated_at BEFORE UPDATE ON federal_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_job_queue_updated_at ON job_queue;
CREATE TRIGGER update_job_queue_updated_at BEFORE UPDATE ON job_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- VIEWS FOR COMMON QUERIES
-- ===========================================

-- Bills with sponsor info view
CREATE OR REPLACE VIEW bills_with_sponsors AS
SELECT
    b.*,
    fm.full_name as sponsor_name,
    fm.party as sponsor_party,
    fm.state as sponsor_state
FROM bills b
LEFT JOIN bill_sponsors bs ON b.bill_print_no = bs.bill_print_no AND b.bill_session_year = bs.bill_session_year
LEFT JOIN federal_members fm ON bs.session_member_id = fm.id
WHERE bs.rules_sponsor = TRUE OR bs.session_member_id IS NULL;

-- Committee membership view
CREATE OR REPLACE VIEW committee_membership AS
SELECT
    cm.*,
    c.full_name as committee_full_name,
    fm.full_name as member_name,
    fm.party as member_party,
    fm.state as member_state
FROM committee_members cm
JOIN committees c ON cm.committee_name = c.name AND cm.chamber = c.chamber
LEFT JOIN federal_members fm ON cm.session_member_id = fm.id;

-- Recent bills view
CREATE OR REPLACE VIEW recent_bills AS
SELECT * FROM bills
WHERE congress >= 115
ORDER BY congress DESC, bill_print_no DESC;

-- ===========================================
-- INITIAL DATA SETUP
-- ===========================================

-- Insert default feature flags
INSERT INTO feature_flags (flag_name, enabled, metadata) VALUES
    ('federal_bills_ingestion_enabled', true, '{"description": "Enable federal bills ingestion"}'),
    ('federal_committees_ingestion_enabled', true, '{"description": "Enable federal committees ingestion"}'),
    ('federal_members_ingestion_enabled', true, '{"description": "Enable federal members ingestion"}'),
    ('telemetry_enabled', true, '{"description": "Enable telemetry collection"}'),
    ('performance_monitoring_enabled', true, '{"description": "Enable performance monitoring"}'),
    ('gpu_acceleration_enabled', false, '{"description": "Enable GPU acceleration for processing"}'),
    ('parallel_processing_enabled', true, '{"description": "Enable parallel processing"}')
ON CONFLICT (flag_name) DO NOTHING;

-- ===========================================
-- PERMISSIONS AND SECURITY
-- ===========================================

-- Grant permissions to opendiscourse user
-- GRANT ALL PRIVILEGES ON DATABASE opendiscourse TO opendiscourse;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO opendiscourse;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO opendiscourse;

-- ===========================================
-- MONITORING AND MAINTENANCE
-- ===========================================

-- Function to get database statistics
CREATE OR REPLACE FUNCTION get_database_stats()
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT,
    table_size TEXT,
    index_size TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        schemaname || '.' || tablename as table_name,
        n_tup_ins - n_tup_del as row_count,
        pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as table_size,
        pg_size_pretty(pg_indexes_size(schemaname || '.' || tablename)) as index_size
    FROM pg_stat_user_tables
    WHERE schemaname = 'public'
    ORDER BY row_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old telemetry data (keep last 30 days)
CREATE OR REPLACE FUNCTION clean_old_telemetry()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM telemetry_events
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old performance metrics (keep last 30 days)
CREATE OR REPLACE FUNCTION clean_old_performance_metrics()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM performance_metrics
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- DATA INTEGRITY CONSTRAINTS
-- ===========================================

-- Ensure congress numbers are valid
ALTER TABLE bills ADD CONSTRAINT check_congress_range
    CHECK (congress >= 1 AND congress <= 200);

ALTER TABLE committees ADD CONSTRAINT check_committee_session_range
    CHECK (current_session >= 1 AND current_session <= 200);

ALTER TABLE federal_members ADD CONSTRAINT check_member_congress_range
    CHECK (congress >= 1 AND congress <= 200);

-- Ensure bill types are valid
ALTER TABLE bills ADD CONSTRAINT check_bill_type_valid
    CHECK (bill_type IN ('HR', 'S', 'HJRES', 'SJRES', 'HCONRES', 'SCONRES', 'HRES', 'SRES'));

-- ===========================================
-- PARTITIONING SETUP (FOR LARGE TABLES)
-- ===========================================

-- Note: Partitioning can be added later for very large tables
-- Example for bills table by congress:
-- CREATE TABLE bills_y2023 PARTITION OF bills FOR VALUES FROM (118) TO (119);
-- CREATE TABLE bills_y2025 PARTITION OF bills FOR VALUES FROM (119) TO (120);

-- ===========================================
-- FINAL SETUP COMPLETE
-- ===========================================

-- Log schema creation
DO $$
BEGIN
    RAISE NOTICE 'OpenLegislation database schema created successfully';
    RAISE NOTICE 'Database: opendiscourse on 100.90.23.60:5432';
    RAISE NOTICE 'Tables created: %', (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public');
    RAISE NOTICE 'Indexes created: %', (SELECT count(*) FROM pg_indexes WHERE schemaname = 'public');
END $$;
