# Local Development Quickstart

This file contains quick steps to configure local environment variables and test the Postgres connection used by the project.

1) Copy `.gitconfig.example` to your home gitconfig or set repo-local config (already applied):

```bash
cp .gitconfig.example ~/.gitconfig
# or for repo-local only:
git config user.name "cbwinslow"
git config user.email "blaine.winslow@gmail.com"
```

2) Create a `.env` in the repo root (a template `.env` is included). DO NOT commit real secrets.

```bash
cp .env .env.local
# edit .env.local to match your local credentials
```

3) Export env vars (or rely on `app.properties.local`):

```bash
export $(egrep -v '^#' .env | xargs)
```

4) Test connectivity using `psql` or `pg_isready` as described in `docs/db_connection.md`.

5) To run the app with the local JDBC URL override:

```bash
mvn -Djdbc.url="$JDBC_DATABASE_URL" -DskipTests=true -pl :legislation:war -am tomcat7:run
```
