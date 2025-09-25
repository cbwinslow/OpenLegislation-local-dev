"""
Database configuration for connecting to remote Ubuntu server PostgreSQL instance.
Tailscale IP: 100.90.23.59
DB: opendiscourse (from prior context)
User: opendiscourse
Pass: opendiscourse123 (CHANGE IN PRODUCTION!)

Usage in scripts:
    from db_config import get_connection_string
    conn_string = get_connection_string()
    # Then: import psycopg2; conn = psycopg2.connect(conn_string)

For security: Set env vars (DB_HOST, DB_NAME, DB_USER, DB_PASS) to override.
Remote access: Ensure Tailscale is connected; server allows connections from your IP.
"""

import os

# Default config
DB_HOST = os.getenv('DB_HOST', '100.90.23.59')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'opendiscourse')
DB_USER = os.getenv('DB_USER', 'opendiscourse')
DB_PASS = os.getenv('DB_PASS', 'opendiscourse123')

def get_connection_string():
    """Return PostgreSQL URI connection string."""
    return f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_connection_params():
    """Return dict for psycopg2.connect()."""
    return {
        'host': DB_HOST,
        'port': DB_PORT,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASS
    }

# Example usage (test connection)
if __name__ == "__main__":
    print("DB Config:")
    print(f"Host: {DB_HOST}")
    print(f"DB: {DB_NAME}")
    print("Connection String (masked):", get_connection_string().replace(DB_PASS, '***'))
    print("\nTo test: pip install psycopg2; then in Python:")
    print("import psycopg2")
    print("from db_config import get_connection_params")
    print("conn = psycopg2.connect(**get_connection_params())")
    print("cur = conn.cursor(); cur.execute('SELECT 1'); print('Connected!')")