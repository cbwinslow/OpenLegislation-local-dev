# Documentation Standards

## Overview
Comprehensive documentation standards ensure that all aspects of the OpenLegislation system are properly documented for maintainability, onboarding, and compliance.

## API Documentation

### OpenAPI Specification Standards
```yaml
openapi: 3.0.3
info:
  title: OpenLegislation API
  version: 1.0.0
  description: Legislative data access API for state and federal legislation
  contact:
    name: OpenLegislation Support
    email: support@openlegislation.ny.gov
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0

servers:
  - url: https://api.openlegislation.ny.gov
    description: Production API
  - url: https://staging-api.openlegislation.ny.gov
    description: Staging API

security:
  - bearerAuth: []
  - apiKeyAuth: []

paths:
  /api/3/bills/{billId}:
    get:
      summary: Retrieve bill by ID
      description: Get detailed information about a specific bill
      operationId: getBillById
      tags:
        - Bills
      parameters:
        - name: billId
          in: path
          required: true
          description: Bill identifier (e.g., S123-2023)
          schema:
            type: string
            pattern: '^[A-Z]+\d+-\d{4}$'
          example: "S123-2023"
      responses:
        '200':
          description: Bill found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Bill'
        '404':
          description: Bill not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
```

## Code Documentation

### JavaDoc Standards
```java
/**
 * Service responsible for processing legislative bills from multiple sources.
 *
 * <p>This service orchestrates the complete bill processing workflow including:
 * <ul>
 *   <li>Data ingestion from XML/JSON sources</li>
 *   <li>Bill text parsing and metadata extraction</li>
 *   <li>Business rule validation</li>
 *   <li>Data enrichment and cross-referencing</li>
 *   <li>Search index updates</li>
 * </ul></p>
 *
 * <p>The service is designed with resilience in mind:
 * <ul>
 *   <li>Idempotent operations for safe retries</li>
 *   <li>Transactional boundaries for data consistency</li>
 *   <li>Circuit breaker patterns for external dependencies</li>
 *   <li>Comprehensive error handling and logging</li>
 * </ul></p>
 *
 * <p><strong>Thread Safety:</strong> All public methods are thread-safe
 * and can be called concurrently.</p>
 *
 * <p><strong>Performance:</strong> Optimized for high-throughput processing
 * with efficient caching, batch operations, and async processing where appropriate.</p>
 *
 * @author OpenLegislation Development Team
 * @since 1.0.0
 * @version 2.1.0
 */
@Service
public class BillProcessingService {

    /**
     * Processes a bill through the complete processing pipeline.
     *
     * <p>This method coordinates all aspects of bill processing in the correct order:
     * validation, parsing, enrichment, persistence, and indexing.</p>
     *
     * <h3>Processing Steps:</h3>
     * <ol>
     *   <li><strong>Validation:</strong> Ensure bill data meets requirements</li>
     *   <li><strong>Parsing:</strong> Extract structured data from raw text</li>
     *   <li><strong>Enrichment:</strong> Add related data and cross-references</li>
     *   <li><strong>Persistence:</strong> Save to database transactionally</li>
     *   <li><strong>Indexing:</strong> Update search indexes</li>
     * </ol>
     *
     * @param bill the bill to process, must not be {@code null}
     * @return the fully processed bill with all enrichments applied
     * @throws BillProcessingException if any step in processing fails
     * @throws IllegalArgumentException if bill parameter is {@code null}
     *
     * @see BillValidator#validateBill(Bill)
     * @see BillParser#parseBillText(String)
     * @see BillEnricher#enrichBill(Bill)
     * @see BillRepository#saveBill(Bill)
     * @see SearchIndexService#updateBillIndex(Bill)
     */
    @Transactional
    public Bill processBill(@NonNull Bill bill) throws BillProcessingException {
        // Implementation with detailed inline comments
        validateBill(bill);
        Bill parsed = parseBill(bill);
        Bill enriched = enrichBill(parsed);
        Bill saved = saveBill(enriched);
        updateSearchIndex(saved);
        return saved;
    }
}
```

## README Standards

