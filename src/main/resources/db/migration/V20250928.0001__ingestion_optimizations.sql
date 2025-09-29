-- Migration: Add missing indexes and optimizations for federal ingestion
-- Ensures proper indexing for high-volume queries and performance

-- Add missing indexes for govinfo tables in public schema (only for existing columns)
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_congress_number ON public.govinfo_bill (congress, bill_number);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_latest_action_date ON public.govinfo_bill (latest_action_date);
CREATE INDEX IF NOT EXISTS idx_govinfo_bill_sponsor_party ON public.govinfo_bill (sponsor_party);

-- Indexes for govinfo actions (frequent range queries) - check if columns exist first
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'govinfo_bill_action' AND column_name = 'action_date') THEN
        CREATE INDEX IF NOT EXISTS idx_govinfo_action_date ON public.govinfo_bill_action (action_date);
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'govinfo_bill_action' AND column_name = 'sequence_no') THEN
        CREATE INDEX IF NOT EXISTS idx_govinfo_action_sequence ON public.govinfo_bill_action (sequence_no);
    END IF;
END $$;

-- Indexes for govinfo cosponsors - check if columns exist first
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'govinfo_bill_cosponsor' AND column_name = 'sponsor_name') THEN
        CREATE INDEX IF NOT EXISTS idx_govinfo_cosponsor_name ON public.govinfo_bill_cosponsor (sponsor_name);
    END IF;
END $$;

-- Committee indexes for govinfo data - check if columns exist first
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'govinfo_bill_committee' AND column_name = 'committee_name') THEN
        CREATE INDEX IF NOT EXISTS idx_govinfo_committee_name ON public.govinfo_bill_committee (committee_name);
    END IF;
END $$;

-- Add check constraints for data integrity (federal-specific) - only if not already present
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.check_constraints WHERE constraint_name = 'chk_govinfo_bill_federal_congress') THEN
        ALTER TABLE public.govinfo_bill ADD CONSTRAINT chk_govinfo_bill_federal_congress
        CHECK (congress IS NOT NULL AND congress > 0);
    END IF;
END $$;

-- Add updated_at trigger if not present (for govinfo tables)
CREATE OR REPLACE FUNCTION public.update_govinfo_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_date_time = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.triggers WHERE trigger_name = 'update_govinfo_bill_updated_at') THEN
        CREATE TRIGGER update_govinfo_bill_updated_at BEFORE UPDATE
        ON public.govinfo_bill FOR EACH ROW EXECUTE FUNCTION public.update_govinfo_updated_at_column();
    END IF;
END $$;

-- Ensure vector extension for embeddings (if not enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Validation: Add a view for ingestion stats (only if modified_date_time column exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'govinfo_bill' AND column_name = 'modified_date_time') THEN
        CREATE OR REPLACE VIEW public.govinfo_ingestion_stats AS
        SELECT
            'govinfo' as data_source,
            COUNT(*) as total_records,
            COUNT(CASE WHEN sponsor_party IS NOT NULL THEN 1 END) as with_sponsor_info,
            AVG(EXTRACT(EPOCH FROM (modified_date_time - introduced_date))) as avg_age_days
        FROM public.govinfo_bill;
    END IF;
END $$;

-- Create unified ingestion stats view combining master and public schemas
CREATE OR REPLACE VIEW master.unified_ingestion_stats AS
SELECT * FROM master.ingestion_stats
UNION ALL
SELECT * FROM public.govinfo_ingestion_stats;

-- Comment for audit
COMMENT ON SCHEMA public IS 'Public schema containing govinfo federal data tables with performance optimizations';