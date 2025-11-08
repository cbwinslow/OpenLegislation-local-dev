# GitHub Copilot Instructions for OpenLegislation

## Project Context

OpenLegislation is a comprehensive legislative data platform for New York State and federal legislative data. The system ingests, processes, indexes, and serves legislative content through a REST API.

### Technology Stack
- **Backend**: Java 17, Spring Framework 5, Maven
- **Database**: PostgreSQL 15, Flyway migrations
- **Search**: Elasticsearch 8
- **Frontend**: React, Next.js
- **Infrastructure**: Docker, Tomcat 9
- **Data Sources**: Congress.gov, GovInfo.gov, NY State LBDC

## Code Style and Conventions

### Java Code
- Use Java 17 features where appropriate
- Follow Spring Framework best practices
- Use constructor injection for dependencies
- Prefer immutable objects where possible
- Use Optional<T> for nullable returns
- Follow consistent naming: `camelCase` for methods/variables, `PascalCase` for classes
- Use SLF4J for logging, never System.out.println
- Write comprehensive Javadoc for public APIs

Example:
```java
@Service
public class BillService {
    private final BillDao billDao;
    private final Logger log = LoggerFactory.getLogger(BillService.class);
    
    public BillService(BillDao billDao) {
        this.billDao = billDao;
    }
    
    public Optional<Bill> getBill(BillId billId) {
        log.debug("Fetching bill: {}", billId);
        return billDao.findById(billId);
    }
}
```

### Python Code
- Follow PEP 8 style guide
- Use type hints for function signatures
- Use dataclasses for data structures
- Prefer f-strings for string formatting
- Use pathlib for file operations
- Write docstrings in Google style

Example:
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class BillMetadata:
    """Metadata for a legislative bill.
    
    Args:
        bill_id: Unique identifier for the bill
        title: Bill title
        sponsor: Primary sponsor name
    """
    bill_id: str
    title: str
    sponsor: Optional[str] = None
```

### SQL and Database
- Use Flyway for all schema changes
- Name migrations: `V{version}__{description}.sql`
- Use snake_case for table and column names
- Always add indexes for foreign keys
- Include rollback scripts for complex migrations

### REST API Design
- Follow RESTful conventions
- Use plural nouns for resources: `/api/3/bills`
- Version APIs: `/api/3/...`
- Return appropriate HTTP status codes
- Use JSON for request/response bodies
- Provide pagination for list endpoints

## Domain-Specific Patterns

### Legislative Data Processing
```java
// Pattern for processing source files
public class XmlBillProcessor extends AbstractLegDataProcessor {
    @Override
    public void process(LegDataFragment fragment) {
        // 1. Parse XML source
        BillXml billXml = parseXml(fragment);
        
        // 2. Transform to domain model
        Bill bill = transformToBill(billXml);
        
        // 3. Persist to database
        billDao.updateBill(bill);
        
        // 4. Index in Elasticsearch
        searchIndexService.indexBill(bill);
        
        // 5. Mark as processed
        processedFilesService.markProcessed(fragment);
    }
}
```

### Federal Data Integration
```python
# Pattern for federal data ingestion
def ingest_federal_bills(congress: int, bill_type: str) -> None:
    """Ingest bills from Congress.gov API.
    
    Args:
        congress: Congress number (e.g., 119 for 119th Congress)
        bill_type: Type of bill (hr, s, hjres, etc.)
    """
    # 1. Fetch from API with pagination
    bills = fetch_bills_paginated(congress, bill_type)
    
    # 2. Transform to internal format
    transformed = [transform_congress_bill(b) for b in bills]
    
    # 3. Store in database
    db.bulk_insert_bills(transformed)
    
    # 4. Download bill text if needed
    download_bill_texts(transformed)
