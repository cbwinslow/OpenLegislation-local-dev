-- Create normalized tables for legislative ingestion pipeline
CREATE TABLE IF NOT EXISTS public.openstates_people (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    given_name TEXT,
    family_name TEXT,
    party TEXT,
    chamber TEXT,
    state TEXT,
    district TEXT,
    email TEXT,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB
);

CREATE TABLE IF NOT EXISTS public.openstates_bills (
    id TEXT PRIMARY KEY,
    identifier TEXT NOT NULL,
    legislative_session TEXT NOT NULL,
    title TEXT NOT NULL,
    classification JSONB NOT NULL,
    subject JSONB NOT NULL,
    first_action_date DATE,
    last_action_date DATE,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    primary_sponsor TEXT,
    source_updated TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB,
    CONSTRAINT uq_openstates_bill_session UNIQUE(identifier, legislative_session)
);

CREATE TABLE IF NOT EXISTS public.openstates_votes (
    id TEXT PRIMARY KEY,
    bill_id TEXT NOT NULL,
    organization TEXT,
    motion_text TEXT,
    motion_classification JSONB NOT NULL,
    result TEXT,
    start_date TIMESTAMPTZ,
    counts JSONB NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB
);

CREATE TABLE IF NOT EXISTS public.congress_bills (
    bill_id TEXT PRIMARY KEY,
    congress TEXT NOT NULL,
    bill_type TEXT NOT NULL,
    bill_number TEXT NOT NULL,
    title TEXT,
    sponsor_bioguide_id TEXT,
    introduced_date DATE,
    latest_action_date DATE,
    latest_action_text TEXT,
    subjects JSONB NOT NULL,
    source_updated TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB
);

CREATE TABLE IF NOT EXISTS public.congress_members (
    bioguide_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    party TEXT,
    chamber TEXT,
    state TEXT,
    district TEXT,
    start_date DATE,
    end_date DATE,
    source_updated TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB
);

CREATE TABLE IF NOT EXISTS public.congress_votes (
    id TEXT PRIMARY KEY,
    chamber TEXT NOT NULL,
    congress TEXT NOT NULL,
    session TEXT,
    roll_call TEXT NOT NULL,
    vote_date TIMESTAMPTZ NOT NULL,
    question TEXT,
    description TEXT,
    result TEXT,
    yeas INTEGER NOT NULL,
    nays INTEGER NOT NULL,
    present INTEGER NOT NULL,
    not_voting INTEGER NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB,
    CONSTRAINT uq_congress_vote UNIQUE(chamber, congress, session, roll_call)
);

CREATE TABLE IF NOT EXISTS public.govinfo_packages (
    package_id TEXT PRIMARY KEY,
    title TEXT,
    collection_code TEXT,
    summary TEXT,
    congress TEXT,
    download TEXT,
    last_modified TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB
);

CREATE TABLE IF NOT EXISTS public.govinfo_downloads (
    package_id TEXT NOT NULL,
    format TEXT NOT NULL,
    url TEXT NOT NULL,
    size BIGINT,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB,
    CONSTRAINT uq_govinfo_download UNIQUE(package_id, format)
);

CREATE TABLE IF NOT EXISTS public.openleg_bills (
    print_no TEXT PRIMARY KEY,
    session TEXT NOT NULL,
    title TEXT,
    sponsor_member_id INTEGER,
    summary TEXT,
    law_section TEXT,
    last_status TEXT,
    last_status_date DATE,
    committee_name TEXT,
    cosponsors JSONB NOT NULL,
    source_updated TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB
);

CREATE TABLE IF NOT EXISTS public.openleg_agendas (
    agenda_id TEXT PRIMARY KEY,
    meeting_date DATE,
    committee_name TEXT,
    location TEXT,
    notes TEXT,
    bills JSONB NOT NULL,
    published_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_payload JSONB
);

