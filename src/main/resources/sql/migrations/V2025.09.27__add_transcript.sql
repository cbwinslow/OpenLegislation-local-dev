-- Add transcript table for CREC
CREATE TABLE IF NOT EXISTS master.transcript (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'CREC'
    govinfo_pkg_id VARCHAR(100) UNIQUE NOT NULL,
    date DATE NOT NULL,
    chamber VARCHAR(20),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transcript_date ON master.transcript(date);
CREATE INDEX idx_transcript_source ON master.transcript(source);
