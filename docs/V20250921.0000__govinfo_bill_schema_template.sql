-- Flyway template: Add tables to store govinfo bill metadata and texts
-- Copy to src/main/resources/sql/migrations as needed and adjust naming.

-- Example schema: govinfo_bill (metadata)
CREATE TABLE IF NOT EXISTS govinfo_bill (
    id BIGSERIAL PRIMARY KEY,
    congress INTEGER NOT NULL,
    bill_number VARCHAR(64) NOT NULL,
    bill_type VARCHAR(8),
    title TEXT,
    introduced_date TIMESTAMP,
    sponsor_name VARCHAR(255),
    sponsor_party VARCHAR(8),
    sponsor_state VARCHAR(8),
    created_at TIMESTAMP DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_govinfo_bill_congress_number ON govinfo_bill(congress, bill_number);

-- Example schema: govinfo_bill_text (versions)
CREATE TABLE IF NOT EXISTS govinfo_bill_text (
    id BIGSERIAL PRIMARY KEY,
    govinfo_bill_id BIGINT NOT NULL REFERENCES govinfo_bill(id) ON DELETE CASCADE,
    version_id VARCHAR(128) NOT NULL,
    text_format VARCHAR(16), -- 'html' or 'plain'
    content TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_govinfo_bill_text_billid ON govinfo_bill_text(govinfo_bill_id);

-- Example schema: govinfo_bill_action (history)
CREATE TABLE IF NOT EXISTS govinfo_bill_action (
    id BIGSERIAL PRIMARY KEY,
    govinfo_bill_id BIGINT NOT NULL REFERENCES govinfo_bill(id) ON DELETE CASCADE,
    action_date TIMESTAMP,
    chamber VARCHAR(16),
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_govinfo_bill_action_billid ON govinfo_bill_action(govinfo_bill_id);

-- NOTE: This is a template. When ready to apply, move into the Flyway migrations directory
-- and run `mvn compile flyway:migrate`. Ensure to add tests and DAOs before writing production data.
