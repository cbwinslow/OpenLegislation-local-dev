-- Migration: Federal Member Schema for Congress.gov Integration
-- Creates tables to store federal legislator data from congress.gov API
-- Mirrors state member schema but adapted for federal structure

-- Federal Person table (basic biographical info)
CREATE TABLE IF NOT EXISTS master.federal_person (
    id BIGSERIAL PRIMARY KEY,
    bioguide_id TEXT UNIQUE NOT NULL, -- Congress.gov unique identifier
    full_name TEXT NOT NULL,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    suffix TEXT,
    nickname TEXT,
    birth_year INTEGER,
    death_year INTEGER,
    gender TEXT CHECK (gender IN ('M', 'F')),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Federal Member table (political info)
CREATE TABLE IF NOT EXISTS master.federal_member (
    id BIGSERIAL PRIMARY KEY,
    person_id BIGINT NOT NULL REFERENCES master.federal_person(id),
    chamber TEXT NOT NULL CHECK (chamber IN ('house', 'senate')),
    state TEXT NOT NULL, -- Two-letter state code
    district TEXT, -- District number for House, null for Senate
    party TEXT CHECK (party IN ('D', 'R', 'I', 'ID')), -- Including Independent
    current_member BOOLEAN DEFAULT true,
    member_type TEXT DEFAULT 'federal' CHECK (member_type = 'federal'),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(person_id, chamber, state, district)
);

-- Federal Member Terms (service history)
CREATE TABLE IF NOT EXISTS master.federal_member_term (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL REFERENCES master.federal_member(id),
    congress INTEGER NOT NULL, -- Congress number (e.g., 118)
    start_year INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    party TEXT CHECK (party IN ('D', 'R', 'I', 'ID')),
    state TEXT NOT NULL,
    district TEXT,
    chamber TEXT NOT NULL CHECK (chamber IN ('house', 'senate')),
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(member_id, congress)
);

-- Federal Member Committees (current committee assignments)
CREATE TABLE IF NOT EXISTS master.federal_member_committee (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL REFERENCES master.federal_member(id),
    committee_code TEXT NOT NULL, -- e.g., "HSAG" for House Agriculture
    committee_name TEXT NOT NULL,
    subcommittee_code TEXT, -- For subcommittees
    subcommittee_name TEXT,
    position TEXT CHECK (position IN ('chair', 'ranking_member', 'vice_chair', 'member', 'ex_officio')),
    congress INTEGER NOT NULL,
    chamber TEXT NOT NULL CHECK (chamber IN ('house', 'senate')),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(member_id, committee_code, subcommittee_code, congress)
);

-- Federal Member Social Media (official accounts)
CREATE TABLE IF NOT EXISTS master.federal_member_social_media (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL REFERENCES master.federal_member(id),
    platform TEXT NOT NULL CHECK (platform IN ('twitter', 'facebook', 'youtube', 'instagram', 'website')),
    handle TEXT, -- Username/handle
    url TEXT, -- Full URL
    is_official BOOLEAN DEFAULT true,
    follower_count INTEGER,
    last_verified TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE(member_id, platform)
);

-- Federal Member Contact Information
CREATE TABLE IF NOT EXISTS master.federal_member_contact (
    id BIGSERIAL PRIMARY KEY,
    member_id BIGINT NOT NULL REFERENCES master.federal_member(id),
    contact_type TEXT NOT NULL CHECK (contact_type IN ('office', 'district', 'personal')),
    phone TEXT,
    fax TEXT,
    email TEXT,
    address_line_1 TEXT,
    address_line_2 TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    building TEXT, -- Capitol building (e.g., "Longworth House Office Building")
    room TEXT, -- Room number
    congress INTEGER NOT NULL, -- For historical contact info
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_federal_person_bioguide ON master.federal_person(bioguide_id);
CREATE INDEX IF NOT EXISTS idx_federal_member_chamber_state ON master.federal_member(chamber, state);
CREATE INDEX IF NOT EXISTS idx_federal_member_current ON master.federal_member(current_member);
CREATE INDEX IF NOT EXISTS idx_federal_member_term_congress ON master.federal_member_term(congress);
CREATE INDEX IF NOT EXISTS idx_federal_member_committee_member ON master.federal_member_committee(member_id);
CREATE INDEX IF NOT EXISTS idx_federal_member_social_platform ON master.federal_member_social_media(member_id, platform);
CREATE INDEX IF NOT EXISTS idx_federal_member_contact_member ON master.federal_member_contact(member_id);

-- Add triggers for change logging
CREATE TRIGGER log_federal_person_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_person FOR EACH ROW EXECUTE PROCEDURE master.log_person_updates();
CREATE TRIGGER log_federal_member_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_member FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates();
CREATE TRIGGER log_federal_member_term_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_member_term FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates();
CREATE TRIGGER log_federal_member_committee_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_member_committee FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates();
CREATE TRIGGER log_federal_member_social_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_member_social_media FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates();
CREATE TRIGGER log_federal_member_contact_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.federal_member_contact FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates();

-- Comments for documentation
COMMENT ON TABLE master.federal_person IS 'Basic biographical information for federal legislators from congress.gov';
COMMENT ON TABLE master.federal_member IS 'Political information and current status for federal members';
COMMENT ON TABLE master.federal_member_term IS 'Historical terms served by federal members';
COMMENT ON TABLE master.federal_member_committee IS 'Current committee assignments for federal members';
COMMENT ON TABLE master.federal_member_social_media IS 'Official social media accounts for federal members';
COMMENT ON TABLE master.federal_member_contact IS 'Contact information for federal members offices';