-- Migration: Federal Member Ingestion Status Tracking
-- Creates table to track ingestion progress and enable resume capability
-- Allows the system to know which members have been processed and their status

-- Federal Member Ingestion Status table
CREATE TABLE IF NOT EXISTS master.federal_member_ingestion_status (
    id BIGSERIAL PRIMARY KEY,
    bioguide_id TEXT NOT NULL UNIQUE, -- Congress.gov unique identifier
    ingestion_status TEXT NOT NULL CHECK (ingestion_status IN ('pending', 'in_progress', 'completed', 'failed')),
    last_attempted_at TIMESTAMP,
    completed_at TIMESTAMP,
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    ingestion_session_id TEXT, -- To group related ingestion runs
    processing_order INTEGER -- For ordered processing if needed
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_federal_member_ingestion_status_bioguide ON master.federal_member_ingestion_status(bioguide_id);
CREATE INDEX IF NOT EXISTS idx_federal_member_ingestion_status_status ON master.federal_member_ingestion_status(ingestion_status);
CREATE INDEX IF NOT EXISTS idx_federal_member_ingestion_status_session ON master.federal_member_ingestion_status(ingestion_session_id);
CREATE INDEX IF NOT EXISTS idx_federal_member_ingestion_status_updated ON master.federal_member_ingestion_status(updated_at);

-- Add trigger for change logging
CREATE TRIGGER log_federal_member_ingestion_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_member_ingestion_status FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates();

-- Comments for documentation
COMMENT ON TABLE master.federal_member_ingestion_status IS 'Tracks ingestion status for federal members to enable resume capability';
COMMENT ON COLUMN master.federal_member_ingestion_status.bioguide_id IS 'Congress.gov unique identifier for the member';
COMMENT ON COLUMN master.federal_member_ingestion_status.ingestion_status IS 'Current status: pending, in_progress, completed, or failed';
COMMENT ON COLUMN master.federal_member_ingestion_status.ingestion_session_id IS 'Groups related ingestion runs for tracking purposes';