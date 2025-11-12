-- Migration: Universal Bill Schema for State and Federal Data Integration
-- Extends existing master schema to support congress.gov data
-- Adds data_source column to distinguish state vs federal data

-- Add data_source column to existing bill table
ALTER TABLE master.bill ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'state' CHECK (data_source IN ('state', 'federal'));
ALTER TABLE master.bill ADD COLUMN IF NOT EXISTS congress INTEGER;
ALTER TABLE master.bill ADD COLUMN IF NOT EXISTS bill_type TEXT;
ALTER TABLE master.bill ADD COLUMN IF NOT EXISTS package_number TEXT;
ALTER TABLE master.bill ADD COLUMN IF NOT EXISTS short_title TEXT;
ALTER TABLE master.bill ADD COLUMN IF NOT EXISTS sponsor_party TEXT;
ALTER TABLE master.bill ADD COLUMN IF NOT EXISTS sponsor_state TEXT;
ALTER TABLE master.bill ADD COLUMN IF NOT EXISTS sponsor_district TEXT;

-- Add data_source to bill_amendment table
ALTER TABLE master.bill_amendment ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'state' CHECK (data_source IN ('state', 'federal'));
ALTER TABLE master.bill_amendment ADD COLUMN IF NOT EXISTS version_id TEXT;

-- Add data_source to bill_sponsor table
ALTER TABLE master.bill_sponsor ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'state' CHECK (data_source IN ('state', 'federal'));
ALTER TABLE master.bill_sponsor ADD COLUMN IF NOT EXISTS sponsor_type TEXT DEFAULT 'sponsor' CHECK (sponsor_type IN ('sponsor', 'cosponsor', 'multisponsor'));

-- Add data_source to bill_amendment_cosponsor table
ALTER TABLE master.bill_amendment_cosponsor ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'state' CHECK (data_source IN ('state', 'federal'));
ALTER TABLE master.bill_amendment_cosponsor ADD COLUMN IF NOT EXISTS sponsor_type TEXT DEFAULT 'cosponsor';

-- Add data_source to bill_amendment_multi_sponsor table
ALTER TABLE master.bill_amendment_multi_sponsor ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'state' CHECK (data_source IN ('state', 'federal'));
ALTER TABLE master.bill_amendment_multi_sponsor ADD COLUMN IF NOT EXISTS sponsor_type TEXT DEFAULT 'multisponsor';

-- Add data_source to bill_amendment_action table
ALTER TABLE master.bill_amendment_action ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'state' CHECK (data_source IN ('state', 'federal'));
ALTER TABLE master.bill_amendment_action ADD COLUMN IF NOT EXISTS action_type TEXT;

-- Add data_source to bill_committee table
ALTER TABLE master.bill_committee ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'state' CHECK (data_source IN ('state', 'federal'));

-- Create federal-specific tables for data that doesn't map directly to state schema

-- Federal bill subjects (legislative subjects/tags)
CREATE TABLE IF NOT EXISTS master.federal_bill_subject (
    id BIGSERIAL PRIMARY KEY,
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    subject TEXT NOT NULL,
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    last_fragment_id TEXT,
    FOREIGN KEY (bill_print_no, bill_session_year) REFERENCES master.bill(bill_print_no, bill_session_year) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Federal bill text versions (multiple formats per bill)
CREATE TABLE IF NOT EXISTS master.federal_bill_text (
    id BIGSERIAL PRIMARY KEY,
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    bill_amend_version CHARACTER(1) NOT NULL DEFAULT '',
    version_id TEXT NOT NULL,
    text_format TEXT NOT NULL CHECK (text_format IN ('html', 'xml', 'plain')),
    content TEXT,
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    last_fragment_id TEXT,
    FOREIGN KEY (bill_print_no, bill_session_year, bill_amend_version) REFERENCES master.bill_amendment(bill_print_no, bill_session_year, bill_amend_version) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Federal document references (links to external documents)
CREATE TABLE IF NOT EXISTS master.federal_doc_reference (
    id BIGSERIAL PRIMARY KEY,
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    external_id TEXT NOT NULL,
    rel_type TEXT NOT NULL,
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    last_fragment_id TEXT,
    FOREIGN KEY (bill_print_no, bill_session_year) REFERENCES master.bill(bill_print_no, bill_session_year) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Federal bill relationships (same-as bills, etc.)
CREATE TABLE IF NOT EXISTS master.federal_bill_relationship (
    id BIGSERIAL PRIMARY KEY,
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    related_bill_print_no TEXT NOT NULL,
    related_session_year SMALLINT NOT NULL,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('same_as', 'identical', 'companion', 'related')),
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
    last_fragment_id TEXT,
    FOREIGN KEY (bill_print_no, bill_session_year) REFERENCES master.bill(bill_print_no, bill_session_year) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_bill_data_source ON master.bill(data_source);
CREATE INDEX IF NOT EXISTS idx_bill_congress ON master.bill(congress);
CREATE INDEX IF NOT EXISTS idx_bill_amendment_data_source ON master.bill_amendment(data_source);
CREATE INDEX IF NOT EXISTS idx_bill_sponsor_data_source ON master.bill_sponsor(data_source);
CREATE INDEX IF NOT EXISTS idx_bill_cosponsor_data_source ON master.bill_amendment_cosponsor(data_source);
CREATE INDEX IF NOT EXISTS idx_bill_multi_sponsor_data_source ON master.bill_amendment_multi_sponsor(data_source);
CREATE INDEX IF NOT EXISTS idx_bill_action_data_source ON master.bill_amendment_action(data_source);
CREATE INDEX IF NOT EXISTS idx_bill_committee_data_source ON master.bill_committee(data_source);

CREATE INDEX IF NOT EXISTS idx_federal_bill_subject_bill ON master.federal_bill_subject(bill_print_no, bill_session_year);
CREATE INDEX IF NOT EXISTS idx_federal_bill_text_bill ON master.federal_bill_text(bill_print_no, bill_session_year, bill_amend_version);
CREATE INDEX IF NOT EXISTS idx_federal_doc_ref_bill ON master.federal_doc_reference(bill_print_no, bill_session_year);
CREATE INDEX IF NOT EXISTS idx_federal_relationship_bill ON master.federal_bill_relationship(bill_print_no, bill_session_year);

-- Add triggers for change logging on new federal tables
CREATE TRIGGER log_federal_bill_subject_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_bill_subject FOR EACH ROW EXECUTE PROCEDURE master.log_bill_updates();
CREATE TRIGGER log_federal_bill_text_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_bill_text FOR EACH ROW EXECUTE PROCEDURE master.log_bill_updates();
CREATE TRIGGER log_federal_doc_reference_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_doc_reference FOR EACH ROW EXECUTE PROCEDURE master.log_bill_updates();
CREATE TRIGGER log_federal_bill_relationship_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_bill_relationship FOR EACH ROW EXECUTE PROCEDURE master.log_bill_updates();
