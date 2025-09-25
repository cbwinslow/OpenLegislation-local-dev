# Monitoring & Observability

## Application Metrics

### Business Metrics
```java
@Configuration
public class MetricsConfig {

    @Bean
    public MeterRegistry meterRegistry() {
        return new PrometheusMeterRegistry(PrometheusConfig.DEFAULT);
    }
}

@Service
public class BillMetricsService {

    private final Counter billsProcessed;
    private final Timer billProcessingTime;
    private final Gauge activeBills;

    public BillMetricsService(MeterRegistry registry) {
        this.billsProcessed = Counter.builder("bills.processed.total")
                .description("Total number of bills processed")
                .register(registry);

        this.billProcessingTime = Timer.builder("bill.processing.duration")
                .description("Time taken to process bills")
                .register(registry);

        this.activeBills = Gauge.builder("bills.active.current", this, BillMetricsService::getActiveBillCount)
                .description("Current number of active bills")
                .register(registry);
    }

    public void recordBillProcessed(Bill bill) {
        billsProcessed.increment();
        // Additional metric recording
    }
}
```

### System Metrics
- **JVM Metrics**: Heap usage, GC pauses, thread count
- **Database Metrics**: Connection pools, query performance, lock waits
- **Infrastructure**: CPU, memory, disk I/O, network

## Logging Strategy

### Structured Logging
```java
@Slf4j
@Service
public class BillProcessingService {

    public void processBill(Bill bill) {
        log.info("Processing bill started",
                kv("billId", bill.getBillId()),
                kv("session", bill.getSession()),
                kv("chamber", bill.getChamber()));

        try {
            // Processing logic
            Bill processed = performProcessing(bill);

            log.info("Processing bill completed",
                    kv("billId", bill.getBillId()),
                    kv("processingTime", getProcessingTime()),
                    kv("status", "success"));

        } catch (Exception e) {
            log.error("Processing bill failed",
                     kv("billId", bill.getBillId()),
                     kv("error", e.getMessage()),
                     kv("status", "failed"), e);
            throw e;
        }
    }
}
```

### Log Levels
- **ERROR**: System errors requiring immediate attention
- **WARN**: Potential issues or deprecated features
- **INFO**: Important business events and state changes
- **DEBUG**: Detailed debugging information
- **TRACE**: Very detailed execution flow

## Distributed Tracing

### OpenTelemetry Integration
```java
@Configuration
public class TracingConfig {

    @Bean
    public OpenTelemetry openTelemetry() {
        return OpenTelemetrySdk.builder()
                .setTracerProvider(tracerProvider())
                .setMeterProvider(meterProvider())
                .build();
    }

    @Bean
    public Tracer tracer(OpenTelemetry openTelemetry) {
        return openTelemetry.getTracer("openlegislation", "1.0.0");
    }
}
```

### Trace Instrumentation
```java
@Service
public class BillService {

    @Autowired
    private Tracer tracer;

    public Bill getBill(String billId) {
        Span span = tracer.spanBuilder("getBill")
                .setAttribute("bill.id", billId)
                .startSpan();

        try (Scope scope = span.makeCurrent()) {
            // Business logic
            Bill bill = billRepository.findById(billId);

            span.setAttribute("bill.found", bill != null);
            return bill;

        } catch (Exception e) {
            span.recordException(e);
            span.setStatus(StatusCode.ERROR, e.getMessage());
            throw e;
        } finally {
            span.end();
        }
    }
}
```

## Alerting Strategy

### Alert Categories
1. **Critical**: System down, data corruption
2. **Warning**: Performance degradation, high error rates
3. **Info**: Maintenance notifications, trend alerts

### Alert Rules
```yaml
groups:
  - name: openlegislation_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times detected"
```

## Dashboard Design

### Application Dashboard
- Request rate, error rate, response time percentiles
- Active users, concurrent sessions
- Database connection pools, query performance
- Cache hit rates, memory usage

### Business Dashboard
- Bills processed per hour/day
- Data ingestion success rates
- API usage by endpoint and user
- Legislative session progress

### Infrastructure Dashboard
- Server CPU, memory, disk usage
- Network I/O, latency
- Database performance metrics
- Container orchestration status

## Health Checks

### Application Health
```java
@Component
public class ApplicationHealthIndicator implements HealthIndicator {

    @Autowired
    private DataSource dataSource;

    @Autowired
    private BillDao billDao;

    @Override
    public Health health() {
        try {
            // Database connectivity check
            dataSource.getConnection().close();

            // Business logic check
            billDao.findRecentBills(1);

            return Health.up()
                    .withDetail("database", "available")
                    .withDetail("businessLogic", "operational")
                    .build();

        } catch (Exception e) {
            return Health.down()
                    .withDetail("error", e.getMessage())
                    .build();
        }
    }
}
```

### External Dependencies
```java
@Component
public class ExternalServiceHealthIndicator implements HealthIndicator {

    @Override
    public Health health() {
        try {
            // Check external API connectivity
            ResponseEntity<String> response = restTemplate.getForEntity(
                "https://api.congress.gov/health", String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                return Health.up().withDetail("congress-api", "available").build();
            } else {
                return Health.down().withDetail("congress-api", "unavailable").build();
            }

        } catch (Exception e) {
            return Health.down()
                    .withDetail("congress-api", "error")
                    .withDetail("message", e.getMessage())
                    .build();
        }
    }
}
```

## Performance Profiling

### Continuous Profiling
```bash
# JVM profiling flags
JAVA_OPTS="
  -XX:+UnlockDiagnosticVMOptions
  -XX:+DebugNonSafepoints
  -Djava.rmi.server.hostname=localhost
  -Dcom.sun.management.jmxremote.port=9091
  -Dcom.sun.management.jmxremote.ssl=false
  -Dcom.sun.management.jmxremote.authenticate=false
"
```

### Profiling Tools
- **JProfiler**: Memory and CPU profiling
- **VisualVM**: JVM monitoring and profiling
- **Async Profiler**: Low-overhead production profiling
- **Java Flight Recorder**: Event-based profiling

## Log Aggregation

### Centralized Logging
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
```

### Log Parsing
```conf
# logstash.conf
input {
  file {
    path => "/var/log/openlegislation/*.log"
    start_position => "beginning"
  }
}

filter {
  grok {
    match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{DATA:logger} - %{GREEDYDATA:message}" }
  }

  json {
    source => "message"
    target => "parsed_json"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "openlegislation-%{+YYYY.MM.dd}"
  }
}
```

## Incident Response

### Alert Response Procedures
1. **Triage**: Assess alert severity and impact
2. **Investigation**: Check logs, metrics, and system status
3. **Resolution**: Apply fixes or workarounds
4. **Communication**: Update stakeholders
5. **Post-mortem**: Document root cause and improvements

### Runbook Automation
```bash
#!/bin/bash
# incident-response.sh

echo "Starting incident response procedure..."

# 1. Check system status
check_system_status() {
    echo "Checking application health..."
    curl -f http://localhost:8080/actuator/health || echo "Application unhealthy"

    echo "Checking database connectivity..."
    # Database checks
}

# 2. Gather diagnostic information
gather_diagnostics() {
    echo "Collecting logs..."
    # Log collection

    echo "Capturing metrics..."
    # Metric snapshots
}

# 3. Execute recovery procedures
execute_recovery() {
    echo "Attempting automated recovery..."
    # Recovery steps
}

# Execute procedures
check_system_status
gather_diagnostics
execute_recovery
```

These monitoring and observability practices ensure system reliability, performance, and rapid issue resolution.