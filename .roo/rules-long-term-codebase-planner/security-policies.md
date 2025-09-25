# Security Policies

## Overview
These policies establish security requirements and practices for the OpenLegislation system to protect sensitive legislative data and ensure compliance.

## Core Security Principles

### 1. Defense in Depth
- **Rule**: Multiple layers of security controls
- **Implementation**: Network, application, and data-level protections
- **Validation**: Regular security assessments and penetration testing

### 2. Least Privilege
- **Rule**: Users and systems have minimum required access
- **Implementation**: Role-based access control (RBAC)
- **Validation**: Access reviews and audit logging

### 3. Secure by Default
- **Rule**: Security features enabled by default
- **Implementation**: Secure configurations, fail-safe defaults
- **Validation**: Security configuration reviews

## Authentication & Authorization

### Authentication Methods
```java
@Configuration
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/api/3/admin/**").hasRole("ADMIN")
                .antMatchers("/api/3/process/**").hasRole("PROCESSOR")
                .antMatchers("/api/3/public/**").permitAll()
                .anyRequest().authenticated()
            .and()
            .httpBasic()
            .and()
            .csrf().disable()  // API endpoints
            .sessionManagement()
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS);
    }
}
```

### JWT Token Implementation
```java
@Service
public class JwtService {

    private static final String SECRET_KEY = System.getenv("JWT_SECRET_KEY");
    private static final long EXPIRATION_TIME = 86400000; // 24 hours

    public String generateToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("roles", userDetails.getAuthorities());

        return Jwts.builder()
                .setClaims(claims)
                .setSubject(userDetails.getUsername())
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + EXPIRATION_TIME))
                .signWith(SignatureAlgorithm.HS256, SECRET_KEY)
                .compact();
    }

    public boolean validateToken(String token, UserDetails userDetails) {
        final String username = extractUsername(token);
        return (username.equals(userDetails.getUsername()) && !isTokenExpired(token));
    }
}
```

### Password Policies
- **Minimum Length**: 12 characters
- **Complexity**: Uppercase, lowercase, numbers, special characters
- **History**: Prevent reuse of last 10 passwords
- **Lockout**: 5 failed attempts, 30-minute lockout
- **Expiration**: 90 days

## Data Protection

### Encryption at Rest
```java
@Configuration
public class EncryptionConfig {

    @Bean
    public StringEncryptor stringEncryptor() {
        PooledPBEStringEncryptor encryptor = new PooledPBEStringEncryptor();
        SimpleStringPBEConfig config = new SimpleStringPBEConfig();

        config.setPassword(System.getenv("ENCRYPTION_PASSWORD"));
        config.setAlgorithm("PBEWITHHMACSHA512ANDAES_256");
        config.setKeyObtentionIterations("1000");
        config.setPoolSize("1");
        config.setProviderName("SunJCE");
        config.setSaltGeneratorClassName("org.jasypt.salt.RandomSaltGenerator");
        config.setIvGeneratorClassName("org.jasypt.iv.RandomIvGenerator");
        config.setStringOutputType("base64");

        encryptor.setConfig(config);
        return encryptor;
    }
}
```

### Database Encryption
```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create encrypted columns
ALTER TABLE user_credentials
ADD COLUMN encrypted_password bytea;

-- Encrypt sensitive data
UPDATE user_credentials
SET encrypted_password = pgp_sym_encrypt(password, 'encryption-key');

-- Create view for decrypted access (with proper permissions)
CREATE VIEW user_credentials_decrypted AS
SELECT id, username,
       pgp_sym_decrypt(encrypted_password, 'encryption-key') as password
FROM user_credentials;
```

### Data Classification
- **Public**: Bill text, summaries, public hearing transcripts
- **Internal**: Processing metadata, system logs
- **Confidential**: User credentials, API keys
- **Restricted**: Raw legislative data with PII

## Input Validation & Sanitization

### SQL Injection Prevention
```java
@Repository
public class BillDao {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    public List<Bill> findBillsBySessionYear(int sessionYear) {
        String sql = "SELECT * FROM bill WHERE session_year = :sessionYear";

        SqlParameterSource params = new MapSqlParameterSource()
            .addValue("sessionYear", sessionYear);

        return jdbcTemplate.query(sql, params, new BillRowMapper());
    }
}
```

### XSS Prevention
```java
@Service
public class BillTextSanitizer {

    private static final PolicyFactory POLICY = new HtmlPolicyBuilder()
        .allowElements("p", "br", "strong", "em", "u")
        .allowAttributes("href").onElements("a")
        .requireRelNofollowOnLinks()
        .toFactory();

    public String sanitizeBillText(String text) {
        if (text == null) {
            return null;
        }

        // Remove potentially dangerous scripts
        text = text.replaceAll("<script[^>]*>.*?</script>", "");

        // Sanitize HTML
        return POLICY.sanitize(text);
    }
}
```

### File Upload Security
```java
@Controller
public class FileUploadController {

    private static final long MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
    private static final List<String> ALLOWED_EXTENSIONS = Arrays.asList("xml", "json");

    @PostMapping("/upload")
    public ResponseEntity<?> uploadFile(@RequestParam("file") MultipartFile file) {

        // Validate file size
        if (file.getSize() > MAX_FILE_SIZE) {
            return ResponseEntity.badRequest().body("File too large");
        }

        // Validate file extension
        String extension = getFileExtension(file.getOriginalFilename());
        if (!ALLOWED_EXTENSIONS.contains(extension.toLowerCase())) {
            return ResponseEntity.badRequest().body("Invalid file type");
        }

        // Validate file content (XML structure, etc.)
        if (!isValidXmlContent(file)) {
            return ResponseEntity.badRequest().body("Invalid file content");
        }

        // Process file securely
        return processUploadedFile(file);
    }

    private boolean isValidXmlContent(MultipartFile file) {
        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            DocumentBuilder builder = factory.newDocumentBuilder();
            builder.parse(file.getInputStream());
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
```

