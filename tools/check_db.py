#!/usr/bin/env python3
"""Simple DB connectivity checker using settings."""
import sys
from settings import settings
import psycopg2

try:
    cfg = settings.db_config
    conn = psycopg2.connect(**cfg)
    conn.close()
    print("DB_OK")
    sys.exit(0)
except Exception as e:
    print(f"DB_ERROR: {e}")
    sys.exit(1)
