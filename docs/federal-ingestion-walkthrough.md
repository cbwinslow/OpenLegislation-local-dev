# Federal Data Ingestion Walkthrough: GovInfo API Integration

This manual provides a step-by-step procedure for repeating the GovInfo API ingestion process in OpenLegislation. It is designed for developers or users setting up the federal data pipeline locally or in production. The process is generalized, robust, and includes error handling, logging, and verification steps.

The ingestion uses the Java-based [`GovInfoApiProcessor`](src/main/java/gov/nysenate/openleg/processors/federal/GovInfoApiProcessor.java), which fetches data via API, parses JSON, maps to models (e.g., Bill), and persists to the database. Logs are detailed in `logs/ingestion-govinfo.log`.

## Prerequisites
- Java 21+ and Maven installed.
- PostgreSQL database set up (see [docs/db_connection.md](docs/db_connection.md)).
- API key from [api.data.gov](https://api.data.gov) for GovInfo (free, sign up required).
- Git clone of the repo: `git clone https://github.com/nysenate/OpenLegislation.git`.
- VS Code or IDE with Maven support.

**Estimated Time**: 30-60 minutes for initial setup; 5-10 minutes per run.

## Overall Process Diagram (Text-Based Flowchart)

```
+--------------------+     +---------------------+     +-------------------+
| 1. Obtain API Key  | --> | 2. Clone & Setup    | --> | 3. Configure API  |
| (api.data.gov)     |     | (git clone, configs)|     | (govinfo-api.prop)|
+--------------------+     +---------------------+     +-------------------+
          |                           |                           |
          v                           v                           v
+--------------------+     +---------------------+     +-------------------+
| 4. Build Project   | --> | 5. Run Script       | --> | 6. Verify Output  |
| (mvn clean compile)|     | (java -jar ... )    |     | (logs + DB query) |
+--------------------+     +---------------------+     +-------------------+
```

**Description**: The flowchart shows the linear steps. Arrows indicate sequence. Each box represents a major phase, with sub-steps detailed below.

## Step-by-Step Procedure

### Step 1: Obtain GovInfo API Key
1. Visit [api.data.gov](https://api.data.gov) and sign up/log in.
2. Search for "GovInfo API" and request access (approval is quick).
3. Copy your API key (e.g., `abc123def456`).

**Description**: The API key authenticates requests to GovInfo endpoints like `/v1/search?collection=BILLS`. Rate limits apply (1000 calls/day free tier).

**Diagram** (API Key Flow):
```
User --> api.data.gov (Sign Up/Login)
         |
         v
Search "GovInfo API" --> Request Access --> Get Key (Copy)
         |
         v
Paste into govinfo-api.properties
```

### Step 2: Clone and Setup the Repository
1. Clone the repo: `git clone https://github.com/nysenate/OpenLegislation.git`.
2. Navigate: `cd OpenLegislation`.
3. Copy example configs:
   - `cp src/main/resources/app.properties.local.example src/main/resources/app.properties.local` (for DB/ES config).
   - `cp src/main/resources/flyway.conf.example src/main/resources/flyway.conf` (for migrations).

**Description**: This sets up the project structure. Edit `app.properties.local` for local DB (e.g., `db.url=jdbc:postgresql://localhost:5432/openleg`).

**Diagram** (Repo Setup):
```
git clone https://github.com/nysenate/OpenLegislation.git
         |
         v
cd OpenLegislation
         |
         +--> cp app.properties.local.example --> Edit DB/ES settings
         |
         +--> cp flyway.conf.example --> Run mvn flyway:migrate (if needed)
```

### Step 3: Configure API and Logging
1. Edit `src/main/resources/govinfo-api.properties`:
   ```
   govinfo.api.key=your_api_key_here
   govinfo.api.base-url=https://api.govinfo.gov/v1
   govinfo.api.limit=50  # Max per page
   govinfo.api.retry-max=3
   govinfo.api.retry-delay-ms=1000
   ```
2. Ensure `src/main/resources/log4j2.xml` is configured for rolling logs in `./logs/ingestion-govinfo.log`.

**Description**: Properties make the process repeatable—change key/congress without code edits. Logging captures verbose details: timestamps, URLs fetched, records processed, errors (e.g., "Processed 25 bills, endpoint: /search?collection=BILLS").

**Diagram** (Config Edit):
```
Open govinfo-api.properties in Editor
         |
         +--> Line 1: govinfo.api.key = [paste key]
         |
         +--> Line 2: govinfo.api.base-url = https://api.govinfo.gov/v1
         |
         +--> Save & Close
```

### Step 4: Build the Project
1. Run: `mvn clean compile`.
   - This resolves dependencies (Jackson for JSON, Spring Web for RestTemplate, SLF4J/Log4j for logging).
   - If errors: Ensure Java 21 (`java -version`), Maven (`mvn -v`), and internet for downloads.
2. Verify: No compilation errors; `target/legislation-3.10.2.war` created.

**Description**: Builds the executable JAR/WAR. Includes JAXB for XML if needed later. Takes 1-2 minutes first time.

**Error Handling**: If deps fail (e.g., Guava/Jackson missing), check pom.xml and rerun.

**Diagram** (Build Process):
```
Terminal: mvn clean compile
         |
         +--> Clean target/ dir
         |
         +--> Download deps (e.g., com.fasterxml.jackson:jackson-databind:2.17.2)
         |
         +--> Compile sources --> Success: target/*.war ready
         |
         +--> Error? --> Check java -version (21+), mvn -v, internet
```

### Step 5: Run the Ingestion Script
1. Create logs dir: `mkdir logs`.
2. Run for bills (default):
   ```
   java -jar target/legislation-3.10.2.war GovInfoApiProcessor --congress=119
   ```
3. For other collections (e.g., laws):
   ```
   java -jar target/legislation-3.10.2.war GovInfoApiProcessor --congress=119 --collection=PLAW
   ```
   - Supported: BILLS (full), PLAW/CRPT/CREC (stubs—extend as needed).

**Description**: CLI parses args, fetches from API (e.g., https://api.govinfo.gov/v1/search?collection=BILLS&congress=119&limit=50), retries on failures (3x, backoff), parses JSON, maps to Bill/LawDocument, persists via DAO. Verbose console output; detailed file logs.

**CLI Args**:
- `--congress=119`: Required (e.g., 118 for 2023-2024).
- `--collection=BILLS`: Optional (default BILLS).

**Expected Output** (Console):
```
INFO GovInfoApiProcessor: Starting ingestion of bills for congress: 119
DEBUG GovInfoApiProcessor: Fetching from URL: https://api.govinfo.gov/v1/search?...
INFO GovInfoApiProcessor: Successfully processed 50 bills for congress 119
INFO GovInfoApiProcessor: Ingestion completed for congress 119: 50 bills ingested
```

**Diagram** (Run Flow):
```
java -jar target/legislation-3.10.2.war GovInfoApiProcessor --congress=119
         |
         +--> Parse args (congress=119, collection=BILLS)
         |
         +--> Build URL: https://api.govinfo.gov/v1/search?collection=BILLS&congress=119&api_key=...&limit=50
         |
         +--> Fetch (RestTemplate) --> Retry if fail (3x)
         |
         +--> Parse JSON (ObjectMapper) --> Map to Bill --> Persist (BillDao)
         |
         +--> Log: Console + ingestion-govinfo.log
```

**Error Handling**: 
- API error (invalid key): "ERROR: API returned error: Invalid key" → Check key.
- Rate limit (429): Auto-retries with delay.
- Network fail: Retries 3x, then throws exception (logged).

### Step 6: Verify Ingestion
1. Check logs: `tail -f logs/ingestion-govinfo.log` for details (e.g., "Processed bill HR1", errors).
2. Query DB (psql or tool):
   ```
   SELECT COUNT(*) FROM bills WHERE federal_congress = 119;
   SELECT print_no, title FROM bills WHERE federal_congress = 119 LIMIT 5;
   ```
   - Expect: 50+ rows for BILLS, federal_source='GovInfo API'.
3. API Test: If server running (`mvn tomcat7:run`), GET `/api/3/bills/2025/hr/1` (federal bills use session 2025).

**Description**: Confirms data persisted correctly. Logs include processed count, endpoints, timestamps for auditing.

**Diagram** (Verification):
```
Check Logs:
tail -f logs/ingestion-govinfo.log | grep "processed"
         |
         v
Query DB:
psql -d openleg -c "SELECT COUNT(*) FROM bills WHERE federal_congress=119;"
         |
         +--> Expect: 50 (or more)
         |
         +--> SELECT print_no, title ... LIMIT 5 --> Verify sample data
```

### Step 7: Repeat and Extend
- **Repeat**: Rerun with different congress/collection (e.g., `--congress=118 --collection=CRPT`). Incremental: Script appends/updates via DAO.
- **Extend**: Add models/DAOs for new collections (e.g., ReportDoc for CRPT). Update `processCollection()` switch. Test with unit tests.
- **Production**: Use cron: `0 2 * * * java -jar ... --congress=$(date +%y)-th --collection=BILLS` (daily deltas via RSS in future).
- **Troubleshooting**:
  - No data: Check API key/logs for "401 Unauthorized".
  - Build fail: `mvn dependency:resolve`.
  - DB errors: Ensure Flyway migrations run (`mvn flyway:migrate`).

**Diagram** (Repeat Cycle):
```
Successful Run --> Change args (e.g., --collection=PLAW) --> Rerun
         |                                      |
         +--> Check logs/DB --> OK? --> Yes: Done | No: Troubleshoot (key, net, DB)
```

**Generalization**: Config/CLI make it easy for any congress/collection. For bulk, add pagination (offset in URL).

## Web Page for Ease of Use
Create `src/main/webapp/federal-ingestion-guide.html` (served at http://localhost:8080/federal-ingestion-guide.html when Tomcat runs). This static page embeds the manual for browser access.

**Content for federal-ingestion-guide.html** (Create separately):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Federal Ingestion Guide</title>
    <style> body { font-family: Arial; } pre { background: #f4f4f4; padding: 10px; } </style>
</head>
<body>
    <h1>GovInfo Federal Data Ingestion Guide</h1>
    <p>Follow the steps in <a href="https://github.com/nysenate/OpenLegislation/blob/main/docs/federal-ingestion-walkthrough.md">docs/federal-ingestion-walkthrough.md</a>.</p>
    <h2>Quick Commands</h2>
    <pre>mvn clean compile
java -jar target/legislation-3.10.2.war GovInfoApiProcessor --congress=119</pre>
    <h2>Flow Diagram</h2>
    <pre>
+--------------------+     +---------------------+     +-------------------+
| 1. Obtain API Key  | --> | 2. Clone & Setup    | --> | 3. Configure API  |
+--------------------+     +---------------------+     +-------------------+
          |                           |                           |
          v                           v                           v
+--------------------+     +---------------------+     +-------------------+
| 4. Build Project   | --> | 5. Run Script       | --> | 6. Verify Output  |
+--------------------+     +---------------------+     +-------------------+
    </pre>
    <p>For full details, see the Markdown manual.</p>
</body>
</html>
```

Update [README.md](README.md): Add "Federal Ingestion: Run Tomcat (`mvn tomcat7:run`) and visit [http://localhost:8080/federal-ingestion-guide.html](http://localhost:8080/federal-ingestion-guide.html) for interactive guide."

This process is robust, logged, and repeatable. For issues, check logs or open GitHub issue.