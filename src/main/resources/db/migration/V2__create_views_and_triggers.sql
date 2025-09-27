-- V2__create_views_and_triggers.sql

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to update the updated_at timestamp on the bills table
CREATE TRIGGER update_bills_updated_at
BEFORE UPDATE ON bills
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create a trigger to update the updated_at timestamp on the amendments table
CREATE TRIGGER update_amendments_updated_at
BEFORE UPDATE ON amendments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Create a view for bills with their primary sponsor
CREATE VIEW bills_with_sponsors AS
SELECT
    b.*,
    s.full_name AS sponsor_name
FROM
    bills b
JOIN
    bill_sponsors bs ON b.id = bs.bill_id
JOIN
    sponsors s ON bs.sponsor_id = s.id
WHERE
    bs.is_primary = TRUE;

-- Create a view for the most recent amendment for each bill
CREATE VIEW latest_amendments AS
SELECT
    a.*
FROM
    amendments a
INNER JOIN (
    SELECT
        bill_id,
        MAX(version) AS max_version
    FROM
        amendments
    GROUP BY
        bill_id
) AS latest ON a.bill_id = latest.bill_id AND a.version = latest.max_version;

-- Add indexes for foreign keys to improve join performance
CREATE INDEX idx_amendments_bill_id ON amendments(bill_id);
CREATE INDEX idx_actions_bill_id ON actions(bill_id);
CREATE INDEX idx_bill_sponsors_bill_id ON bill_sponsors(bill_id);
CREATE INDEX idx_bill_sponsors_sponsor_id ON bill_sponsors(sponsor_id);
CREATE INDEX idx_bill_committees_bill_id ON bill_committees(bill_id);
CREATE INDEX idx_bill_committees_committee_id ON bill_committees(committee_id);
CREATE INDEX idx_votes_amendment_id ON votes(amendment_id);
CREATE INDEX idx_related_bills_related_bill_id ON related_bills(related_bill_id);
CREATE INDEX idx_laws_bill_id ON laws(bill_id);
CREATE INDEX idx_govinfo_metadata_bill_id ON govinfo_metadata(bill_id);