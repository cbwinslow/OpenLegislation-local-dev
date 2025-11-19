-- Create audit log table
CREATE TABLE IF NOT EXISTS master.audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    row_id TEXT, -- Identifier for the row (e.g., PK as string)
    old_values JSONB,
    new_values JSONB,
    changed_by TEXT DEFAULT current_user,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit_log
CREATE INDEX idx_audit_log_table_operation ON master.audit_log(table_name, operation);
CREATE INDEX idx_audit_log_changed_at ON master.audit_log(changed_at);

-- Function to log changes (PL/pgSQL)
CREATE OR REPLACE FUNCTION master.audit_trigger() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO master.audit_log (table_name, operation, row_id, old_values, new_values)
        VALUES (TG_RELNAME, 'DELETE', row_to_json(OLD)::text, row_to_json(OLD), NULL);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO master.audit_log (table_name, operation, row_id, old_values, new_values)
        VALUES (TG_RELNAME, 'UPDATE', row_to_json(NEW)::text, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO master.audit_log (table_name, operation, row_id, old_values, new_values)
        VALUES (TG_RELNAME, 'INSERT', row_to_json(NEW)::text, NULL, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to key tables
CREATE TRIGGER audit_bill_trigger AFTER INSERT OR UPDATE OR DELETE ON master.bill FOR EACH ROW EXECUTE FUNCTION master.audit_trigger();
CREATE TRIGGER audit_federal_person_trigger AFTER INSERT OR UPDATE OR DELETE ON master.federal_person FOR EACH ROW EXECUTE FUNCTION master.audit_trigger();
CREATE TRIGGER audit_federal_member_trigger AFTER INSERT OR UPDATE OR DELETE ON master.federal_member FOR EACH ROW EXECUTE FUNCTION master.audit_trigger();
CREATE TRIGGER audit_federal_member_term_trigger AFTER INSERT OR UPDATE OR DELETE ON master.federal_member_term FOR EACH ROW EXECUTE FUNCTION master.audit_trigger();
CREATE TRIGGER audit_bill_action_trigger AFTER INSERT OR UPDATE OR DELETE ON master.bill_amendment_action FOR EACH ROW EXECUTE FUNCTION master.audit_trigger();
CREATE TRIGGER audit_bill_sponsor_trigger AFTER INSERT OR UPDATE OR DELETE ON master.bill_sponsor FOR EACH ROW EXECUTE FUNCTION master.audit_trigger();

-- Add any missing updated_at triggers for timestamps
CREATE OR REPLACE FUNCTION master.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_federal_person_updated_at BEFORE UPDATE ON master.federal_person FOR EACH ROW EXECUTE PROCEDURE master.update_updated_at_column();
CREATE TRIGGER update_federal_member_updated_at BEFORE UPDATE ON master.federal_member FOR EACH ROW EXECUTE PROCEDURE master.update_updated_at_column();
CREATE TRIGGER update_bill_updated_at BEFORE UPDATE ON master.bill FOR EACH ROW EXECUTE PROCEDURE master.update_updated_at_column();
