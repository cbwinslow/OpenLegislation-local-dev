# Data Ingestion Guidance for OpenLegislation Project

## 1. Adapting Codebase and SQL Schema to Java Classes

The existing codebase is Java-based (Maven via [`pom.xml`](pom.xml)), with SQL schema managed by Flyway migrations in [`src/main/resources/sql/migrations`](src/main/resources/sql/migrations). To align with Java classes for seamless data ingestion:

### Step-by-Step Recommendations:
1. **Inventory Existing Entities**: Review Java entities (e.g., in `src/main/java/gov/nysenate/openleg/model`—assume standard structure from project). Map SQL tables (e.g., bills, members from migrations like [`V20250921.0003__universal_bill_schema.sql`](src/main/resources/sql/migrations/V20250921.0003__universal_bill_schema.sql)) to JPA entities. Use tools like IntelliJ's database diagrammer or Liquibase for visualization.

2. **ORM Mapping with Hibernate/JPA**:
   - Add Hibernate dependency if not present: In [`pom.xml`](pom.xml), ensure `<dependency><groupId>org.hibernate</groupId><artifactId>hibernate-core</artifactId><version>6.4.0.Final</version></dependency>`.
   - Annotate entities with `@Entity`, `@Table`, `@Id`, `@Column` for direct SQL-to-Java mapping. Example for a Bill entity:
     ```java
     @Entity
     @Table(name = "bills")
     public class Bill {
         @Id
         @GeneratedValue(strategy = GenerationType.IDENTITY)
         private Long id;
         @Column(name = "bill_id")
         private String billId;
         // Add fields matching schema, e.g., @OneToMany for amendments
     }
     ```
   - Configure in `persistence.xml` or Spring Boot `application.properties`: `spring.jpa.hibernate.ddl-auto=validate` for schema validation.

3. **Schema Migrations with Flyway**:
   - Extend existing Flyway setup (already in use). Create new migration scripts for federal/legislation fields, e.g., `V20250925.0002__add_legislation_source.sql` to add columns like `source_url`, `ingestion_timestamp`.
   - Best practice: Versioned, repeatable migrations. Test with `flyway migrate -configFiles=src/main/resources/flyway.conf` in CI/CD.

4. **ETL Processes**:
   - Use Spring Batch for ingestion jobs: Define `ItemReader` (e.g., JDBC for SQL), `ItemProcessor` (transformations like date formatting, null handling), `ItemWriter` (JPA repositories).
   - Transformations: Map disparate sources (e.g., XML to JSON) using Jackson or JAXB (already in project from [`jaxb-setup.md`](docs/jaxb-setup.md)).
   - Minimize disruptions: Run migrations in blue-green deployments; use feature flags for new fields.

5. **Best Practices**:
   - Immutable data: Use audit columns (`created_at`, `updated_at`) in entities.
   - Idempotency: Check for existing records via unique constraints before insert.
   - Testing: Integrate with [`IngestionIntegrationIT.java`](src/test/java/gov/nysenate/openleg/IngestionIntegrationIT.java) for ETL validation.
   - Tools: Hibernate for ORM, Flyway for migrations, Spring Data JPA for repositories.

## 2. Alternative Legislation Resources

Beyond current sources (e.g., Congress.gov integration in [`docs/congress_gov_integration.md`](docs/congress_gov_integration.md)):

