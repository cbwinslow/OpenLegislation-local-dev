# Performance Optimization Guidelines

## Overview
These guidelines ensure optimal performance across all components of the OpenLegislation system.

## Core Principles

### 1. Performance by Design
- **Rule**: Performance considerations must be included in initial design
- **Implementation**: Performance requirements in acceptance criteria
- **Validation**: Performance tests in CI/CD pipeline

### 2. Measure First
- **Rule**: Never optimize without measurement
- **Implementation**: Establish performance baselines before optimization
- **Validation**: A/B testing for performance changes

### 3. 80/20 Rule
- **Rule**: Focus optimization efforts on the 20% that matters
- **Implementation**: Identify performance bottlenecks through profiling
- **Validation**: Performance monitoring and alerting

## Application Performance

### Database Optimization

#### Query Optimization
```java
// Bad: N+1 queries
public List<Bill> getBillsWithActions(List<String> billIds) {
    return billIds.stream()
        .map(id -> billDao.findById(id))  // N queries
        .filter(Optional::isPresent)
        .map(Optional::get)
        .collect(Collectors.toList());
}

// Good: Single query with join
public List<Bill> getBillsWithActions(List<String> billIds) {
    return billDao.findBillsWithActions(billIds);  // 1 query
}
```

#### Connection Pooling
```java
@Configuration
public class DatabaseConfig {

    @Bean
    @ConfigurationProperties("spring.datasource.hikari")
    public HikariDataSource dataSource() {
        HikariDataSource dataSource = new HikariDataSource();
        dataSource.setMaximumPoolSize(20);
        dataSource.setMinimumIdle(5);
        dataSource.setConnectionTimeout(30000);
        dataSource.setIdleTimeout(600000);
        dataSource.setMaxLifetime(1800000);
        return dataSource;
    }
}
```

#### Indexing Strategy
```sql
-- Primary keys (automatic)
-- Foreign keys (automatic for some DBs)
CREATE INDEX idx_bill_session_year ON bill(session_year);
CREATE INDEX idx_bill_status ON bill(status);
CREATE INDEX idx_bill_action_date ON bill_action(action_date);

-- Composite indexes for common queries
CREATE INDEX idx_bill_search ON bill(session_year, status, chamber);
```

### Memory Management

#### Object Pooling
```java
// Use object pooling for expensive objects
@Bean
public GenericObjectPool<XmlProcessor> xmlProcessorPool() {
    GenericObjectPoolConfig<XmlProcessor> config = new GenericObjectPoolConfig<>();
    config.setMaxTotal(10);
    config.setMaxIdle(5);
    config.setMinIdle(1);

    return new GenericObjectPool<>(new XmlProcessorFactory(), config);
}
```

#### Streaming Processing
```java
// Process large XML files without loading into memory
public void processLargeXmlFile(Path xmlFile) throws IOException {
    try (XMLStreamReader reader = XMLInputFactory.newInstance()
            .createXMLStreamReader(Files.newInputStream(xmlFile))) {

        while (reader.hasNext()) {
            int event = reader.next();

            if (event == XMLStreamConstants.START_ELEMENT) {
                String elementName = reader.getLocalName();

                if ("bill".equals(elementName)) {
                    processBillElement(reader);  // Process incrementally
                }
            }
        }
    }
}
```

### Caching Strategy

#### Multi-Level Caching
```java
@Service
public class BillCacheService {

    @Autowired
    private CacheManager cacheManager;

    @Cacheable(value = "bills", key = "#billId")
    public Bill getBill(String billId) {
        return billDao.findById(billId);
    }

    @CacheEvict(value = "bills", key = "#bill.billId")
    public Bill saveBill(Bill bill) {
        return billDao.save(bill);
    }
}
```

#### Cache Configuration
```yaml
spring:
  cache:
    type: redis
    redis:
      time-to-live: 3600000  # 1 hour

  redis:
    host: localhost
    port: 6379
    timeout: 2000ms
```

## API Performance

