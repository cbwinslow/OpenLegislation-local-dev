-- Database schema for web crawling and legislative data collection
-- This schema stores crawled data from government websites

-- Main table for crawled legislative data
CREATE TABLE IF NOT EXISTS crawled_legislative_data (
    id SERIAL PRIMARY KEY,
    jurisdiction VARCHAR(50) NOT NULL, -- 'federal', 'nys', 'california', etc.
    data_type VARCHAR(50) NOT NULL, -- 'bills', 'members', 'votes', 'committees', 'hearings'
    source_url TEXT NOT NULL,
    crawled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    content_hash VARCHAR(64), -- For detecting changes
    raw_data JSONB, -- Store the extracted data as JSON
    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'error'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient querying
CREATE INDEX IF NOT EXISTS idx_crawled_data_jurisdiction ON crawled_legislative_data(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_crawled_data_type ON crawled_legislative_data(data_type);
CREATE INDEX IF NOT EXISTS idx_crawled_data_status ON crawled_legislative_data(processing_status);
CREATE INDEX IF NOT EXISTS idx_crawled_data_crawled_at ON crawled_legislative_data(crawled_at);
CREATE INDEX IF NOT EXISTS idx_crawled_data_hash ON crawled_legislative_data(content_hash);

-- Table for crawl sessions/metadata
CREATE TABLE IF NOT EXISTS crawl_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_websites INTEGER DEFAULT 0,
    successful_crawls INTEGER DEFAULT 0,
    failed_crawls INTEGER DEFAULT 0,
    total_records INTEGER DEFAULT 0,
    jurisdictions_crawled JSONB, -- Array of jurisdictions
    data_types_crawled JSONB, -- Array of data types
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for website configurations
CREATE TABLE IF NOT EXISTS website_configs (
    id SERIAL PRIMARY KEY,
    jurisdiction VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    website_name VARCHAR(100) NOT NULL,
    base_url TEXT NOT NULL,
    crawl_url TEXT NOT NULL, -- Specific URL to crawl
    crawl_frequency_hours INTEGER DEFAULT 24, -- How often to crawl
    last_crawled TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    crawl_config JSONB, -- Store crawl4ai configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(jurisdiction, data_type, website_name)
);

-- Index for website configs
CREATE INDEX IF NOT EXISTS idx_website_configs_jurisdiction ON website_configs(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_website_configs_active ON website_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_website_configs_last_crawled ON website_configs(last_crawled);

-- Table for ingestion triggers
CREATE TABLE IF NOT EXISTS ingestion_triggers (
    id SERIAL PRIMARY KEY,
    trigger_name VARCHAR(100) UNIQUE NOT NULL,
    jurisdiction VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    script_path TEXT NOT NULL, -- Path to ingestion script
    trigger_condition JSONB, -- Conditions for triggering
    last_triggered TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default website configurations
INSERT INTO website_configs (jurisdiction, data_type, website_name, base_url, crawl_url, crawl_config) VALUES
('federal', 'bills', 'congress_gov', 'https://www.congress.gov', 'https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%7D', '{
    "wait_for": "body",
    "page_timeout": 30000,
    "delay_before_return_html": 2.0
}'),
('federal', 'members', 'congress_gov', 'https://www.congress.gov', 'https://www.congress.gov/members', '{
    "wait_for": "body",
    "page_timeout": 30000,
    "delay_before_return_html": 2.0
}'),
('nys', 'bills', 'nysenate_gov', 'https://www.nysenate.gov', 'https://www.nysenate.gov/search/legislation', '{
    "wait_for": "body",
    "page_timeout": 30000,
    "delay_before_return_html": 2.0
}'),
('nys', 'members', 'nysenate_gov', 'https://www.nysenate.gov', 'https://www.nysenate.gov/senators-committees', '{
    "wait_for": "body",
    "page_timeout": 30000,
    "delay_before_return_html": 2.0
}')
ON CONFLICT (jurisdiction, data_type, website_name) DO NOTHING;

-- Insert default ingestion triggers
INSERT INTO ingestion_triggers (trigger_name, jurisdiction, data_type, script_path, trigger_condition) VALUES
('federal_bill_ingestion', 'federal', 'bills', 'tools/ingestion/core/ingest_federal_data.py', '{"min_records": 1}'),
('federal_member_ingestion', 'federal', 'members', 'tools/ingestion/members/ingest_federal_members.py', '{"min_records": 1}'),
('nys_bill_ingestion', 'nys', 'bills', 'tools/ingestion/core/ingest_nys_data.py', '{"min_records": 1}'),
('nys_member_ingestion', 'nys', 'members', 'tools/ingestion/members/ingest_nys_members.py', '{"min_records": 1}')
ON CONFLICT (trigger_name) DO NOTHING;

-- Function to trigger ingestion for new crawled data
CREATE OR REPLACE FUNCTION trigger_ingestion_for_crawled_data()
RETURNS TRIGGER AS $$
DECLARE
    trigger_record RECORD;
    script_path TEXT;
BEGIN
    -- Only trigger for newly inserted or updated records that are processed
    IF NEW.processing_status = 'processed' AND (OLD.processing_status IS NULL OR OLD.processing_status != 'processed') THEN
        -- Find matching ingestion triggers
        FOR trigger_record IN
            SELECT * FROM ingestion_triggers
            WHERE jurisdiction = NEW.jurisdiction
            AND data_type = NEW.data_type
            AND is_active = TRUE
        LOOP
            -- Update last_triggered timestamp
            UPDATE ingestion_triggers
            SET last_triggered = CURRENT_TIMESTAMP
            WHERE id = trigger_record.id;

            -- Log the trigger (you could also execute the script here)
            RAISE NOTICE 'Triggered ingestion for % %: %', NEW.jurisdiction, NEW.data_type, trigger_record.script_path;
        END LOOP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on crawled_legislative_data table
DROP TRIGGER IF EXISTS trigger_ingestion_on_processed_data ON crawled_legislative_data;
CREATE TRIGGER trigger_ingestion_on_processed_data
    AFTER INSERT OR UPDATE ON crawled_legislative_data
    FOR EACH ROW EXECUTE FUNCTION trigger_ingestion_for_crawled_data();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add update triggers for timestamp columns
DROP TRIGGER IF EXISTS update_crawled_data_updated_at ON crawled_legislative_data;
CREATE TRIGGER update_crawled_data_updated_at
    BEFORE UPDATE ON crawled_legislative_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_website_configs_updated_at ON website_configs;
CREATE TRIGGER update_website_configs_updated_at
    BEFORE UPDATE ON website_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ingestion_triggers_updated_at ON ingestion_triggers;
CREATE TRIGGER update_ingestion_triggers_updated_at
    BEFORE UPDATE ON ingestion_triggers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();