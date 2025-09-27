-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the bills table
CREATE TABLE bills (
    id SERIAL PRIMARY KEY,
    base_bill_id VARCHAR(255) UNIQUE NOT NULL,
    session_year INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    status VARCHAR(255),
    ldblurb TEXT,
    substituted_by VARCHAR(255),
    reprint_of VARCHAR(255),
    direct_previous_version VARCHAR(255),
    chapter_num INTEGER,
    chapter_year INTEGER,
    federal_congress INTEGER,
    federal_source VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create the amendments table
CREATE TABLE amendments (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    version VARCHAR(10) NOT NULL,
    memo TEXT,
    law_section VARCHAR(255),
    law_code VARCHAR(255),
    act_clause TEXT,
    full_text TEXT,
    stricken BOOLEAN DEFAULT FALSE,
    uni_bill BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create the actions table
CREATE TABLE actions (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    action_date DATE NOT NULL,
    chamber VARCHAR(50),
    sequence_no INTEGER,
    text TEXT,
    type VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the sponsors table
CREATE TABLE sponsors (
    id SERIAL PRIMARY KEY,
    member_id VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the bill_sponsors join table
CREATE TABLE bill_sponsors (
    bill_id INTEGER REFERENCES bills(id),
    sponsor_id INTEGER REFERENCES sponsors(id),
    is_primary BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (bill_id, sponsor_id)
);

-- Create the committees table
CREATE TABLE committees (
    id SERIAL PRIMARY KEY,
    committee_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    chamber VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the bill_committees join table
CREATE TABLE bill_committees (
    bill_id INTEGER REFERENCES bills(id),
    committee_id INTEGER REFERENCES committees(id),
    PRIMARY KEY (bill_id, committee_id)
);

-- Create the votes table
CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    amendment_id INTEGER REFERENCES amendments(id),
    vote_date TIMESTAMP,
    vote_type VARCHAR(255),
    ayes INTEGER,
    nays INTEGER,
    abstains INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the related_bills table
CREATE TABLE related_bills (
    bill_id INTEGER REFERENCES bills(id),
    related_bill_id INTEGER REFERENCES bills(id),
    relationship_type VARCHAR(255),
    PRIMARY KEY (bill_id, related_bill_id)
);

-- Create the laws table
CREATE TABLE laws (
    id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bills(id),
    law_type VARCHAR(255),
    law_number VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create the govinfo_metadata table
CREATE TABLE govinfo_metadata (
    bill_id INTEGER REFERENCES bills(id),
    package_id VARCHAR(255),
    last_modified TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (bill_id)
);