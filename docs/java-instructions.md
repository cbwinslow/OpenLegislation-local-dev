# Java Instructions for Federal Data Ingestion

The existing Java codebase provides a solid foundation for ingesting and exporting (i.e., persisting) data to a SQL database using Spring Data JPA, Hibernate, and PostgreSQL. It's primarily structured around a service-DAO pattern for handling updates, notifications, and spotchecks, with a generic ingestion mechanism in [`IngestionService.java`](src/main/java/gov/nysenate/openleg/service/ingestion/IngestionService.java). This service already demonstrates how to fetch data from external sources (e.g., RSS feeds or APIs via RestTemplate), parse it, map it to JPA entities, and save it to the database using a repository. The setup uses PostgreSQL as the backend (configured via Flyway migrations and C3P0 connection pooling, as seen in [`pom.xml`](pom.xml)), with entities like [`Document.java`](src/main/java/gov/nysenate/openleg/model/document/Document.java) mapped to tables.

However, the Java codebase focuses more on NY State legislation processing (e.g., bills, agendas, calendars via spotchecks and updates in packages like `gov.nysenate.openleg.spotchecks` and `gov.nysenate.openleg.updates`). Federal ingestion (e.g., Congress.gov or GovInfo) isn't directly implemented in Java here—instead, the workspace leans on Python scripts in `tools/` (e.g., [`ingest_congress_api.py`](tools/ingest_congress_api.py), [`govinfo_bill_ingestion.py`](tools/govinfo_bill_ingestion.py)) for ETL tasks, which likely connect to the same PostgreSQL DB via SQLAlchemy (see `src/db/` Python modules). That said, you *can* leverage the Java architecture without reinventing the wheel by extending the existing patterns for federal data. Below, I'll explain how, step by step.

## 1. Understand the Existing Architecture
- **Entities (Models)**: JPA-annotated classes (e.g., `@Entity` in [`Document.java`](src/main/java/gov/nysenate/openleg/model/document/Document.java)) define the schema. Fields map to DB columns (e.g., `@Column`, `@Id`). Metadata can be stored as JSONB for flexibility.
- **Repositories (DAOs)**: Extend `JpaRepository` (e.g., [`DocumentRepository.java`](src/main/java/gov/nysenate/openleg/dao/document/DocumentRepository.java)) for CRUD ops like `saveAll()`, `existsByUrl()`, and custom queries via `@Query`.
- **Services**: Business logic layer (e.g., [`IngestionService.java`](src/main/java/gov/nysenate/openleg/service/ingestion/IngestionService.java)) handles fetching (RestTemplate for APIs, Rome for RSS), filtering duplicates, mapping to entities, and persisting via repositories. It's transactional (`@Transactional`) and schedulable (`@Scheduled`).
- **Database Setup**: 
  - PostgreSQL driver and Hibernate ORM in [`pom.xml`](pom.xml).
  - Flyway plugin runs migrations (e.g., from `src/main/resources/db/migration/` like [`V20250928.0001__ingestion_optimizations.sql`](src/main/resources/db/migration/V20250928.0001__ingestion_optimizations.sql)) during build/integration tests.
  - Connection config likely in `application.properties` or `flyway.conf` (not visible; check `src/main/resources/`).
- **Build/Run**: Maven-based (`mvn clean install` compiles, runs tests, generates JAXB classes from XSDs like USLM schemas in `docs/uslm-bill.xsd`). Deploys as WAR to Tomcat (plugin in [`pom.xml`](pom.xml)).
- **Key Dependencies for Ingestion**:
  - `spring-data-jpa` for repositories.
  - `spring-web` for RestTemplate (HTTP clients).
  - `rome` for RSS/XML parsing.
  - `jackson` for JSON (e.g., Congress.gov API).
  - `hibernate-core` for ORM.

This setup is extensible—it's not hardcoded to NY data, so you can add federal-specific entities/services.

## 2. Leveraging for Federal Data Export to SQL
To ingest federal data (e.g., bills from Congress.gov API or GovInfo bulk XML/JSON) into PostgreSQL, extend the patterns from `IngestionService`. Avoid Python if you want pure Java; integrate with existing update events (e.g., `BillUpdateEvent` in `gov.nysenate.openleg.updates.bill`) for consistency.

### Step 2.1: Define Federal-Specific JPA Entities
Create entities mirroring federal schemas (e.g., from GovInfo USLM or Congress.gov JSON). Start with a `FederalBill` entity, similar to `Document`.

