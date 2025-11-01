-- Migration: Generic Ingestion Status Tracking
-- Creates a flexible table to track ingestion progress for any data source or table
-- Supports multiple ingestion types with configurable record identifiers

-- Generic Ingestion Status table
CREATE TABLE IF NOT EXISTS master.ingestion_status (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL, -- Target table being ingested into
    record_id TEXT NOT NULL, -- Unique identifier for the record (can be composite key serialized)
    source TEXT NOT NULL DEFAULT 'unknown', -- Data source (govinfo, congress_api, etc.)
    ingestion_status TEXT NOT NULL CHECK (ingestion_status IN ('pending', 'in_progress', 'completed', 'failed')),
    last_attempted_at TIMESTAMP,
    completed_at TIMESTAMP,
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    processing_priority INTEGER DEFAULT 0, -- Higher priority processed first
    metadata JSONB, -- Additional data about the record
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    ingestion_session_id TEXT, -- Groups related ingestion runs
    UNIQUE(table_name, record_id, source)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ingestion_status_table_record ON master.ingestion_status(table_name, record_id, source);
CREATE INDEX IF NOT EXISTS idx_ingestion_status_status ON master.ingestion_status(ingestion_status);
CREATE INDEX IF NOT EXISTS idx_ingestion_status_session ON master.ingestion_status(ingestion_session_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_status_source ON master.ingestion_status(source);
CREATE INDEX IF NOT EXISTS idx_ingestion_status_priority ON master.ingestion_status(processing_priority DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_status_updated ON master.ingestion_status(updated_at);

-- Add trigger for change logging
CREATE TRIGGER IF NOT EXISTS log_ingestion_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.ingestion_status FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates();

-- Comments for documentation
COMMENT ON TABLE master.ingestion_status IS 'Generic ingestion status tracking for any table or data source';
COMMENT ON COLUMN master.ingestion_status.table_name IS 'Name of the target table being ingested into';
COMMENT ON COLUMN master.ingestion_status.record_id IS 'Unique identifier for the record being processed';
COMMENT ON COLUMN master.ingestion_status.source IS 'Data source identifier (govinfo, congress_api, etc.)';
COMMENT ON COLUMN master.ingestion_status.ingestion_status IS 'Current processing status';
COMMENT ON COLUMN master.ingestion_status.metadata IS 'Additional JSON data about the record';