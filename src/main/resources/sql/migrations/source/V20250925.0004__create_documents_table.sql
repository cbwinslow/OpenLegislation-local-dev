-- Create documents table for ingestion
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(255) NOT NULL,
    url VARCHAR(2048) UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    pub_date TIMESTAMP,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_pub_date ON documents(pub_date);
CREATE INDEX IF NOT EXISTS idx_documents_url ON documents(url);
