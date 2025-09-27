# Testing Strategies

## Overview
Comprehensive testing strategies ensure reliability, maintainability, and confidence in the OpenLegislation system.

## Testing Pyramid

### 1. Unit Tests (Bottom Layer - 70%)
```java
@Test
void parseBillAction_ValidInput_ReturnsParsedAction() {
    // Given
    String actionText = "03/15/2023: REFERRED TO RULES";
    BillActionParser parser = new BillActionParser();

    // When
    BillAction action = parser.parse(actionText);

    // Then
    assertThat(action.getDate()).isEqualTo(LocalDate.of(2023, 3, 15));
    assertThat(action.getText()).isEqualTo("REFERRED TO RULES");
}
```

**Guidelines**:
- Test public methods only
- One assertion per test
- Fast execution (< 100ms)
- No external dependencies

### 2. Integration Tests (Middle Layer - 20%)
```java
@SpringBootTest
@Sql(scripts = "/test-data.sql")
class BillProcessingIntegrationTest {

    @Autowired
    private BillProcessor billProcessor;

    @Autowired
    private BillDao billDao;

    @Test
    void processBill_EndToEnd_SavesBillAndActions() {
        // Given
        Bill bill = createTestBill();

        // When
        Bill processed = billProcessor.process(bill);

        // Then
        assertThat(billDao.findById(processed.getBillId())).isPresent();
        assertThat(processed.getActions()).isNotEmpty();
    }
}
```

**Guidelines**:
- Test component interactions
- Use test database
- Include external services (mocks for slow services)
- Clean up after tests

### 3. End-to-End Tests (Top Layer - 10%)
```java
@Test
void billIngestionWorkflow_CompleteFlow_Success() {
    // Given - Place XML file in staging directory
    copyTestXmlToStaging("bill-123.xml");

    // When - Trigger processing
    restTemplate.postForEntity("/api/3/admin/process/run", null, String.class);

    // Then - Verify results
    await().atMost(30, SECONDS).until(() ->
        billRepository.findById("S123").isPresent());

    Bill bill = billRepository.findById("S123").get();
    assertThat(bill.getTitle()).isNotEmpty();
}
```

**Guidelines**:
- Test complete user workflows
- Use production-like environment
- Slow execution acceptable
- High business value

## Test Automation

### CI/CD Integration
```yaml
# .github/workflows/test.yml
jobs:
  test:
    steps:
      - name: Run unit tests
        run: mvn test -Dgroups=unit

      - name: Run integration tests
        run: mvn test -Dgroups=integration

      - name: Run E2E tests
        run: mvn test -Dgroups=e2e
```

### Test Data Management
```java
@Configuration
public class TestDataConfig {

    @Bean
    @Profile("test")
    public TestDataLoader testDataLoader() {
        return new TestDataLoader()
            .addBill("S123", "Test Bill")
            .addMember("MEM001", "John Doe")
            .addCommittee("COM001", "Rules Committee");
    }
}
```

## Test Quality Metrics

### Coverage Requirements
- **Unit Tests**: > 80% line coverage
- **Integration Tests**: > 60% branch coverage
- **Critical Paths**: 100% coverage

### Performance Benchmarks
- **Unit Tests**: < 100ms per test
- **Integration Tests**: < 5s per test
- **E2E Tests**: < 60s per test

## Specialized Testing

### Data Processing Tests
```java
@Test
void processFederalBillXml_ComplexAmendment_ParsesCorrectly() {
    // Test complex federal bill with amendments
    String xmlContent = loadTestResource("federal-bill-with-amendments.xml");
    FederalBillProcessor processor = new FederalBillProcessor();

    Bill bill = processor.process(xmlContent);

    assertThat(bill.getAmendments()).hasSize(3);
    assertThat(bill.getAmendment(0).getText()).contains("Section 1");
}
```

### Security Tests
```java
@Test
void apiEndpoint_UnauthorizedAccess_Returns401() {
    mockMvc.perform(get("/api/admin/process"))
           .andExpect(status().isUnauthorized());
}

@Test
void sqlInjection_Attempt_ReturnsBadRequest() {
    mockMvc.perform(get("/api/bills/search")
                   .param("query", "'; DROP TABLE bills; --"))
           .andExpect(status().isBadRequest());
}
```

### Performance Tests
```java
@Test
void processLargeBillFile_UnderTimeLimit() {
    // Given
    String largeBillXml = loadLargeTestFile("large-bill.xml");

    // When
    long startTime = System.nanoTime();
    Bill bill = billProcessor.process(largeBillXml);
    long endTime = System.nanoTime();

    // Then
    long durationMs = (endTime - startTime) / 1_000_000;
    assertThat(durationMs).isLessThan(5000); // 5 seconds
}
```

## Test Infrastructure

### Test Environments
- **Unit Tests**: In-memory databases, mocked services
- **Integration Tests**: Docker containers, test databases
- **E2E Tests**: Full application stack, production-like setup

### Test Utilities
```java
public class TestUtils {

    public static Bill createTestBill(String billId, String title) {
        return Bill.builder()
                .billId(billId)
                .title(title)
                .session(2023)
                .chamber(Chamber.SENATE)
                .build();
    }

    public static void assertBillEquals(Bill expected, Bill actual) {
        assertThat(actual.getBillId()).isEqualTo(expected.getBillId());
        assertThat(actual.getTitle()).isEqualTo(expected.getTitle());
        // Additional assertions...
    }
}
```

## Continuous Testing

### Test Reporting
```xml
<!-- pom.xml -->
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <executions>
    <execution>
      <goals>
        <goal>prepare-agent</goal>
        <goal>report</goal>
      </goals>
    </execution>
  </executions>
</plugin>
```

### Quality Gates
- **Coverage**: Fail build if below threshold
- **Security**: Block vulnerable dependencies
- **Performance**: Fail if response times exceeded
- **Code Quality**: Enforce static analysis rules

## Test Maintenance

### Flaky Test Management
```java
@RepeatedTest(3)
@DisplayName("Process bill (retry on failure)")
void processBill_RetryOnFailure() {
    // Test that may occasionally fail due to timing
}
```

### Test Documentation
```java
/**
 * Tests the complete bill processing workflow from XML ingestion
 * to database persistence. This test ensures that:
 * 1. XML parsing works correctly
 * 2. Business rules are applied
 * 3. Data is persisted accurately
 * 4. Audit trail is maintained
 */
@Test
void billProcessing_EndToEnd_Success() {
    // Test implementation
}
```

These testing strategies ensure comprehensive coverage and maintainable test suites that provide confidence in system reliability.
