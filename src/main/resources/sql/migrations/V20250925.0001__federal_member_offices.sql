-- Add table for federal member office contact information
CREATE TABLE IF NOT EXISTS master.federal_member_office (
    id SERIAL PRIMARY KEY,
    member_id INTEGER NOT NULL REFERENCES master.federal_member(id) ON DELETE CASCADE,
    office_type VARCHAR(50) NOT NULL,  -- e.g., 'capitol', 'district', 'state'
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    phone VARCHAR(20),
    fax VARCHAR(20),
    is_current BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(member_id, office_type, is_current)
);

-- Index for queries
CREATE INDEX idx_federal_member_office_member_id ON master.federal_member_office(member_id);
CREATE INDEX idx_federal_member_office_current ON master.federal_member_office(member_id, is_current);