### Project README Template
```markdown
# OpenLegislation

[![CI/CD](https://github.com/nysenate/OpenLegislation/workflows/CI-CD/badge.svg)](https://github.com/nysenate/OpenLegislation/actions/workflows/ci-cd.yml)
[![Security Scan](https://github.com/nysenate/OpenLegislation/workflows/Security%20Scan/badge.svg)](https://github.com/nysenate/OpenLegislation/actions/workflows/security-scan.yml)
[![CodeQL](https://github.com/nysenate/OpenLegislation/workflows/CodeQL/badge.svg)](https://github.com/nysenate/OpenLegislation/security/code-scanning)
[![Coverage](https://codecov.io/gh/nysenate/OpenLegislation/branch/main/graph/badge.svg)](https://codecov.io/gh/nysenate/OpenLegislation)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> Legislative data processing platform providing unified access to state and federal legislation

## 🚀 Features

- **Multi-Source Data Ingestion**: Support for state legislative data and federal Congress.gov/GovInfo APIs
- **Real-time Search**: Full-text search with advanced filtering and faceting
- **RESTful API**: Comprehensive API for programmatic access
- **High Performance**: Optimized for high-throughput data processing
- **Scalable Architecture**: Horizontal scaling with container orchestration
- **Data Quality**: Comprehensive validation and enrichment pipelines

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [License](#license)

## 🏃 Quick Start

### Prerequisites

- **Java**: 17 or higher (Eclipse Temurin recommended)
- **Maven**: 3.8.0 or higher
- **PostgreSQL**: 15 or higher
- **Elasticsearch**: 8.x (optional, for search features)
- **Docker**: For containerized development

### Installation

```bash
# Clone the repository
git clone https://github.com/nysenate/OpenLegislation.git
cd OpenLegislation

# Build the project
mvn clean compile

# Set up database
createdb openleg
psql openleg < src/main/resources/sql/schema.sql

# Run the application
mvn spring-boot:run
```

### First API Call

```bash
# Get API health status
curl http://localhost:8080/actuator/health

# Search for bills
curl "http://localhost:8080/api/3/bills/search?query=tax&limit=5"
```

## 📚 API Documentation

### Authentication

The API supports multiple authentication methods:

```bash
# API Key Authentication
curl -H "X-API-Key: your-api-key" http://localhost:8080/api/3/bills

# JWT Bearer Token
curl -H "Authorization: Bearer your-jwt-token" http://localhost:8080/api/3/bills
```

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/3/bills` | GET | Search bills with filtering |
| `/api/3/bills/{id}` | GET | Get bill by ID |
| `/api/3/laws` | GET | Search laws and statutes |
| `/api/3/committees` | GET | Committee information |
| `/api/3/members` | GET | Legislator information |

### Example Usage

```bash
# Get bill details
curl http://localhost:8080/api/3/bills/S123-2023

# Search bills by sponsor
curl "http://localhost:8080/api/3/bills/search?sponsor=John+Doe"

# Get bills by status
curl "http://localhost:8080/api/3/bills/search?status=PASSED&chamber=SENATE"
```

## 💻 Development

### Project Structure

```
src/
├── main/java/gov/nysenate/openleg/
│   ├── api/                 # REST controllers and DTOs
│   ├── service/             # Business logic services
│   ├── domain/              # Domain models and business rules
│   ├── repository/          # Data access layer
│   ├── infrastructure/      # External integrations
│   └── common/              # Shared utilities
├── main/resources/
│   ├── sql/                 # Database migrations
│   └── application.yml      # Application configuration
└── test/                    # Test suites
    ├── java/                # Unit and integration tests
    └── resources/           # Test data and fixtures
```

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-bill-endpoint
   ```

2. **Run Tests**
   ```bash
   mvn test                           # Unit tests
   mvn integration-test              # Integration tests
   mvn verify                        # Full test suite
   ```

3. **Code Quality Checks**
   ```bash
   mvn spotless:check                 # Code formatting
   mvn checkstyle:check              # Style guidelines
   mvn pmd:check                     # Code analysis
   ```

4. **Submit Pull Request**
   - Ensure all tests pass
   - Update documentation if needed
   - Request review from team members

### Testing Strategy

- **Unit Tests**: Business logic, utilities, isolated components
- **Integration Tests**: Database interactions, external APIs
- **End-to-End Tests**: Complete user workflows
- **Performance Tests**: Load testing and benchmarking

## 🚢 Deployment

### Docker Deployment

```bash
# Build application image
docker build -t openlegislation:latest .

