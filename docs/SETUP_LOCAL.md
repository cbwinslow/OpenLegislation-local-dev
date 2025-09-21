# Local Setup and Run Instructions

This file gives concise steps to prepare a Linux development machine (zsh) to build and run OpenLegislation locally.

Prerequisites

* Java 17 JDK
* Apache Maven
* Node.js and npm (for building web assets)
* PostgreSQL (for running the app locally)

Install on Debian/Ubuntu

    # Install OpenJDK 17
    sudo apt update
    sudo apt install -y openjdk-17-jdk

    # Install Maven
    sudo apt install -y maven

    # Install Node.js + npm (Node 18 LTS recommended)
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs

    # Optional: install PostgreSQL if you need a local DB
    sudo apt install -y postgresql postgresql-contrib

macOS (Homebrew)

    brew install openjdk@17 maven node postgresql

Quickstart: build and run

1. Copy env template and set values

    cp .env.example .env
    # edit .env to set real values
    export $(egrep -v '^#' .env | xargs)

2. Optionally copy `app.properties.local` to `src/main/resources/app.properties.local` and adjust values (it already exists as a template in `src/main/resources`).

3. Build (skip tests for first run if you don't have a DB):

    mvn -DskipTests=true compile

4. Build full WAR and run via embedded Tomcat during development (example):

    # Run the webapp module with maven (this will also run `npm ci` in the webapp directory)
    mvn -Djdbc.url="$JDBC_DATABASE_URL" -DskipTests=true -pl :legislation:war -am tomcat7:run

Notes and troubleshooting

* If `mvn` is not found, ensure Maven is installed and on your `PATH`.
* Node/npm must be available so the build can run `npm ci` in `src/main/webapp`.
* Some dependencies may be hosted in an internal NY Senate Maven repository (`https://dev.nysenate.gov/maven/repo`). If you encounter errors resolving artifacts, you may need credentials or to mirror those artifacts to a local repository.
* For running integration tests or the app against a database, ensure PostgreSQL is configured and reachable using the settings from `.env` / `app.properties.local`.

If you want, I can try running `mvn -DskipTests=true compile` here after you confirm it's OK for me to attempt (I will check for `mvn`, `java`, and `node` first and report the results).