### Response Time Targets
- **API Endpoints**: < 500ms (95th percentile)
- **Search Queries**: < 2s (95th percentile)
- **Bulk Operations**: < 30s (95th percentile)
- **File Downloads**: < 60s (95th percentile)

### Pagination
```java
@RestController
public class BillController {

    @GetMapping("/bills")
    public Page<BillSummary> getBills(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size,
            @RequestParam(required = false) String search) {

        Pageable pageable = PageRequest.of(page, size, Sort.by("publishedDate").descending());
        return billService.searchBills(search, pageable);
    }
}
```

### Compression
```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new CompressionInterceptor());
    }

    @Bean
    public GzipCompressor gzipCompressor() {
        return new GzipCompressor();
    }
}
```

## Infrastructure Performance

### JVM Tuning
```bash
# JVM performance flags
JAVA_OPTS="
  -Xms2g -Xmx4g
  -XX:+UseG1GC
  -XX:MaxGCPauseMillis=200
  -XX:+UseCompressedOops
  -XX:+OptimizeStringConcat
  -Djava.awt.headless=true
"
```

### Database Tuning
```sql
-- PostgreSQL configuration recommendations
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### Load Balancing
```nginx
upstream openleg_backend {
    least_conn;
    server backend1:8080 weight=3;
    server backend2:8080 weight=3;
    server backend3:8080 weight=1;  # Lower weight for maintenance
    keepalive 32;
}

server {
    listen 80;
    location / {
        proxy_pass http://openleg_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
    }
}
```

## Monitoring & Alerting

### Performance Metrics
```java
@Timed(value = "bill.processing", histogram = true)
public Bill processBill(Bill bill) {
    // Processing logic
}

@Gauge(name = "bill.queue.size")
public int getQueueSize() {
    return billQueue.size();
}
```

### Alerting Rules
```yaml
groups:
  - name: openleg_performance
    rules:
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"

      - alert: HighMemoryUsage
        expr: (1 - system_memory_available / system_memory_total) > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage detected"
```

## Performance Testing

### Load Testing
```javascript
// k6 load test script
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Ramp up to 200 users
    { duration: '5m', target: 200 },  // Stay at 200 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
  },
};

export default function () {
  let response = http.get('http://localhost:8080/api/3/bills');
  check(response, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}
```

### Profiling Tools
- **JVM**: VisualVM, JProfiler, YourKit
- **Database**: pgBadger, explain.depesz.com
- **Application**: Spring Boot Actuator, Micrometer
- **Infrastructure**: Prometheus, Grafana

## Optimization Workflow

### 1. Identify Bottlenecks
```bash
# Use profiling tools to identify hotspots
./gradlew build --profile
java -agentlib:hprof=cpu=samples,depth=10 -jar application.jar
```

### 2. Measure Impact
```java
@Benchmark
@BenchmarkMode(Mode.AverageTime)
public void testBillProcessingPerformance() {
    // Performance test implementation
}
```

### 3. Implement Optimization
- Apply the most impactful changes first
- Use established patterns and best practices
- Ensure backward compatibility

### 4. Validate Results
- Run performance tests before and after
- Monitor production metrics
- A/B test significant changes

### 5. Document Changes
- Update performance baselines
- Document optimization decisions
- Share learnings with team

## Performance Budgets

### Application Metrics
- **CPU Usage**: < 70% average
- **Memory Usage**: < 80% of allocated heap
- **Disk I/O**: < 1000 IOPS sustained
- **Network I/O**: < 100 Mbps sustained

### Database Metrics
- **Connection Pool Utilization**: < 80%
- **Query Response Time**: < 100ms average
- **Lock Wait Time**: < 10ms average
- **Cache Hit Rate**: > 95%

### Infrastructure Metrics
- **Server Response Time**: < 200ms
- **Error Rate**: < 1%
- **Uptime**: > 99.9%
- **Auto-scaling**: < 5 minutes

These guidelines must be regularly reviewed and updated as the system evolves and new performance challenges emerge.