# Run with PostgreSQL
docker run --name openleg-postgres -e POSTGRES_DB=openleg -d postgres:15
docker run --name openleg-app --link openleg-postgres:db -p 8080:8080 openlegislation:latest
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes cluster
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/database.yml
kubectl apply -f k8s/application.yml
```

### Production Checklist

- [ ] Environment variables configured
- [ ] Database backups scheduled
- [ ] SSL certificates installed
- [ ] Monitoring and alerting set up
- [ ] Load balancer configured
- [ ] CDN configured for static assets

## ⚙️ Configuration

### Application Properties

```yaml
# Database Configuration
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/openleg
    username: ${DB_USERNAME:openleg}
    password: ${DB_PASSWORD}

  jpa:
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect

# External APIs
app:
  congress:
    api-key: ${CONGRESS_API_KEY}
    base-url: https://api.congress.gov/v3
  govinfo:
    api-key: ${GOVINFO_API_KEY}
    base-url: https://www.govinfo.gov

# Security
jwt:
  secret: ${JWT_SECRET}
  expiration: 86400000  # 24 hours

# Caching
cache:
  redis:
    host: ${REDIS_HOST:localhost}
    port: ${REDIS_PORT:6379}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USERNAME` | Database username | openleg |
| `DB_PASSWORD` | Database password | *required* |
| `CONGRESS_API_KEY` | Congress.gov API key | *required* |
| `GOVINFO_API_KEY` | GovInfo API key | *required* |
| `JWT_SECRET` | JWT signing secret | *required* |

## 📊 Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8080/actuator/health

# Database connectivity
curl http://localhost:8080/actuator/health/db

# External services
curl http://localhost:8080/actuator/health/external
```

### Metrics

Access metrics at `/actuator/metrics`:

- **JVM Metrics**: Memory usage, GC statistics, thread counts
- **HTTP Metrics**: Request counts, response times, error rates
- **Database Metrics**: Connection pool status, query performance
- **Business Metrics**: Bills processed, API usage statistics

### Logging

Logs are available at `/actuator/logfile` with structured JSON format:

```json
{
  "timestamp": "2023-12-01T10:30:45.123Z",
  "level": "INFO",
  "logger": "gov.nysenate.openleg.service.BillProcessingService",
  "message": "Bill S123-2023 processed successfully",
  "billId": "S123-2023",
  "processingTime": 150,
  "thread": "http-nio-8080-exec-1",
  "requestId": "abc-123-def"
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/OpenLegislation.git`
3. Create feature branch: `git checkout -b feature/amazing-feature`
4. Make changes and add tests
5. Run tests: `mvn test`
6. Commit changes: `git commit -m "Add amazing feature"`
7. Push to branch: `git push origin feature/amazing-feature`
8. Create Pull Request

### Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- New York State Senate for sponsoring this project
- All contributors and maintainers
- Open source community for tools and libraries

## 📞 Support

- **Documentation**: [docs.openlegislation.ny.gov](https://docs.openlegislation.ny.gov)
- **Issues**: [GitHub Issues](https://github.com/nysenate/OpenLegislation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nysenate/OpenLegislation/discussions)
- **Email**: support@openlegislation.ny.gov
```

## Architecture Documentation

### System Architecture Diagrams

#### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Web Browsers • Mobile Apps • Third-party Systems    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Load Balancer • Rate Limiting • Authentication      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 Application Services Layer                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Bill Service • Law Service • Search Service         │    │
│  │ Member Service • Committee Service • API Service    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Access Layer                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ PostgreSQL Database • Elasticsearch • Redis Cache   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 External Data Sources                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Congress.gov API • GovInfo.gov • State Systems      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

#### Data Flow Architecture
```
Raw Data Sources → Ingestion Pipeline → Processing Pipeline → Storage Layer → API Layer → Clients

Ingestion Pipeline:
  ┌─────────────────────────────────────────────────────────────┐
  │ 1. Data Collection     2. Format Detection    3. Initial    │
  │    • Congress.gov API     • XML/JSON parsing    • Validation │
  │    • GovInfo bulk data   • Schema validation   • Sanitization│
  │    • State XML feeds     • Encoding detection               │
  └─────────────────────────────────────────────────────────────┘

Processing Pipeline:
  ┌─────────────────────────────────────────────────────────────┐
  │ 4. Content Parsing     5. Data Enrichment     6. Quality    │
  │    • Bill text parsing    • Sponsor lookup      • Validation │
  │    • Action extraction   • Committee mapping   • Consistency │
  │    • Metadata extraction • Cross-references    • Completeness│
  └─────────────────────────────────────────────────────────────┘

Storage & Indexing:
  ┌─────────────────────────────────────────────────────────────┐
  │ 7. Database Storage    8. Search Indexing    9. Caching     │
  │    • PostgreSQL writes    • Elasticsearch      • Redis       │
  │    • Transaction mgmt    • Full-text search   • Performance  │
  │    • Audit logging       • Faceted search     • Reliability  │
  └─────────────────────────────────────────────────────────────┘
```

## Deployment Documentation

### Infrastructure as Code

#### Terraform Configuration
```hcl
# AWS Infrastructure for OpenLegislation
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# VPC Configuration
resource "aws_vpc" "openleg" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "openleg-vpc"
    Environment = "production"
    Project     = "OpenLegislation"
  }
}