Example: Create `src/main/java/gov/nysenate/openleg/model/federal/bill/FederalBill.java`:
```java
package gov.nysenate.openleg.model.federal.bill;

import gov.nysenate.openleg.model.BaseObject;  // If exists, or use java.time
import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "federal_bills", schema = "public")  // Or your schema
public class FederalBill {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "congress_number", nullable = false)
    private Integer congress;  // e.g., 118

    @Column(name = "bill_type", nullable = false)  // e.g., "hr", "s"
    private String type;

    @Column(name = "number", nullable = false)
    private Integer number;

    @Column(name = "title")
    private String title;

    @Column(name = "summary", columnDefinition = "TEXT")
    private String summary;

    @Column(name = "status")  // e.g., "introduced", "passed"
    private String status;

    @Column(name = "introduced_date")
    private LocalDateTime introducedDate;

    @Column(name = "sponsor_id")
    private String sponsor;  // Link to member

    @Column(name = "text_content", columnDefinition = "TEXT")
    private String fullText;  // Parsed from XML/PDF

    @Column(name = "metadata", columnDefinition = "JSONB")  // Full API response
    private String metadata;

    @Column(name = "source_url", unique = true)
    private String sourceUrl;  // Congress.gov URL for idempotency

    @Column(name = "ingested_at", nullable = false)
    private LocalDateTime ingestedAt = LocalDateTime.now();

    // Constructors, getters, setters (similar to Document.java)
    // toString() for logging
}
```
- Add more fields based on [Congress.gov API docs](https://api.congress.gov) or GovInfo mappings (see `docs/govinfo-119-mapping.md`).
- For relationships (e.g., sponsors, actions), add `@OneToMany` to a `FederalMember` entity.
- Run Flyway migration: Create `V20250929.0001__federal_bills_table.sql` in `src/main/resources/db/migration/` to add the table:
  ```sql
  CREATE TABLE IF NOT EXISTS federal_bills (
      id BIGSERIAL PRIMARY KEY,
      congress_number INTEGER NOT NULL,
      bill_type VARCHAR(10) NOT NULL,
      number INTEGER NOT NULL,
      title TEXT,
      summary TEXT,
      status VARCHAR(50),
      introduced_date TIMESTAMP,
      sponsor_id VARCHAR(50),
      text_content TEXT,
      metadata JSONB,
      source_url VARCHAR(500) UNIQUE NOT NULL,
      ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

  CREATE INDEX idx_federal_bills_congress ON federal_bills(congress_number);
  CREATE INDEX idx_federal_bills_status ON federal_bills(status);
  ```

### Step 2.2: Create a Repository
Similar to `DocumentRepository`. Create `src/main/java/gov/nysenate/openleg/dao/federal/bill/FederalBillRepository.java`:
```java
package gov.nysenate.openleg.dao.federal.bill;

import gov.nysenate.openleg.model.federal.bill.FederalBill;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface FederalBillRepository extends JpaRepository<FederalBill, Long> {
    Optional<FederalBill> findBySourceUrl(String sourceUrl);  // For duplicates

    boolean existsBySourceUrl(String sourceUrl);

    @Query("SELECT b FROM FederalBill b WHERE b.congress = :congress AND b.type = :type ORDER BY b.number")
    List<FederalBill> findByCongressAndType(Integer congress, String type);

    // Upsert logic can use save() with @Version for optimistic locking if needed
}
```

### Step 2.3: Create an Ingestion Service
Extend `IngestionService` for federal data. Create `src/main/java/gov/nysenate/openleg/service/ingestion/federal/FederalBillIngestionService.java`:
```java
package gov.nysenate.openleg.service.ingestion.federal;

import com.fasterxml.jackson.databind.ObjectMapper;  // For JSON parsing
import gov.nysenate.openleg.dao.federal.bill.FederalBillRepository;
import gov.nysenate.openleg.model.federal.bill.FederalBill;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
@Transactional
public class FederalBillIngestionService {
    private static final Logger logger = LoggerFactory.getLogger(FederalBillIngestionService.class);

    @Autowired
    private FederalBillRepository billRepository;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();  // For JSON

    /**
     * Ingest bills from Congress.gov API (e.g., recent introduced bills).
     * API key optional; rate-limited to 1000 req/day without.
     */
    public void ingestCongressBills(String apiKey, Integer congress, String type, Integer limit) {
        String url = "https://api.congress.gov/v3/bill/" + congress + "/" + type + "?limit=" + limit +
                     (apiKey != null ? "&api_key=" + apiKey : "");
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            if (response.getStatusCode().is2xxSuccessful()) {
                Map<String, Object> body = response.getBody();
                List<Map<String, Object>> bills = (List<Map<String, Object>>) body.get("bills");  // Adjust path per API

                List<FederalBill> newBills = bills.stream()
                    .filter(billMap -> !billRepository.existsBySourceUrl((String) billMap.get("congressUrl")))
                    .map(this::mapToFederalBill)
                    .toList();

                billRepository.saveAll(newBills);
                logger.info("Ingested {} new federal bills for congress {}, type {}", newBills.size(), congress, type);
            }
        } catch (Exception e) {
            logger.error("Error ingesting Congress bills: {}", e.getMessage(), e);
        }
    }

    private FederalBill mapToFederalBill(Map<String, Object> billData) {
        FederalBill bill = new FederalBill();
        bill.setCongress(((Number) billData.get("congress")).intValue());
        bill.setType((String) billData.get("billType"));
        bill.setNumber(((Number) billData.get("number")).intValue());
        bill.setTitle((String) billData.get("title"));
        bill.setSummary((String) billData.get("summary"));
        bill.setStatus((String) billData.get("latestAction").get("actionStatus"));
        // Parse dates, sponsor, etc. (use LocalDateTime.parse if ISO strings)
        bill.setIntroducedDate(LocalDateTime.parse((String) billData.get("introducedDate")));
        bill.setSourceUrl((String) billData.get("congressUrl"));
        bill.setFullText(extractText(billData));  // Custom method to parse text/summaryInXml
        bill.setMetadata(objectMapper.writeValueAsString(billData));  // Full JSON
        return bill;
    }

    private String extractText(Map<String, Object> billData) {
        // Logic to get text from 'text' or 'summaries' fields; fetch full if needed via another API call
        return (String) billData.getOrDefault("summary", "No text available");
    }

    /**
     * Scheduled ingestion example (e.g., daily for new bills).
     */
    @Scheduled(cron = "0 0 2 * * ?")  // Daily at 2 AM
    public void scheduledIngestRecentBills() {
        ingestCongressBills(null, 118, "hr", 100);  // No API key, House bills, limit 100
    }

    // For GovInfo bulk: Download XML/ZIP, parse with JAXB (see pom.xml JAXB plugin for USLM XSDs)
    // Example: Use XmlMapper or SAX for large files, then map to FederalBill
}
```
- For GovInfo: Use JAXB (already configured in [`pom.xml`](pom.xml) for USLM schemas) to unmarshal XML into custom classes (generated in `target/generated-sources/xjc`). Fetch bulk data via HTTP or SFTP.
- Handle large datasets: Batch saves (`saveAll()` in chunks), use `@Transactional` for atomicity.
- Duplicates: Check `existsBySourceUrl()` before saving, like in `IngestionService`.

### Step 2.4: Integrate and Run
- **Autowiring**: Spring will inject the repository into the service (add `@Autowired`).
- **Configuration**: Add to `applicationContext.xml` or `@Configuration` class (if using annotations). Set DB URL/user/pass in `src/main/resources/application.properties`:
  ```
  spring.datasource.url=jdbc:postgresql://localhost:5432/openleg
  spring.datasource.username=youruser
  spring.datasource.password=yourpass
  spring.jpa.hibernate.ddl-auto=validate  # Or update
  spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect
  ```
- **Build/Deploy**:
  - `mvn clean compile` (generates JAXB if needed).
  - `mvn flyway:migrate` to apply schema changes.
  - `mvn tomcat7:run` to start embedded Tomcat and test.
  - For production: Build WAR (`mvn package`), deploy to Tomcat.
- **Testing**: Use `@SpringBootTest` or integration tests (see `src/test/java/` patterns). Mock RestTemplate for unit tests.
- **Error Handling/Logging**: Use SLF4J/Log4j (configured in `test.log4j2.xml`). Add retries for API failures.
- **Scalability**: For bulk GovInfo (large XMLs), use streaming parsers (StAX/SAX) to avoid OOM. Integrate with existing update events (e.g., fire `BillUpdateEvent` after save for notifications).

### Step 2.5: Potential Enhancements from Existing Code
- **Updates Integration**: After saving, publish `BillUpdateEvent` (from `gov.nysenate.openleg.updates.bill`) to trigger spotchecks/notifications.
- **Spotchecks**: Extend `gov.nysenate.openleg.spotchecks` for federal data validation (e.g., compare ingested vs. source).
- **Notifications**: Use `gov.nysenate.openleg.notifications` to email on ingestion completion.
- **Python Bridge**: If mixing, call Java services from Python via Jython or REST endpoints (expose service as `@RestController`).
- **Challenges**: Federal data volume is high—use partitioning/indexing in migrations. API rate limits: Cache with Ehcache (in [`pom.xml`](pom.xml)).

This leverages ~80% of the existing setup (JPA, services, deps) while adding federal specifics. If you need code for GovInfo XML parsing or a full example repo/service, provide more details on the exact API/source.