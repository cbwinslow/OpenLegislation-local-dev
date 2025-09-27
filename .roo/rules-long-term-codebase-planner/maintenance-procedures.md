# Maintenance Procedures

## Overview
Structured procedures for maintaining, updating, and evolving the OpenLegislation codebase over time.

## Regular Maintenance Tasks

### 1. Dependency Updates
```bash
# Weekly dependency check
mvn versions:display-dependency-updates
mvn versions:display-plugin-updates

# Update dependencies
mvn versions:update-properties
mvn versions:update-parent

# Test after updates
mvn clean test
```

### 2. Database Maintenance
```sql
-- Weekly cleanup
VACUUM ANALYZE bill;
VACUUM ANALYZE bill_action;
REINDEX INDEX idx_bill_session_year;

-- Monthly archive
UPDATE bill SET archived = true
WHERE published_date < NOW() - INTERVAL '2 years'
AND last_updated < NOW() - INTERVAL '6 months';
```

### 3. Log Rotation
```bash
# Rotate application logs
logrotate -f /etc/logrotate.d/openleg

# Archive old logs
find /var/log/openleg -name "*.log.*" -mtime +30 -delete
```

## Code Health Monitoring

### Technical Debt Tracking
```java
// Code quality metrics
@Scheduled(fixedRate = 86400000) // Daily
public void monitorCodeQuality() {
    int cyclomaticComplexity = calculateAverageComplexity();
    double duplicationRate = calculateDuplicationRate();
    double testCoverage = calculateTestCoverage();

    if (cyclomaticComplexity > 10) {
        alert("High cyclomatic complexity detected");
    }

    if (testCoverage < 0.8) {
        alert("Test coverage below threshold");
    }
}
```

### Performance Monitoring
```yaml
# Prometheus metrics
jvm_memory_used_bytes{area="heap"} > 0.9 * jvm_memory_max_bytes{area="heap"}
http_request_duration_seconds{quantile="0.95"} > 2.0
database_connections_active > 50
```

## Release Management

### Version Numbering
- **Major**: Breaking changes (1.x.x)
- **Minor**: New features (x.1.x)
- **Patch**: Bug fixes (x.x.1)
- **Pre-release**: Alpha/Beta/RC (x.x.x-alpha.1)

### Release Process
```bash
# 1. Create release branch
git checkout -b release/v1.2.0

# 2. Update version
mvn versions:set -DnewVersion=1.2.0

# 3. Run full test suite
mvn clean verify

# 4. Create release notes
git log --oneline v1.1.0..HEAD > release-notes.md

# 5. Tag release
git tag -a v1.2.0 -m "Release v1.2.0"

# 6. Deploy to staging
mvn deploy -Pstaging

# 7. Deploy to production
mvn deploy -Pproduction
```

## Backup and Recovery

### Database Backups
```bash
# Daily backup
pg_dump openleg > openleg_$(date +%Y%m%d).sql

# Compress backup
gzip openleg_$(date +%Y%m%d).sql

# Upload to S3
aws s3 cp openleg_$(date +%Y%m%d).sql.gz s3://openleg-backups/

# Cleanup old backups (keep 30 days)
find /backups -name "openleg_*.sql.gz" -mtime +30 -delete
```

### Application Backups
```bash
# Configuration backup
tar -czf config_backup_$(date +%Y%m%d).tar.gz /etc/openleg/

# Log backup
tar -czf logs_backup_$(date +%Y%m%d).tar.gz /var/log/openleg/
```

## Incident Response

### System Outage Procedure
1. **Detection**: Monitoring alerts
2. **Assessment**: Check system status
3. **Communication**: Notify stakeholders
4. **Recovery**: Follow recovery procedures
5. **Post-mortem**: Document lessons learned

### Data Corruption Recovery
```sql
-- Restore from backup
pg_restore -d openleg openleg_backup.sql

-- Verify data integrity
SELECT COUNT(*) FROM bill;
SELECT COUNT(*) FROM bill_action;

-- Rebuild indexes if needed
REINDEX DATABASE openleg;
```

## Security Maintenance

### Vulnerability Scanning
```bash
# Weekly security scan
mvn org.owasp:dependency-check-maven:check

# Update dependencies with security fixes
mvn versions:use-latest-versions

# Review and apply security patches
```

### Access Review
```sql
-- Review user access
SELECT username, last_login, role
FROM user_accounts
WHERE last_login < NOW() - INTERVAL '90 days';

-- Disable inactive accounts
UPDATE user_accounts
SET active = false
WHERE last_login < NOW() - INTERVAL '180 days';
```

## Performance Optimization

### Query Optimization
```sql
-- Analyze slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_bill_status_date
ON bill (status, published_date);
```

### Cache Management
```java
@Scheduled(fixedRate = 3600000) // Hourly
public void refreshCaches() {
    billCache.invalidateAll();
    memberCache.invalidateAll();

    // Warm up frequently accessed data
    preloadHotData();
}
```

## Documentation Updates

### API Documentation
```bash
# Generate updated API docs
mvn spring-boot:run -Dspring-boot.run.profiles=docs

# Update OpenAPI spec
curl http://localhost:8080/v3/api-docs > openapi.json
```

### Code Documentation
```java
/**
 * Updates bill processing logic for new legislative session.
 *
 * @param sessionYear the legislative session year
 * @param rules updated processing rules
 * @since 1.2.0
 */
public void updateProcessingRules(int sessionYear, ProcessingRules rules) {
    // Implementation
}
```

## Compliance Maintenance

### Data Retention
```sql
-- Implement retention policies
DELETE FROM audit_log
WHERE created_at < NOW() - INTERVAL '7 years';

-- Archive old data
UPDATE bill SET archived = true
WHERE published_date < NOW() - INTERVAL '10 years';
```

### Regulatory Updates
- Monitor legislative data format changes
- Update parsing logic for new requirements
- Maintain compliance with data retention laws

## Team Coordination

### Maintenance Schedule
- **Daily**: Automated tasks (backups, log rotation)
- **Weekly**: Dependency updates, security scans
- **Monthly**: Performance reviews, access audits
- **Quarterly**: Major updates, compliance reviews
- **Annually**: Architecture reviews, disaster recovery tests

### Communication
- **Internal**: Team standups, maintenance windows
- **External**: Status page updates, incident notifications
- **Documentation**: Runbooks, post-mortems

These procedures ensure the system remains reliable, secure, and performant over its operational lifetime.
