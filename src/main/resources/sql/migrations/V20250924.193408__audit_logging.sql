-- V20250924.193408__audit_logging.sql
-- Add audit logging table and triggers for key tables to track INSERT/UPDATE/DELETE operations

-- Create audit log table
CREATE TABLE IF NOT EXISTS master.audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id JSONB NOT NULL,  -- e.g., {"bill_print_no": "H1", "bill_session_year": 119}
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_row JSONB,
    new_row JSONB NOT NULL,
    changed_by TEXT,  -- Session ID or source
    changed_at TIMESTAMP DEFAULT now(),
    INDEX idx_audit_table_operation (table_name, operation),
    INDEX idx_audit_changed_at (changed_at)
);

-- Function to log INSERT
CREATE OR REPLACE FUNCTION master.log_audit_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO master.audit_log (table_name, record_id, operation, new_row, changed_by)
    VALUES (TG_TABLE_NAME,
            (SELECT row_to_json(t)::jsonb FROM (SELECT NEW.*) t),
            'INSERT',
            row_to_json(NEW)::jsonb,
            coalesce(current_setting('openleg.session_id', true), 'unknown'));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to log UPDATE
CREATE OR REPLACE FUNCTION master.log_audit_update()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO master.audit_log (table_name, record_id, operation, old_row, new_row, changed_by)
    VALUES (TG_TABLE_NAME,
            (SELECT row_to_json(t)::jsonb FROM (SELECT NEW.*) t),
            'UPDATE',
            row_to_json(OLD)::jsonb,
            row_to_json(NEW)::jsonb,
            coalesce(current_setting('openleg.session_id', true), 'unknown'));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to log DELETE
CREATE OR REPLACE FUNCTION master.log_audit_delete()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO master.audit_log (table_name, record_id, operation, old_row, changed_by)
    VALUES (TG_TABLE_NAME,
            row_to_json(OLD)::jsonb,
            'DELETE',
            row_to_json(OLD)::jsonb,
            coalesce(current_setting('openleg.session_id', true), 'unknown'));
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for key tables
-- Bill table
CREATE TRIGGER audit_bill_insert AFTER INSERT ON master.bill FOR EACH ROW EXECUTE FUNCTION master.log_audit_insert();
CREATE TRIGGER audit_bill_update AFTER UPDATE ON master.bill FOR EACH ROW EXECUTE FUNCTION master.log_audit_update();
CREATE TRIGGER audit_bill_delete AFTER DELETE ON master.bill FOR EACH ROW EXECUTE FUNCTION master.log_audit_delete();

-- Bill sponsor
CREATE TRIGGER audit_bill_sponsor_insert AFTER INSERT ON master.bill_sponsor FOR EACH ROW EXECUTE FUNCTION master.log_audit_insert();
CREATE TRIGGER audit_bill_sponsor_update AFTER UPDATE ON master.bill_sponsor FOR EACH ROW EXECUTE FUNCTION master.log_audit_update();
CREATE TRIGGER audit_bill_sponsor_delete AFTER DELETE ON master.bill_sponsor FOR EACH ROW EXECUTE FUNCTION master.log_audit_delete();

-- Bill amendment action
CREATE TRIGGER audit_bill_amendment_action_insert AFTER INSERT ON master.bill_amendment_action FOR EACH ROW EXECUTE FUNCTION master.log_audit_insert();
CREATE TRIGGER audit_bill_amendment_action_update AFTER UPDATE ON master.bill_amendment_action FOR EACH ROW EXECUTE FUNCTION master.log_audit_update();
CREATE TRIGGER audit_bill_amendment_action_delete AFTER DELETE ON master.bill_amendment_action FOR EACH ROW EXECUTE FUNCTION master.log_audit_delete();

-- Federal person
CREATE TRIGGER audit_federal_person_insert AFTER INSERT ON master.federal_person FOR EACH ROW EXECUTE FUNCTION master.log_audit_insert();
CREATE TRIGGER audit_federal_person_update AFTER UPDATE ON master.federal_person FOR EACH ROW EXECUTE FUNCTION master.log_audit_update();
CREATE TRIGGER audit_federal_person_delete AFTER DELETE ON master.federal_person FOR EACH ROW EXECUTE FUNCTION master.log_audit_delete();

-- Federal member
CREATE TRIGGER audit_federal_member_insert AFTER INSERT ON master.federal_member FOR EACH ROW EXECUTE FUNCTION master.log_audit_insert();
CREATE TRIGGER audit_federal_member_update AFTER UPDATE ON master.federal_member FOR EACH ROW EXECUTE FUNCTION master.log_audit_update();
CREATE TRIGGER audit_federal_member_delete AFTER DELETE ON master.federal_member FOR EACH ROW EXECUTE FUNCTION master.log_audit_delete();

-- Federal member social media
CREATE TRIGGER audit_federal_member_social_media_insert AFTER INSERT ON master.federal_member_social_media FOR EACH ROW EXECUTE FUNCTION master.log_audit_insert();
CREATE TRIGGER audit_federal_member_social_media_update AFTER UPDATE ON master.federal_member_social_media FOR EACH ROW EXECUTE FUNCTION master.log_audit_update();
CREATE TRIGGER audit_federal_member_social_media_delete AFTER DELETE ON master.federal_member_social_media FOR EACH ROW EXECUTE FUNCTION master.log_audit_delete();

-- Optional: View to query audits by table/operation
CREATE VIEW master.audit_view AS
SELECT * FROM master.audit_log
ORDER BY changed_at DESC;

-- Grant permissions (assuming openleg_ingest user)
GRANT SELECT, INSERT ON master.audit_log TO openleg_ingest;
GRANT USAGE, EXECUTE ON SCHEMA master TO openleg_ingest;
GRANT EXECUTE ON FUNCTION master.log_audit_insert(), master.log_audit_update(), master.log_audit_delete() TO openleg_ingest;