# Application Load Balancer
resource "aws_lb" "openleg" {
  name               = "openleg-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name        = "openleg-alb"
    Environment = "production"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "openleg" {
  name = "openleg-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "openleg-cluster"
    Environment = "production"
  }
}

# RDS PostgreSQL Database
resource "aws_db_instance" "openleg" {
  identifier             = "openleg-prod"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.r6g.large"
  allocated_storage      = 500
  storage_type           = "gp3"
  multi_az               = true
  backup_retention_period = 30
  skip_final_snapshot    = false
  final_snapshot_identifier = "openleg-prod-final"

  db_name  = "openleg"
  username = var.db_username
  password = var.db_password

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.database.name

  tags = {
    Name        = "openleg-database"
    Environment = "production"
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "openleg" {
  cluster_id           = "openleg-cache"
  engine               = "redis"
  node_type            = "cache.r6g.large"
  num_cache_nodes      = 2
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.cache.name
  security_group_ids = [aws_security_group.cache.id]

  tags = {
    Name        = "openleg-cache"
    Environment = "production"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "openleg-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.openleg.name
    ServiceName = aws_ecs_service.openleg.name
  }
}
```

#### Kubernetes Manifests
```yaml
# k8s/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openlegislation
  labels:
    app: openlegislation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: openlegislation
  template:
    metadata:
      labels:
        app: openlegislation
    spec:
      containers:
      - name: openlegislation
        image: openlegislation:latest
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "prod"
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: host
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: openlegislation
spec:
  selector:
    app: openlegislation
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: openlegislation
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.openlegislation.ny.gov
    secretName: openlegislation-tls
  rules:
  - host: api.openlegislation.ny.gov
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: openlegislation
            port:
              number: 80
```

## Runbooks and Procedures

### Incident Response Runbook

#### Database Connection Issues
```markdown
# Database Connection Issues - Runbook

## Impact
- API requests failing with 500 errors
- Bill processing stalled
- Search functionality degraded

## Symptoms
- HTTP 500 errors in application logs
- "Connection refused" or "Connection timeout" errors
- Database connection pool exhausted warnings

## Initial Assessment (5 minutes)
1. Check application health endpoint
   ```bash
   curl -f https://api.openlegislation.ny.gov/actuator/health
   ```

2. Check database connectivity from application servers
   ```bash
   # From application server
   psql -h $DB_HOST -U $DB_USERNAME -d $DB_NAME -c "SELECT 1"
   ```

3. Check database server status
   ```bash
   # AWS RDS status
   aws rds describe-db-instances --db-instance-identifier openleg-prod --query 'DBInstances[0].DBInstanceStatus'
   ```

## Immediate Actions (15 minutes)
1. **If connection pool exhausted**: Restart application instances
   ```bash
   kubectl rollout restart deployment/openlegislation
   ```

2. **If database server down**: Check AWS RDS events and status
   ```bash
   aws rds describe-events --source-identifier openleg-prod --source-type db-instance
   ```

3. **If network connectivity issue**: Check security groups and NACLs
   ```bash
   aws ec2 describe-security-groups --group-ids $DB_SECURITY_GROUP
   ```

## Investigation (30 minutes)
1. Review application logs for error patterns
   ```bash
   kubectl logs -l app=openlegislation --since=1h | grep -i "connection\|database\|pool"
   ```

2. Check database performance metrics
   ```sql
   -- Long-running queries
   SELECT pid, now() - pg_stat_activity.query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '1 minute'
   ORDER BY duration DESC;

   -- Connection counts
   SELECT count(*) as connections FROM pg_stat_activity;
   ```

3. Review infrastructure metrics
   - CPU utilization on database server
   - Memory usage trends
   - Network I/O patterns

## Resolution Steps
1. **Kill long-running queries** (if safe to do so)
   ```sql
   SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND now() - query_start > interval '10 minutes';
   ```

2. **Scale database instance** if consistently overloaded
   ```bash
   aws rds modify-db-instance --db-instance-identifier openleg-prod --db-instance-class db.r6g.xlarge --apply-immediately
   ```

3. **Restart application** if connection pool corrupted
   ```bash
   kubectl scale deployment openlegislation --replicas=0
   kubectl scale deployment openlegislation --replicas=3
   ```

## Recovery Verification
1. Confirm application health
   ```bash
   curl https://api.openlegislation.ny.gov/actuator/health | jq '.status'
   ```

2. Test core functionality
   ```bash
   curl "https://api.openlegislation.ny.gov/api/3/bills/search?limit=1"
   ```

3. Monitor for 30 minutes to ensure stability

## Prevention Measures
1. Implement connection pool monitoring alerts
2. Set up database performance monitoring
3. Configure automatic scaling policies
4. Regular database maintenance and optimization
5. Implement circuit breaker patterns for database calls

## Escalation
- If issue persists > 1 hour: Escalate to database administrators
- If data corruption suspected: Escalate to data recovery team
- If widespread outage: Escalate to incident management team

## Post-Incident Actions
1. Document root cause and resolution steps
2. Update monitoring thresholds if needed
3. Implement additional safeguards
4. Schedule post-mortem meeting within 24 hours
```

#### Application Deployment Issues
```markdown
# Application Deployment Issues - Runbook

## Impact
- New features not available
- Application instability
- Rollback may be required

## Symptoms
- Deployment pipeline failures
- Application startup failures
- Health check failures post-deployment

## Initial Assessment
1. Check deployment status
   ```bash
   kubectl get pods -l app=openlegislation
   kubectl describe deployment/openlegislation
   ```

2. Review deployment logs
   ```bash
   kubectl logs -l app=openlegislation --since=10m
   ```

3. Check recent changes
   ```bash
   git log --oneline -10
   ```

## Common Issues and Solutions

### Database Migration Failures
```bash
# Check migration status
kubectl exec -it $(kubectl get pods -l app=openlegislation -o jsonpath='{.items[0].metadata.name}') -- ./flyway info

# Manual migration if needed
kubectl exec -it $(kubectl get pods -l app=openlegislation -o jsonpath='{.items[0].metadata.name}') -- ./flyway migrate
```

### Configuration Issues
```bash
# Validate configuration
kubectl exec -it $(kubectl get pods -l app=openlegislation -o jsonpath='{.items[0].metadata.name}') -- java -jar app.jar --spring.profiles.active=prod --dry-run

# Check environment variables
kubectl exec -it $(kubectl get pods -l app=openlegislation -o jsonpath='{.items[0].metadata.name}') -- env | grep -E "(DB_|API_|JWT_)"
```

### Resource Constraints
```bash
# Check resource usage
kubectl top pods -l app=openlegislation

# Adjust resource limits if needed
kubectl patch deployment/openlegislation --type='json' -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "4Gi"}]'
```

## Rollback Procedure
1. Identify last known good deployment
   ```bash
   kubectl rollout history deployment/openlegislation
   ```

2. Rollback to previous version
   ```bash
   kubectl rollout undo deployment/openlegislation --to-revision=2
   ```

3. Verify rollback success
   ```bash
   kubectl get pods -l app=openlegislation
   curl https://api.openlegislation.ny.gov/actuator/health
   ```

## Deployment Verification
- [ ] Application starts successfully
- [ ] Health checks pass
- [ ] Database connections work
- [ ] External API integrations function
- [ ] Basic API endpoints respond
- [ ] Search functionality works
- [ ] No error logs in first 5 minutes

## Continuous Improvement
- Add more comprehensive pre-deployment tests
- Implement blue-green deployment strategy
- Add automated rollback capabilities
- Enhance monitoring and alerting
- Regular deployment dry-runs
```

These documentation standards ensure comprehensive, maintainable, and user-friendly documentation across all project components and operational procedures.