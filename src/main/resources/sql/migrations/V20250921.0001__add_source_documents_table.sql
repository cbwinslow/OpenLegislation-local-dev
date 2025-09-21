-- Migration: create a canonical source_documents table for ingesting external bulk XML
-- This single table is designed to receive records from govinfo, congress, state, and local sources.
-- Fields are intentionally generic but capture important metadata and the raw payload.

CREATE TABLE IF NOT EXISTS source_documents (
    id BIGSERIAL PRIMARY KEY,
    source_domain TEXT NOT NULL,
    source_collection TEXT,
    source_congress TEXT,
    source_session TEXT,
    source_filename TEXT,
    source_url TEXT,
    doc_type TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    canonical_id TEXT,
    title TEXT,
    sponsors JSONB,
    actions JSONB,
    text_versions JSONB,
    raw_xml bytea,
    parsed_json JSONB,
    ingest_status TEXT DEFAULT 'new',
    ingest_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_source_documents_source_domain ON source_documents (source_domain);
CREATE INDEX IF NOT EXISTS idx_source_documents_canonical_id ON source_documents (canonical_id);
CREATE INDEX IF NOT EXISTS idx_source_documents_published_at ON source_documents (published_at);