- **Recommended: EU Legislation Portal (EUR-Lex)** (https://eur-lex.europa.eu):
  - **Accessibility**: Free API (SPARQL endpoint for RDF data), bulk downloads via OAI-PMH.
  - **Update Frequency**: Daily updates for new directives/regulations.
  - **Integration Feasibility**: High—XML/JSON formats align with USLM schema ([`docs/uslm-bill.xsd`](docs/uslm-bill.xsd)). Use REST API for queries (e.g., `/api/legislation/{id}`). Map to Java entities via JAXB. Ethical/legal: Public domain EU law.
  - Pros: Comprehensive EU/international coverage; multilingual.
  - Cons: Focus on EU, requires schema adaptations for non-US data.

Other options: WorldLII (worldlii.org) for global laws, but EUR-Lex is most reliable for structured data.

## 3. WikiLeaks Integration Feasibility

- **Feasibility Assessment**:
  - No official API; data via website scraping (RSS feeds at https://wikileaks.org/feed.xml) or torrent downloads (e.g., Vault 7).
  - Direct integration: Possible via periodic scraping (respect robots.txt—WikiLeaks allows non-commercial). Use Python/Scrapy for RSS parsing, but Java equivalent with Jsoup.
  - Formats: PDFs, text, ZIP archives with metadata (JSON/XML excerpts).
  - Value for Project: Exposes classified docs on legislation/policy; useful for transparency analysis, but niche for OpenLegislation (focus on public laws).

- **Sample Dataset Structure** (Illustrative, based on public examples—no direct fetch to avoid restrictions):
  - Document: "Cablegate" (e.g., 2010 diplomatic cables).
    - Metadata: `{ "id": "10STATE123", "date": "2010-01-01", "title": "Classified Cable Summary", "source": "US Embassy", "classification": "SECRET" }`
    - Content: PDF (encrypted excerpts) or TXT: "Summary: Legislative reform in [country]..."
    - Structure: Hierarchical folders (e.g., /releases/cablegate/2010/01/10STATE123.pdf), with RSS: `<item><title>Cable ID</title><link>https://wikileaks.org/cable/...</link><pubDate>2010-01-01</pubDate></item>`.
  - Potential: Extract text for keyword search on "legislation"; store metadata in DB.

- **Restrictions**:
  - **Legal/Ethical**: Public domain, but verify no copyrighted material. US/EU laws allow fair use for research; avoid redistribution of sensitive info.
  - **Technical**: Rate limiting (use delays); no auth needed. Ethical: Cite sources; don't automate aggressively to avoid DoS.
  - Recommendation: Use RSS for new docs only; manual review for ingestion.

## 4. Scalable FastAPI-Based System Design

Design for document ingestion/processing. (Pseudocode; delegate full impl to code mode if needed.)

### Schemas (Pydantic Models):
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class DocumentIngestSchema(BaseModel):
    file_id: Optional[str] = None
    source_url: str
    metadata: Dict[str, Any]  # e.g., {"source": "wikileaks", "date": "2025-01-01"}
    extracted_text: Optional[str] = None

class DocumentResponseSchema(BaseModel):
    doc_id: str
    status: str  # "ingested", "processing", "error"
    analysis_results: Optional[Dict[str, Any]] = None  # e.g., {"keywords": ["legislation"]}

class JobStatusSchema(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed"
    progress: float
```

### Endpoints:
- **POST /ingest**: Trigger ingestion.
  ```python
  from fastapi import FastAPI, UploadFile, Depends
  from fastapi.security import HTTPBearer
  app = FastAPI()
  security = HTTPBearer()  # JWT/API key

  @app.post("/ingest", response_model=DocumentResponseSchema)
  async def ingest_doc(schema: DocumentIngestSchema, token: str = Depends(security)):
      # Validate auth, upload to S3, queue job (e.g., Celery)
      job_id = queue_ingestion(schema)
      return {"doc_id": job_id, "status": "queued"}
  ```
- **GET /documents/{doc_id}**: Retrieve details.
  ```python
  @app.get("/documents/{doc_id}", response_model=DocumentResponseSchema)
  async def get_doc(doc_id: str, token: str = Depends(security)):
      # Fetch from DB/S3
      return db.get_document(doc_id)
  ```
- **POST /scan**: Trigger WikiLeaks scan.
  ```python
  @app.post("/scan")
  async def scan_wikileaks(token: str = Depends(security)):
      # Parse RSS, detect new docs, trigger ingest
      new_docs = parse_rss("https://wikileaks.org/feed.xml")
      return {"scanned": len(new_docs), "new": len(new_docs)}
  ```
- **GET /status/{job_id}**: Job status.
  ```python
  @app.get("/status/{job_id}", response_model=JobStatusSchema)
  async def get_status(job_id: str):
      return job_queue.status(job_id)
  ```

- **Authentication**: JWT via `python-jose` or API keys in headers. Use FastAPI's `OAuth2PasswordBearer`.
- **Error Handling**: Global exception handlers: `@app.exception_handler(HTTPException)`. Return JSON errors with codes (e.g., 429 for rate limit).
- **Rate Limiting**: Use `slowapi`: `@limiter.limit("5/minute")`.
- **Logging**: `logging` module with structlog; integrate ELK stack.

Deploy: Dockerize, Kubernetes for scaling; CI/CD via GitHub Actions ([`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml)).

## 5. Storage and Automated Workflow

- **Storage**: AWS S3 (primary) or Cloudflare R2 (cost-effective alternative to D2). Buckets: `raw-documents` (PDFs), `processed` (JSON). Use IAM roles—no hard-coded keys.
  - Config: Env vars `AWS_ACCESS_KEY_ID` from secrets manager (AWS SSM or Doppler).

- **Automated Workflow**:
  1. **Trigger**: Event-driven (S3 Event Notifications to Lambda) or cron (every 30min via env `SCAN_INTERVAL=30`).
     - Pseudocode (Lambda/Python):
       ```python
       import boto3, requests, schedule, time
       s3 = boto3.client('s3')

       def scan_wikileaks():
           rss = requests.get("https://wikileaks.org/feed.xml")
           new_docs = parse_rss(rss.content)  # Filter by date
           for doc in new_docs:
               url = doc['link']
               pdf_content = requests.get(url).content
               s3_key = f"raw/{doc['id']}.pdf"
               s3.put_object(Bucket='openleg-raw', Key=s3_key, Body=pdf_content)
               # Trigger Lambda for processing

       # Cron: schedule.every(30).minutes.do(scan_wikileaks)
       # Or Lambda cron via EventBridge
       ```
  2. **Download/Upload**: As above; use `boto3` for S3.
  3. **OCR Processing**: AWS Textract (managed, accurate for PDFs).
     - Pseudocode:
       ```python
       textract = boto3.client('textract')
       def ocr_pipeline(s3_key):
           response = textract.detect_document_text(Document={'S3Object': {'Bucket': 'openleg-raw', 'Name': s3_key}})
           text = ' '.join([block['Text'] for block in response['Blocks'] if block['BlockType'] == 'LINE'])
           json_data = {"text": text, "metadata": extract_metadata(text)}
           s3.put_object(Bucket='openleg-processed', Key=f"{s3_key}.json", Body=json.dumps(json_data))
           return json_data
       ```
     - Alternatives: Tesseract (open-source, local) or Google Vision (if multi-cloud).
  4. **Ingestion to SQL**: Map JSON to Java entities via ETL (Spring Batch). Store S3 URL in DB (e.g., `document_url` column).
     - Pseudocode (Java):
       ```java
       @Service
       public class IngestionService {
           @Autowired private DocumentRepository repo;
           public void ingest(String s3Url, String text) {
               Document doc = new Document();
               doc.setSourceUrl(s3Url);
               doc.setExtractedText(text);
               repo.save(doc);  // JPA persists to Postgres
           }
       }
       ```

- **Best Practices**: Idempotent (check hashes), dead-letter queues for failures, monitoring (CloudWatch).

## 6. Database Options Evaluation

- **Stick with PostgreSQL** (current, from schema docs):
  - Pros: ACID compliance, JSONB for unstructured metadata/text, full-text search (tsvector for legislation queries), scales vertically/horizontally (read replicas).
  - Cons: Less flexible for high-volume semi-structured data; ingestion bottlenecks under extreme load.
  - Migration: None needed; extend schema with Flyway.

- **Migrate to NoSQL (MongoDB for metadata/text)**:
  - Pros: Schema-less for variable doc structures, horizontal scaling, built-in text indexing.
  - Cons: No transactions across docs, query complexity vs SQL joins; Java driver overhead.
  - Strategy: Dual-write during migration; use Change Data Capture (Debezium) to sync Postgres to Mongo.

- **Cassandra for High-Volume**:
  - Pros: Distributed, high write throughput for ingestion logs.
  - Cons: NoSQL query limits; not ideal for complex joins.

- **Hybrid Approach (Recommended)**: Postgres for structured (bills/members), MongoDB for unstructured (extracted text/metadata).
  - Pros: Best of both—relational integrity + flexibility. Compatibility: Use Spring Data MongoDB alongside JPA.
  - Cons: Dual maintenance; sync via Kafka.
  - Strategy:
    1. Provision MongoDB (AWS DocumentDB or Atlas).
    2. Migrate: ETL script to export Postgres JSON fields to Mongo collections.
    3. Java: `@Repository` for both (e.g., `MongoTemplate` for docs).
    4. Hybrid Query: App-level joins or Elasticsearch for unified search.

Ensure Java backend compatibility via multi-module Maven setup.
