# Usage Guide

## Overview
OpenLegislation is a comprehensive platform for processing, storing, and serving legislative data from New York State and federal sources.

## Getting Started

### Prerequisites
- Java 17 or higher
- Maven 3.6+
- PostgreSQL 12+
- Elasticsearch 8.x
- Node.js 16+ (for frontend development)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/nysenate/OpenLegislation.git
   cd OpenLegislation
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Set up database**
   ```bash
   createdb openlegislation
   mvn compile flyway:migrate
   ```

4. **Build and run**
   ```bash
   mvn clean compile
   mvn tomcat7:run
   ```

5. **Access the application**
   - Web interface: http://localhost:8080
   - API documentation: http://localhost:8080/static/docs/html/

## API Usage

### Authentication
Request a free API key from http://legislation.nysenate.gov/

### Base URL
```
https://legislation.nysenate.gov/api/3/
```

### Common Endpoints

#### Bills
```http
GET /api/3/bills/{sessionYear}/{printNo}
GET /api/3/bills/search?term={searchTerm}
GET /api/3/bills/recent?limit={limit}
```

#### Laws
```http
GET /api/3/laws/{lawId}
GET /api/3/laws/search?term={searchTerm}
```

#### Committees
```http
GET /api/3/committees/{sessionYear}
GET /api/3/committees/{sessionYear}/{chamber}/{name}
```

### Response Format
All API responses are in JSON format:

```json
{
  "success": true,
  "message": "",
  "responseType": "bill",
  "result": {
    // Bill data
  }
}
```

## Data Ingestion

### Manual Ingestion
Place XML/SOBI files in the staging directory and trigger processing:

```bash
curl -X POST http://localhost:8080/api/3/admin/process/run \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Automated Ingestion
Use the provided tools for bulk ingestion:

```bash
# Federal data
python tools/fetch_govinfo_bulk.py

# Congress data
python tools/bulk_ingest_congress_gov.sh
```

## Development Workflow

### Code Style
- Follow Java coding standards
- Use meaningful variable and method names
- Add comprehensive documentation
- Write unit tests for new functionality

### Testing
```bash
# Run unit tests
mvn test

# Run integration tests
mvn verify

# Generate test coverage report
mvn jacoco:report
```

### Database Migrations
Use Flyway for schema changes:

```sql
-- src/main/resources/sql/migrations/V1_2__add_federal_fields.sql
ALTER TABLE bill ADD COLUMN congress_number INTEGER;
ALTER TABLE bill ADD COLUMN federal_bill_type VARCHAR(10);
```

### Building for Production
```bash
mvn clean package -DskipTests
# Deploy target/legislation-*.war to Tomcat
```

## Configuration

### Application Properties
Key configuration files:
- `src/main/resources/app.properties` - Main configuration
- `src/main/resources/app.properties.local` - Local overrides
- `src/main/resources/logback.xml` - Logging configuration

### Environment Variables
- `JDBC_DATABASE_URL` - Database connection string
- `ELASTICSEARCH_URL` - Elasticsearch cluster URL
- `API_KEY_SECRET` - API authentication secret

## Troubleshooting

### Common Issues

#### Database Connection Issues
- Verify PostgreSQL is running
- Check connection string in `.env`
- Ensure database exists and user has permissions

#### Build Failures
- Clear Maven cache: `mvn clean`
- Update dependencies: `mvn dependency:resolve`
- Check Java version: `java -version`

#### Elasticsearch Issues
- Verify Elasticsearch is running on correct port
- Check cluster health: `curl localhost:9200/_cluster/health`
- Reindex data if necessary

#### Memory Issues
- Increase JVM heap size in Maven: `MAVEN_OPTS="-Xmx2g"`
- Monitor memory usage during processing
- Optimize batch sizes in configuration

### Logs
Check application logs in:
- `logs/openlegislation.log`
- Tomcat logs: `tomcat/logs/`
- Maven output for build issues

### Support
- GitHub Issues: https://github.com/nysenate/OpenLegislation/issues
- Documentation: http://legislation.nysenate.gov/static/docs/html/
- Email: developers@nysenate.gov

## Performance Tuning

### Database Optimization
- Use appropriate indexes
- Monitor query performance
- Implement connection pooling
- Use prepared statements

### Application Tuning
- Configure thread pools appropriately
- Set appropriate cache sizes
- Monitor JVM garbage collection
- Use profiling tools for bottlenecks

### Infrastructure Scaling
- Horizontal scaling with load balancer
- Database read replicas
- Elasticsearch cluster configuration
- CDN for static assets