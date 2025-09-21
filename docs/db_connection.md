# Database Connection & Quick Test Guide

This document describes how to use the example `.env` and `app.properties.local` files added to the repository and how to quickly test connectivity to a Postgres instance (example Zerotier host `172.28.208.142:5433`).

Files added:
- `.env` (repo root): contains `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, and `JDBC_DATABASE_URL` for local convenience.
- `src/main/resources/app.properties.local`: local Java properties file that reads from the same values. Copy or configure this file for local runs.

Security note: Do not commit real secrets. `.env` is intended for local development only and should be added to your personal `~/.gitignore` or the repo-level ignore if you choose.

Quick test commands (run from a developer machine with `psql` installed):

1) Test TCP reachability with `pg_isready` (if available):

```bash
PGHOST=172.28.208.142 PGPORT=5433 pg_isready -h $PGHOST -p $PGPORT
```

2) Test a CLI connection with `psql` using env vars:

```bash
export PGHOST=172.28.208.142
export PGPORT=5433
export PGUSER=opendiscourse
export PGPASSWORD=opendiscourse123
export PGDATABASE=openleg

psql
# or explicitly:
psql "postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PGDATABASE"
```

3) Test JDBC connectivity (for Java apps):

Use the JDBC URL shown in `src/main/resources/app.properties.local` or the `JDBC_DATABASE_URL` from `.env`:

```bash
JDBC_DATABASE_URL=jdbc:postgresql://172.28.208.142:5433/openleg

# Example: run mvn with system property
mvn -Djdbc.url="$JDBC_DATABASE_URL" test
```

If you cannot reach the host, confirm your Zerotier membership and routing to `172.28.208.142` and that the remote machine's firewall allows connections on port `5433`.
