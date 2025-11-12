-- Sample DDL for bill-related tables (PostgreSQL).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS master.bill (
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    title TEXT,
    summary TEXT,
    active_version CHARACTER(1) NOT NULL DEFAULT '',
    status TEXT,
    status_date DATE,
    data_source TEXT DEFAULT 'state',
    congress INTEGER,
    bill_type TEXT,
    short_title TEXT,
    sponsor_party TEXT,
    sponsor_state TEXT,
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    modified_date_time TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (bill_print_no, bill_session_year)
);

CREATE TABLE IF NOT EXISTS master.bill_amendment (
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    bill_amend_version CHARACTER(1) NOT NULL,
    sponsor_memo TEXT,
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (bill_print_no, bill_session_year, bill_amend_version),
    FOREIGN KEY (bill_print_no, bill_session_year) REFERENCES master.bill (bill_print_no, bill_session_year) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS master.bill_amendment_vote_info (
    id SERIAL PRIMARY KEY,
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    bill_amend_version CHARACTER(1) NOT NULL,
    vote_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    vote_type master.vote_type NOT NULL,
    committee_name TEXT,
    committee_chamber master.chamber,
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    FOREIGN KEY (bill_print_no, bill_session_year, bill_amend_version) REFERENCES master.bill_amendment ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS master.bill_amendment_vote_roll (
    vote_id INTEGER NOT NULL,
    session_member_id INTEGER NOT NULL,
    session_year SMALLINT NOT NULL,
    vote_code master.vote_code NOT NULL,
    member_short_name TEXT,
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (vote_id, session_member_id, session_year, vote_code),
    FOREIGN KEY (vote_id) REFERENCES master.bill_amendment_vote_info (id) ON DELETE CASCADE,
    FOREIGN KEY (session_member_id) REFERENCES public.session_member (id)
);

CREATE TABLE IF NOT EXISTS master.bill_milestone (
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    status TEXT NOT NULL,
    rank SMALLINT NOT NULL,
    action_sequence_no SMALLINT NOT NULL,
    date DATE NOT NULL,
    committee_name TEXT,
    committee_chamber master.chamber,
    created_date_time TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (bill_print_no, bill_session_year, status, rank),
    FOREIGN KEY (bill_print_no, bill_session_year) REFERENCES master.bill (bill_print_no, bill_session_year) ON DELETE CASCADE
);

-- Vector table for embeddings.
CREATE TABLE IF NOT EXISTS master.bill_embeddings (
    bill_print_no TEXT NOT NULL,
    bill_session_year SMALLINT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    PRIMARY KEY (bill_print_no, bill_session_year)
);

CREATE TABLE IF NOT EXISTS master.govinfo_raw_payload (
    id BIGSERIAL PRIMARY KEY,
    ingestion_type TEXT NOT NULL,
    record_id TEXT NOT NULL,
    source_path TEXT,
    payload JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);
