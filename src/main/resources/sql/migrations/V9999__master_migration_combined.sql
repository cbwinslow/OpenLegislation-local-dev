-- ============================================================================
-- OpenLegislation Master Migration Script
-- ============================================================================
-- This script combines all individual migration files into a single comprehensive
-- migration for the OpenLegislation database schema.
-- 
-- Generated: $(date)
-- Total migrations: $(find src/main/resources/sql/migrations/ -name "V*.sql" | wc -l)
-- ============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- CORE SCHEMA AND TABLES (from V1__openleg.db-init.sql)
-- ============================================================================

-- Create master schema
CREATE SCHEMA IF NOT EXISTS master;

-- Create core tables
CREATE TABLE IF NOT EXISTS master.bill (
    bill_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_print_no VARCHAR(50) NOT NULL,
    bill_session_year INTEGER NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    title TEXT,
    summary TEXT,
    active_version VARCHAR(10),
    status VARCHAR(50),
    sponsor_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS master.person (
    person_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(200),
    email VARCHAR(200),
    img_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS master.member (
    member_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES master.person(person_id),
    chamber VARCHAR(20) NOT NULL,
    district_code INTEGER,
    incumbent BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ENHANCED SCHEMA FOR FEDERAL DATA (from V20250921.0004__federal_member_schema.sql)
-- ============================================================================

-- Federal person table
CREATE TABLE IF NOT EXISTS master.federal_person (
    person_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bioguide_id VARCHAR(20) UNIQUE,
    thomas_id VARCHAR(20),
    lis_id VARCHAR(20),
    govtrack_id INTEGER,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    middle_name VARCHAR(100),
    suffix VARCHAR(20),
    nickname VARCHAR(100),
    party VARCHAR(50),
    state VARCHAR(2),
    district VARCHAR(10),
    chamber VARCHAR(20),
    term_start DATE,
    term_end DATE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Federal member offices
CREATE TABLE IF NOT EXISTS master.federal_member_office (
    office_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES master.federal_person(person_id),
    office_type VARCHAR(50), -- 'district', 'senate', 'leadership'
    city VARCHAR(100),
    state VARCHAR(2),
    zip VARCHAR(10),
    phone VARCHAR(20),
    fax VARCHAR(20),
    building VARCHAR(100),
    room VARCHAR(50),
    address TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INGESTION TRACKING (from V20250921.0006__generic_ingestion_tracking.sql)
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.ingestion_status (
    status_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id VARCHAR(100) NOT NULL,
    table_name VARCHAR(200) NOT NULL,
    record_id VARCHAR(200),
    status VARCHAR(20) NOT NULL, -- 'pending', 'in_progress', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DOCUMENT STORAGE (from V20250921.0001__add_source_documents_table.sql)
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.source_document (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL, -- 'govinfo', 'congress_api', 'ny_openleg'
    source_id VARCHAR(200) NOT NULL,
    document_type VARCHAR(50), -- 'bill', 'agenda', 'calendar', 'vote'
    title TEXT,
    content TEXT,
    metadata JSONB,
    file_path VARCHAR(500),
    checksum VARCHAR(64),
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AGENDA AND CALENDAR TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.agenda (
    agenda_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agenda_number INTEGER,
    session_year INTEGER,
    chamber VARCHAR(20),
    meeting_date DATE,
    meeting_time TIME,
    location TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS master.calendar (
    calendar_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    calendar_number INTEGER,
    session_year INTEGER,
    chamber VARCHAR(20),
    calendar_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- VOTE AND AMENDMENT TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.bill_amendment (
    amendment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID REFERENCES master.bill(bill_id),
    amendment_print_no VARCHAR(50),
    amendment_session_year INTEGER,
    content TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS master.bill_amendment_vote_info (
    vote_info_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    amendment_id UUID REFERENCES master.bill_amendment(amendment_id),
    vote_date DATE,
    vote_type VARCHAR(50),
    ayes INTEGER,
    nays INTEGER,
    absences INTEGER,
    excused INTEGER,
    result VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- BILL MILESTONE AND STATUS TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.bill_milestone (
    milestone_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID REFERENCES master.bill(bill_id),
    milestone_type VARCHAR(50), -- 'introduced', 'passed_senate', 'passed_assembly', 'signed'
    milestone_date DATE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- EMBEDDINGS AND VECTOR SEARCH
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.bill_embedding (
    embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bill_id UUID REFERENCES master.bill(bill_id),
    bill_print_no VARCHAR(50),
    bill_session_year INTEGER,
    embedding vector(1536),
    embedding_metadata JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUDIT LOGGING (from V20250924.193408__audit_logging.sql)
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    operation VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    old_values JSONB,
    new_values JSONB,
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET
);

-- ============================================================================
-- DOCUMENTS TABLE (from V20250925.0004__create_documents_table.sql)
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT,
    document_type VARCHAR(50),
    source VARCHAR(100),
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TRANSCRIPTS (from V2025.09.27__add_transcript.sql)
-- ============================================================================

CREATE TABLE IF NOT EXISTS master.transcript (
    transcript_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100),
    transcript_date DATE,
    transcript_type VARCHAR(50),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Bill indexes
CREATE INDEX IF NOT EXISTS idx_bill_print_no_session ON master.bill(bill_print_no, bill_session_year);
CREATE INDEX IF NOT EXISTS idx_bill_chamber_session ON master.bill(chamber, bill_session_year);
CREATE INDEX IF NOT EXISTS idx_bill_status ON master.bill(status);
CREATE INDEX IF NOT EXISTS idx_bill_updated_at ON master.bill(updated_at);

-- Person and member indexes
CREATE INDEX IF NOT EXISTS idx_person_full_name ON master.person(full_name);
CREATE INDEX IF NOT EXISTS idx_member_chamber_district ON master.member(chamber, district_code);
CREATE INDEX IF NOT EXISTS idx_member_incumbent ON master.member(incumbent);

-- Federal person indexes
CREATE INDEX IF NOT EXISTS idx_federal_person_bioguide ON master.federal_person(bioguide_id);
CREATE INDEX IF NOT EXISTS idx_federal_person_state_chamber ON master.federal_person(state, chamber);
CREATE INDEX IF NOT EXISTS idx_federal_person_active ON master.federal_person(active);

-- Ingestion status indexes
CREATE INDEX IF NOT EXISTS idx_ingestion_status_source ON master.ingestion_status(source_id, status);
CREATE INDEX IF NOT EXISTS idx_ingestion_status_table ON master.ingestion_status(table_name, status);
CREATE INDEX IF NOT EXISTS idx_ingestion_status_created ON master.ingestion_status(created_at);

-- Source document indexes
CREATE INDEX IF NOT EXISTS idx_source_document_source ON master.source_document(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_source_document_type ON master.source_document(document_type);
CREATE INDEX IF NOT EXISTS idx_source_document_processed ON master.source_document(processed);
CREATE INDEX IF NOT EXISTS idx_source_document_checksum ON master.source_document(checksum);

-- Agenda and calendar indexes
CREATE INDEX IF NOT EXISTS idx_agenda_session_date ON master.agenda(session_year, meeting_date);
CREATE INDEX IF NOT EXISTS idx_calendar_session_date ON master.calendar(session_year, calendar_date);

-- Vote indexes
CREATE INDEX IF NOT EXISTS idx_amendment_bill ON master.bill_amendment(bill_id);
CREATE INDEX IF NOT EXISTS idx_vote_info_amendment ON master.bill_amendment_vote_info(amendment_id);
CREATE INDEX IF NOT EXISTS idx_vote_date ON master.bill_amendment_vote_info(vote_date);

-- Milestone indexes
CREATE INDEX IF NOT EXISTS idx_milestone_bill ON master.bill_milestone(bill_id);
CREATE INDEX IF NOT EXISTS idx_milestone_type_date ON master.bill_milestone(milestone_type, milestone_date);

-- Embedding indexes
CREATE INDEX IF NOT EXISTS idx_embedding_bill ON master.bill_embedding(bill_id);
CREATE INDEX IF NOT EXISTS idx_embedding_print_session ON master.bill_embedding(bill_print_no, bill_session_year);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_table_record ON master.audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON master.audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_operation ON master.audit_log(operation);

-- Document indexes
CREATE INDEX IF NOT EXISTS idx_documents_type ON master.documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_source ON master.documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_created ON master.documents(created_at);

-- Transcript indexes
CREATE INDEX IF NOT EXISTS idx_transcript_date ON master.transcript(transcript_date);
CREATE INDEX IF NOT EXISTS idx_transcript_type ON master.transcript(transcript_type);
CREATE INDEX IF NOT EXISTS idx_transcript_session ON master.transcript(session_id);

-- ============================================================================
-- TRIGGERS AND FUNCTIONS
-- ============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION master.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_bill_updated_at BEFORE UPDATE ON master.bill
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_person_updated_at BEFORE UPDATE ON master.person
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_member_updated_at BEFORE UPDATE ON master.member
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_federal_person_updated_at BEFORE UPDATE ON master.federal_person
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_federal_member_office_updated_at BEFORE UPDATE ON master.federal_member_office
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_ingestion_status_updated_at BEFORE UPDATE ON master.ingestion_status
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_source_document_updated_at BEFORE UPDATE ON master.source_document
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_agenda_updated_at BEFORE UPDATE ON master.agenda
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_calendar_updated_at BEFORE UPDATE ON master.calendar
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_amendment_updated_at BEFORE UPDATE ON master.bill_amendment
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_vote_info_updated_at BEFORE UPDATE ON master.bill_amendment_vote_info
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_milestone_updated_at BEFORE UPDATE ON master.bill_milestone
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_embedding_updated_at BEFORE UPDATE ON master.bill_embedding
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON master.documents
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_transcript_updated_at BEFORE UPDATE ON master.transcript
    FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES (from V20250925.0003__views_plsql.sql)
-- ============================================================================

-- Active bills view
CREATE OR REPLACE VIEW master.active_bills AS
SELECT 
    b.bill_id,
    b.bill_print_no,
    b.bill_session_year,
    b.chamber,
    b.title,
    b.summary,
    b.status,
    p.full_name as sponsor_name,
    b.updated_at
FROM master.bill b
LEFT JOIN master.member m ON b.sponsor_id = m.member_id
LEFT JOIN master.person p ON m.person_id = p.person_id
WHERE b.status NOT IN ('withdrawn', 'rejected');

-- Federal members view
CREATE OR REPLACE VIEW master.active_federal_members AS
SELECT 
    fp.person_id,
    fp.bioguide_id,
    fp.first_name,
    fp.last_name,
    fp.party,
    fp.state,
    fp.chamber,
    fp.district,
    fp.term_start,
    fp.term_end
FROM master.federal_person fp
WHERE fp.active = true;

-- Ingestion progress view
CREATE OR REPLACE VIEW master.ingestion_progress AS
SELECT 
    source_id,
    table_name,
    status,
    COUNT(*) as count,
    MIN(started_at) as first_started,
    MAX(completed_at) as last_completed
FROM master.ingestion_status
GROUP BY source_id, table_name, status;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON SCHEMA master IS 'Main schema for OpenLegislation data';

COMMENT ON TABLE master.bill IS 'Legislative bills and resolutions';
COMMENT ON TABLE master.person IS 'People involved in legislation (sponsors, members, etc.)';
COMMENT ON TABLE master.member IS 'Member information with chamber and district details';
COMMENT ON TABLE master.federal_person IS 'Federal legislators (Congress members)';
COMMENT ON TABLE master.federal_member_office IS 'Office locations for federal members';
COMMENT ON TABLE master.ingestion_status IS 'Tracking table for data ingestion progress';
COMMENT ON TABLE master.source_document IS 'Original source documents before processing';
COMMENT ON TABLE master.agenda IS 'Committee meeting agendas';
COMMENT ON TABLE master.calendar IS 'Legislative calendars and active lists';
COMMENT ON TABLE master.bill_amendment IS 'Amendments to bills';
COMMENT ON TABLE master.bill_amendment_vote_info IS 'Vote information for amendments';
COMMENT ON TABLE master.bill_milestone IS 'Milestones in bill lifecycle';
COMMENT ON TABLE master.bill_embedding IS 'Vector embeddings for bill search';
COMMENT ON TABLE master.audit_log IS 'Audit trail for all data changes';
COMMENT ON TABLE master.documents IS 'General document storage with embeddings';
COMMENT ON TABLE master.transcript IS 'Legislative session transcripts';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'OpenLegislation Master Migration completed successfully!';
    RAISE NOTICE 'Schema: master created with all tables, indexes, and views';
    RAISE NOTICE 'Total tables created: %', (
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'master'
    );
END $$;