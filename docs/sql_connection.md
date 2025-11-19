# SQL Connection Guide

## Overview
This guide covers database connection configuration and management for the OpenLegislation project.

## Database Configuration

### PostgreSQL Setup
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE openlegislation;
CREATE USER openleg_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE openlegislation TO openleg_user;
\q
```

### Connection Parameters
- **Host**: localhost (or remote host)
- **Port**: 5432 (default)
- **Database**: openlegislation
- **Username**: openleg_user
- **Password**: (from environment)
- **SSL Mode**: require (for production)

## Application Configuration

### JDBC URL Format
```
jdbc:postgresql://host:port/database?sslmode=require&sslfactory=org.postgresql.ssl.NonValidatingFactory
```

### Environment Variables
```bash
# Required environment variables
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=openlegislation
export PGUSER=openleg_user
export PGPASSWORD=your_secure_password

# Combined JDBC URL
export JDBC_DATABASE_URL="jdbc:postgresql://${PGHOST}:${PGPORT}/${PGDATABASE}?user=${PGUSER}&password=${PGPASSWORD}&sslmode=require"
```

### Application Properties
```properties
# src/main/resources/app.properties
jdbc.driverClassName=org.postgresql.Driver
jdbc.url=${JDBC_DATABASE_URL}
jdbc.username=${PGUSER}
jdbc.password=${PGPASSWORD}

# Connection pool settings
jdbc.maxActive=20
jdbc.maxIdle=10
jdbc.minIdle=5
jdbc.maxWait=10000
```

## Connection Pooling

### HikariCP Configuration
```properties
# Advanced connection pool settings
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.idle-timeout=300000
spring.datasource.hikari.max-lifetime=600000
spring.datasource.hikari.connection-timeout=20000
spring.datasource.hikari.leak-detection-threshold=60000
```

### Monitoring
```java
// Monitor connection pool health
@Configuration
public class DatabaseConfig {
    @Autowired
    private HikariDataSource dataSource;

    @Bean
    public MeterRegistry meterRegistry() {
        // Configure metrics for connection pool
        return new SimpleMeterRegistry();
    }
}
```

## Database Migrations

### Flyway Setup
```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-core</artifactId>
    <version>9.16.0</version>
</dependency>
```

### Migration Files
```
src/main/resources/sql/migrations/
├── core/
│   ├── V1__openleg.db-init.sql
│   ├── V2__openleg.schema.sql
│   └── V3__openleg.data.sql
├── bills/
│   └── V20190205.0412__2019_budget_pdfs.sql
├── federal/
│   ├── V20250921.0004__federal_member_schema.sql
│   └── V20250928.0001__ingestion_optimizations.sql
└── members/
    └── V20200527.1011__reset_member_data.sql
```

See `src/main/resources/sql/migrations/README.md` for complete documentation on the organized structure.

### Running Migrations
```bash
# Via Maven
mvn compile flyway:migrate

# Via Spring Boot
mvn spring-boot:run

# Check migration status
mvn flyway:info
```

## Schema Design

### Core Tables
```sql
-- Bills table
CREATE TABLE bill (
    bill_id SERIAL PRIMARY KEY,
    session_year INTEGER NOT NULL,
    print_no VARCHAR(20) NOT NULL,
    title TEXT,
    summary TEXT,
    status VARCHAR(50),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bill actions
CREATE TABLE bill_action (
    action_id SERIAL PRIMARY KEY,
    bill_id INTEGER REFERENCES bill(bill_id),
    action_date DATE NOT NULL,
    chamber VARCHAR(20),
    action_text TEXT,
    sequence_no INTEGER
);

-- Indexes for performance
CREATE INDEX idx_bill_session_year ON bill(session_year);
CREATE INDEX idx_bill_print_no ON bill(print_no);
CREATE INDEX idx_bill_action_bill_id ON bill_action(bill_id);
```

### Federal Extensions
```sql
-- Federal bill fields
ALTER TABLE bill ADD COLUMN congress_number INTEGER;
ALTER TABLE bill ADD COLUMN federal_bill_type VARCHAR(10);
ALTER TABLE bill ADD COLUMN govinfo_id VARCHAR(50);
ALTER TABLE bill ADD COLUMN congressdotgov_url TEXT;
```

## Query Optimization

### Index Strategy
```sql
-- Composite indexes for common queries
CREATE INDEX idx_bill_search ON bill(session_year, print_no, status);

-- Partial indexes for active bills
CREATE INDEX idx_active_bills ON bill(session_year, modified_date)
WHERE status NOT IN ('SIGNED', 'VETOED', 'STRICKEN');

-- Full-text search index
CREATE INDEX idx_bill_fulltext ON bill
USING gin(to_tsvector('english', title || ' ' || summary));
```

### Query Patterns
```sql
-- Optimized bill search
SELECT * FROM bill
WHERE session_year = $1
  AND print_no ILIKE $2 || '%'
ORDER BY print_no
LIMIT 50;

-- Recent bill actions
SELECT b.print_no, ba.action_date, ba.action_text
FROM bill b
JOIN bill_action ba ON b.bill_id = ba.bill_id
WHERE b.session_year = $1
  AND ba.action_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY ba.action_date DESC;
```

## Monitoring and Troubleshooting

### Connection Issues
```bash
# Test connection
psql "postgresql://user:password@host:port/database"

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log

# Monitor active connections
SELECT * FROM pg_stat_activity;
```

### Performance Monitoring
```sql
-- Slow query log
SELECT query, total_time, calls, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Table bloat check
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Backup and Recovery
```bash
# Create backup
pg_dump openlegislation > backup.sql

# Restore backup
psql openlegislation < backup.sql

# Point-in-time recovery setup
# Configure WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/archive/%f'
```

## Security Best Practices

### Connection Security
- Use SSL/TLS for all connections
- Store credentials securely (environment variables, secret management)
- Implement connection timeouts
- Use least privilege principle for database users

### Data Protection
```sql
-- Row Level Security (if needed)
ALTER TABLE sensitive_data ENABLE ROW LEVEL SECURITY;

-- Audit logging
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name TEXT,
    operation TEXT,
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Access Control
```sql
-- Create read-only user for reporting
CREATE USER readonly_user WITH PASSWORD 'password';
GRANT CONNECT ON DATABASE openlegislation TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- Application user with write access
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO openleg_user;
```

## High Availability

### Replication Setup
```bash
# Configure streaming replication
# Primary server postgresql.conf
wal_level = replica
max_wal_senders = 3
wal_keep_segments = 64

# Standby server recovery.conf
primary_conninfo = 'host=primary_host port=5432 user=replication_user'
standby_mode = 'on'
```

### Connection Failover
```java
// Configure multiple hosts in JDBC URL
jdbc:postgresql://host1:5432,host2:5432/database?targetServerType=preferSlave&loadBalanceHosts=true
```

### Load Balancing
- Use Pgpool-II or PgBouncer for connection pooling
- Implement read/write splitting
- Configure health checks and automatic failover