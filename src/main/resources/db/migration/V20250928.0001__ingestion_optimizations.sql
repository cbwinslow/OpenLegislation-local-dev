-- Migration: Add indexes, constraints, and optimizations for federal ingestion
-- Ensures 3NF compliance, proper FKs, indexes for high-volume queries, partitioning readiness

-- Add indexes for bill lookups (high-volume)
CREATE INDEX IF NOT EXISTS idx_bill_congress_session ON master.bill (congress, bill_session_year) WHERE data_source = 'federal';
CREATE INDEX IF NOT EXISTS idx_bill_status_date ON master.bill (status_date) WHERE data_source = 'federal';
CREATE INDEX IF NOT EXISTS idx_bill_sponsor_state ON master.bill (sponsor_state, sponsor_party) WHERE data_source = 'federal';

-- Indexes for actions (frequent range queries)
CREATE INDEX IF NOT EXISTS idx_bill_action_date_chamber ON master.bill_amendment_action (effect_date, chamber) WHERE data_source = 'federal';
CREATE INDEX IF NOT EXISTS idx_bill_action_sequence ON master.bill_amendment_action (sequence_no) WHERE data_source = 'federal';

-- Indexes for sponsors and cosponsors
CREATE INDEX IF NOT EXISTS idx_bill_sponsor_member ON master.bill_sponsor (session_member_id) WHERE data_source = 'federal';
CREATE INDEX IF NOT EXISTS idx_bill_cosponsor_sequence ON master.bill_amendment_cosponsor (sequence_no) WHERE data_source = 'federal';

-- Committee indexes for amendments and votes
CREATE INDEX IF NOT EXISTS idx_bill_committee_name_chamber ON master.bill_amendment (committee_name, committee_chamber) WHERE data_source = 'federal';
CREATE INDEX IF NOT EXISTS idx_vote_date_type ON master.bill_amendment_vote_info (vote_date, vote_type) WHERE data_source = 'federal';

-- Ensure FK constraints are in place (if not already from models)
-- Note: Assuming models generate these, but explicit for safety
ALTER TABLE master.bill_amendment
ADD CONSTRAINT IF NOT EXISTS fk_bill_amendment_bill
FOREIGN KEY (bill_print_no, bill_session_year)
REFERENCES master.bill (bill_print_no, bill_session_year)
ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE master.bill_sponsor
ADD CONSTRAINT IF NOT EXISTS fk_bill_sponsor_bill
FOREIGN KEY (bill_print_no, bill_session_year)
REFERENCES master.bill (bill_print_no, bill_session_year)
ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE master.bill_amendment_action
ADD CONSTRAINT IF NOT EXISTS fk_bill_action_amendment
FOREIGN KEY (bill_print_no, bill_session_year, bill_amend_version)
REFERENCES master.bill_amendment (bill_print_no, bill_session_year, bill_amend_version)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Add check constraints for data integrity (federal-specific)
ALTER TABLE master.bill
ADD CONSTRAINT IF NOT EXISTS chk_bill_federal_congress
CHECK (data_source = 'federal' IMPLIES congress IS NOT NULL AND congress > 0);

ALTER TABLE master.bill
ADD CONSTRAINT IF NOT EXISTS chk_bill_data_source
CHECK (data_source IN ('state', 'federal'));

-- For raw payloads, ensure JSONB indexing if needed
CREATE INDEX IF NOT EXISTS idx_raw_payload_ingestion_type ON master.govinfo_raw_payload (ingestion_type);
CREATE INDEX IF NOT EXISTS idx_raw_payload_record_id ON master.govinfo_raw_payload (record_id);

-- Partitioning readiness: For high-volume, suggest partitioning bill by congress (manual step, not auto)
-- Example for congress 118 partition (user to execute if volume high)
-- CREATE TABLE master.bill_118 PARTITION OF master.bill FOR VALUES FROM (118) TO (119);
-- ALTER TABLE master.bill DETACH PARTITION master.bill_118; -- If needed later

-- Add updated_at trigger if not present (for all tables)
CREATE OR REPLACE FUNCTION master.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_date_time = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bill_updated_at BEFORE UPDATE
ON master.bill FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_amendment_updated_at BEFORE UPDATE
ON master.bill_amendment FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

-- Similar for other tables: committee_version, agenda_info_addendum, etc.
CREATE TRIGGER update_committee_version_updated_at BEFORE UPDATE
ON master.committee_version FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_agenda_updated_at BEFORE UPDATE
ON master.agenda FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

CREATE TRIGGER update_calendar_updated_at BEFORE UPDATE
ON master.calendar FOR EACH ROW EXECUTE FUNCTION master.update_updated_at_column();

-- Ensure vector extension for embeddings (if not enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Validation: Add a view for ingestion stats
CREATE OR REPLACE VIEW master.ingestion_stats AS
SELECT
    data_source,
    COUNT(*) as total_records,
    COUNT(CASE WHEN status IS NOT NULL THEN 1 END) as with_status,
    AVG(EXTRACT(EPOCH FROM (modified_date_time - created_date_time))) as avg_age_seconds
FROM master.bill
GROUP BY data_source;

-- Comment for audit
COMMENT ON TABLE master.bill IS 'Universal bill table supporting state and federal ingestion with optimizations for high-volume inserts';