-- Create view for federal member details
CREATE OR REPLACE VIEW master.v_federal_member_details AS
SELECT
    p.id as person_id,
    p.bioguide_id,
    p.full_name,
    m.chamber,
    m.state,
    m.district,
    m.party,
    m.current_member,
    array_agg(t.congress) as congresses,
    string_agg(sm.platform || ':' || sm.handle, ', ') as social_media
FROM master.federal_person p
JOIN master.federal_member m ON p.id = m.person_id
LEFT JOIN master.federal_member_term t ON m.id = t.member_id
LEFT JOIN master.federal_member_social_media sm ON m.id = sm.member_id
GROUP BY p.id, p.bioguide_id, p.full_name, m.chamber, m.state, m.district, m.party, m.current_member;

-- Create view for bill summary
CREATE OR REPLACE VIEW master.v_bill_summary AS
SELECT
    b.bill_print_no,
    b.bill_session_year,
    b.title,
    b.status,
    count(ba.sequence_no) as action_count,
    array_agg(DISTINCT bs.session_member_id) as sponsors,
    string_agg(DISTINCT bc.committee_name, ', ') as committees
FROM master.bill b
LEFT JOIN master.bill_amendment_action ba ON b.bill_print_no = ba.bill_print_no AND b.bill_session_year = ba.bill_session_year
LEFT JOIN master.bill_sponsor bs ON b.bill_print_no = bs.bill_print_no AND b.bill_session_year = bs.bill_session_year
LEFT JOIN master.bill_committee bc ON b.bill_print_no = bc.bill_print_no AND b.bill_session_year = bc.bill_session_year
GROUP BY b.bill_print_no, b.bill_session_year, b.title, b.status;

-- PL/SQL function for current member terms
CREATE OR REPLACE FUNCTION master.fn_get_current_terms(member_id INTEGER)
RETURNS TABLE (congress INTEGER, start_year INTEGER, end_year INTEGER) AS $$
BEGIN
    RETURN QUERY
    SELECT t.congress, t.start_year, t.end_year
    FROM master.federal_member_term t
    WHERE t.member_id = $1
    AND (t.end_year IS NULL OR t.end_year >= EXTRACT(YEAR FROM current_date))
    ORDER BY t.congress DESC;
END;
$$ LANGUAGE plpgsql;

-- Index on views if needed
CREATE INDEX idx_v_member_details_bioguide ON master.v_federal_member_details(bioguide_id);

-- Add missing FK for federal_member_office
ALTER TABLE master.federal_member_office ADD CONSTRAINT fk_federal_member_office_member
FOREIGN KEY (member_id) REFERENCES master.federal_member(id) ON DELETE CASCADE;

-- Example view for audit
CREATE OR REPLACE VIEW master.v_recent_audits AS
SELECT * FROM master.audit_log
WHERE changed_at >= now() - INTERVAL '7 days'
ORDER BY changed_at DESC;