```

### Error Handling
```java
// Always handle specific exceptions
try {
    processBill(billId);
} catch (SourceFileNotFoundException e) {
    log.error("Source file not found for bill: {}", billId, e);
    throw new DataProcessingException("Unable to process bill", e);
} catch (ParseException e) {
    log.error("Failed to parse bill XML: {}", billId, e);
    // Continue processing other bills
}
```

## Testing Guidelines

### Unit Tests
- Use JUnit 5 for Java tests
- Use pytest for Python tests
- Mock external dependencies
- Test edge cases and error conditions
- Aim for 80%+ code coverage

```java
@Test
void testBillProcessing() {
    // Given
    BillXml xml = createTestBillXml();
    when(billDao.findById(any())).thenReturn(Optional.empty());
    
    // When
    processor.process(xml);
    
    // Then
    verify(billDao).updateBill(argThat(bill -> 
        bill.getTitle().equals("Test Bill")
    ));
}
```

### Integration Tests
- Use test containers for database tests
- Test full processing pipelines
- Use real sample data from `src/test/resources/`

## Documentation Standards

- Update README.md for major features
- Document API changes in `docs/api_reference.md`
- Create architecture diagrams for complex flows
- Keep inline comments focused on "why", not "what"
- Update migration guides for breaking changes

## Common Tasks

### Adding a New Data Source
1. Create `SourceType` enum entry
2. Implement `SourceFileFsDao` for file access
3. Create processor extending `AbstractLegDataProcessor`
4. Add domain models in `legislation/` package
5. Create database migrations
6. Update API controllers
7. Write integration tests

### Adding a New API Endpoint
1. Create controller method with `@RequestMapping`
2. Add service layer logic
3. Document in OpenAPI/Swagger
4. Write unit tests
5. Update API documentation

### Database Schema Changes
1. Create Flyway migration in `src/main/resources/sql/migrations/`
2. Test migration on clean database
3. Update DAO interfaces and implementations
4. Update integration tests
5. Document breaking changes

## Security Considerations

- Never commit credentials or secrets
- Use parameterized queries, never string concatenation
- Validate and sanitize all user input
- Use HTTPS for external API calls
- Follow OWASP security guidelines
- Use BCrypt for password hashing

## Performance Best Practices

- Use connection pooling for database
- Implement caching for frequently accessed data
- Use bulk operations for batch processing
- Index database columns used in WHERE clauses
- Paginate large result sets
- Use async processing for long-running tasks

## AI Agent Collaboration

When working with AI agents:

### Software Development Agent
- Focus on code quality, testing, and best practices
- Review for security vulnerabilities
- Suggest performance improvements
- Ensure consistent code style

### Legislative Policy Agent
- Validate legislative data structures
- Ensure accurate bill metadata
- Verify legislative process compliance
- Assist with policy categorization

### Database Agent
- Optimize queries and indexes
- Design efficient schemas
- Review migration scripts
- Monitor performance metrics

### Documentation Agent
- Create comprehensive documentation
- Write clear API references
- Maintain consistency across docs
- Generate code examples

## Workflow Integration

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Messages
Follow conventional commits:
- `feat: Add federal bill ingestion`
- `fix: Resolve null pointer in bill processing`
- `docs: Update API documentation`
- `refactor: Simplify database query logic`
- `test: Add unit tests for bill service`
- `chore: Update dependencies`

### Pull Request Guidelines
- Link related issues
- Provide clear description
- Include test results
- Update documentation
- Request review from relevant team members

## Resources

- [OpenLegislation API Docs](http://legislation.nysenate.gov/static/docs/html/)
- [Spring Framework Docs](https://spring.io/projects/spring-framework)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Elasticsearch Docs](https://www.elastic.co/guide/)
- [Congress.gov API](https://api.congress.gov/)

## Quick Commands

```bash
# Build project
mvn clean install

# Run tests
mvn test

# Run with specific profile
mvn spring-boot:run -Dspring.profiles.active=dev

# Database migration
mvn flyway:migrate

# Format code
mvn spotless:apply

# Run security scan
mvn dependency-check:check

# Python tools
cd tools
python3 -m pytest
python3 fetch_govinfo_bulk.py --help
```

## Contact and Support

For questions about:
- **Java/Backend**: Review Spring and Maven documentation
- **Federal Data**: Check `docs/congress_gov_integration.md`
- **Database**: Review schema in `src/main/resources/sql/migrations/`
- **API**: Check controllers in `src/main/java/gov/nysenate/openleg/api/`

Remember: Write clean, maintainable code that the next developer (including future you) will thank you for!
