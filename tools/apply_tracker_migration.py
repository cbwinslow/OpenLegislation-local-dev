#!/usr/bin/env python3
"""Apply minimal tracker migration to create master.ingestion_status and helper function.

This script is idempotent and intended for local dev to ensure the ingestion tracker table
exists so the Python tools can run smoke tests without requiring full Flyway migrations.
"""
import sys
from settings import settings
import psycopg2

SCHEMA_SQL = "CREATE SCHEMA IF NOT EXISTS master;"

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS master.ingestion_status (
  id BIGSERIAL PRIMARY KEY,
  table_name TEXT NOT NULL,
  record_id TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'unknown',
  ingestion_status TEXT NOT NULL CHECK (ingestion_status IN ('pending','in_progress','completed','failed')),
  last_attempted_at TIMESTAMP,
  completed_at TIMESTAMP,
  failure_reason TEXT,
  retry_count INTEGER DEFAULT 0,
  processing_priority INTEGER DEFAULT 0,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  ingestion_session_id TEXT,
  UNIQUE (table_name, record_id, source)
);
"""

INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_ingestion_status_table_record ON master.ingestion_status (table_name, record_id, source);",
    "CREATE INDEX IF NOT EXISTS idx_ingestion_status_status ON master.ingestion_status (ingestion_status);",
    "CREATE INDEX IF NOT EXISTS idx_ingestion_status_session ON master.ingestion_status (ingestion_session_id);",
    "CREATE INDEX IF NOT EXISTS idx_ingestion_status_source ON master.ingestion_status (source);",
]

NOOP_FN_SQL = """
CREATE OR REPLACE FUNCTION master.log_member_updates()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RETURN NEW;
END;
$$;
"""

TRIGGER_DO_SQL = """
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'log_ingestion_updates_to_change_log') THEN
    EXECUTE 'CREATE TRIGGER log_ingestion_updates_to_change_log BEFORE INSERT OR DELETE OR UPDATE ON master.ingestion_status FOR EACH ROW EXECUTE PROCEDURE master.log_member_updates()';
  END IF;
END
$$;
"""


def apply_migration():
    cfg = settings.db_config
    try:
        conn = psycopg2.connect(**cfg)
        cur = conn.cursor()
        print("Applying tracker migration to database:", cfg.get('database'))

        # Execute blocks separately to avoid multi-statement parsing edge cases
        cur.execute(SCHEMA_SQL)
        cur.execute(TABLE_SQL)
        for idx_sql in INDEXES_SQL:
            cur.execute(idx_sql)

        # Create noop function and trigger if possible
        try:
            cur.execute(NOOP_FN_SQL)
            cur.execute(TRIGGER_DO_SQL)
        except Exception as te:
            print("Warning applying trigger/function SQL:", te)

        conn.commit()
        print("Migration applied (idempotent)")
        cur.close()
        conn.close()

    except Exception as e:
        print("Failed to apply migration:", e)
        sys.exit(1)


if __name__ == '__main__':
    apply_migration()