## Network Security

### HTTPS Configuration
```yaml
server:
  ssl:
    enabled: true
    key-store: classpath:keystore.p12
    key-store-password: ${SSL_KEYSTORE_PASSWORD}
    key-store-type: PKCS12
    key-alias: openleg
    protocol: TLS
    enabled-protocols: TLSv1.2,TLSv1.3
    ciphers: >
      TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
      TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256

  servlet:
    session:
      cookie:
        secure: true
        http-only: true
        same-site: strict
```

### API Rate Limiting
```java
@Configuration
public class RateLimitConfig {

    @Bean
    public RateLimiterRegistry rateLimiterRegistry() {
        return RateLimiterRegistry.of(
            Map.of(
                "api", RateLimiter.of("api", RateLimiterConfig.custom()
                    .limitRefreshPeriod(Duration.ofMinutes(1))
                    .limitForPeriod(100)
                    .timeoutDuration(Duration.ofSeconds(5))
                    .build())
            )
        );
    }
}
```

### CORS Configuration
```java
@Configuration
public class CorsConfig {

    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/api/**")
                    .allowedOrigins("https://openlegislation.ny.gov")
                    .allowedMethods("GET", "POST", "PUT", "DELETE")
                    .allowedHeaders("*")
                    .allowCredentials(true)
                    .maxAge(3600);
            }
        };
    }
}
```

## Security Monitoring

### Audit Logging
```java
@Aspect
@Component
public class AuditAspect {

    private static final Logger auditLogger = LoggerFactory.getLogger("AUDIT");

    @AfterReturning(pointcut = "execution(* gov.nysenate.openleg.api.*.*(..))",
                    returning = "result")
    public void logApiAccess(JoinPoint joinPoint, Object result) {
        HttpServletRequest request = ((ServletRequestAttributes)
            RequestContextHolder.currentRequestAttributes()).getRequest();

        auditLogger.info("API_ACCESS|user={}|method={}|endpoint={}|ip={}|result={}",
            getCurrentUser(),
            request.getMethod(),
            request.getRequestURI(),
            request.getRemoteAddr(),
            result != null ? "success" : "failure");
    }
}
```

### Security Event Monitoring
```yaml
# Prometheus alerting rules
groups:
  - name: security_alerts
    rules:
      - alert: FailedLoginAttempts
        expr: rate(login_failures_total[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate of failed login attempts"

      - alert: SuspiciousApiAccess
        expr: rate(api_requests_total{status="403"}[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate of forbidden API access"
```

## Incident Response

### Security Incident Procedure
1. **Detection**: Automated monitoring alerts
2. **Assessment**: Security team evaluates impact
3. **Containment**: Isolate affected systems
4. **Recovery**: Restore from clean backups
5. **Lessons Learned**: Post-incident review and improvements

### Breach Notification
- **Internal**: Immediate notification to security team
- **External**: Within 72 hours if PII involved
- **Documentation**: Detailed incident report

## Compliance Requirements

### Data Retention
```sql
-- Implement data retention policies
CREATE OR REPLACE FUNCTION cleanup_old_data() RETURNS void AS $$
BEGIN
    -- Delete data older than retention period
    DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '7 years';
    DELETE FROM session_data WHERE expires_at < NOW();

    -- Archive old legislative data (don't delete)
    UPDATE bill SET archived = true WHERE published_date < NOW() - INTERVAL '10 years';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup job
SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');
```

### Access Reviews
- **Frequency**: Quarterly for privileged access
- **Scope**: All user accounts and system permissions
- **Documentation**: Access review reports

### Security Training
- **Frequency**: Annual security awareness training
- **Topics**: Password security, phishing recognition, data handling
- **Tracking**: Training completion records

## Third-Party Security

### Dependency Scanning
```xml
<!-- pom.xml -->
<build>
  <plugins>
    <plugin>
      <groupId>org.owasp</groupId>
      <artifactId>dependency-check-maven</artifactId>
      <version>7.4.4</version>
      <executions>
        <execution>
          <goals>
            <goal>check</goal>
          </goals>
        </execution>
      </executions>
    </plugin>
  </plugins>
</build>
```

### Vendor Assessment
- **Process**: Security questionnaire for all vendors
- **Requirements**: SOC 2 compliance, penetration testing
- **Monitoring**: Ongoing security monitoring

## Security Testing

### Automated Security Testing
```java
@SpringBootTest
public class SecurityTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    public void shouldPreventSqlInjection() throws Exception {
        mockMvc.perform(get("/api/bills")
                .param("search", "'; DROP TABLE bill; --"))
                .andExpect(status().isBadRequest());
    }

    @Test
    public void shouldRequireAuthentication() throws Exception {
        mockMvc.perform(get("/api/admin/process"))
                .andExpect(status().isUnauthorized());
    }
}
```

### Penetration Testing
- **Frequency**: Annual external penetration testing
- **Scope**: Web applications, APIs, network infrastructure
- **Remediation**: Critical findings fixed within 30 days

These security policies must be regularly reviewed and updated to address new threats and compliance requirements.