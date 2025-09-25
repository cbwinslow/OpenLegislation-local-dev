# Code Quality Standards

## Overview
These standards ensure consistent, maintainable, and high-quality code across the OpenLegislation codebase.

## General Principles

### 1. Readability First
- **Rule**: Code must be readable by humans before machines
- **Implementation**: Clear naming, consistent formatting, meaningful comments
- **Validation**: Code review checklist includes readability assessment

### 2. DRY (Don't Repeat Yourself)
- **Rule**: Eliminate code duplication through abstraction
- **Implementation**: Extract common functionality into reusable components
- **Validation**: Static analysis tools flag duplicate code blocks

### 3. Single Responsibility Principle
- **Rule**: Each class/method/function has one reason to change
- **Implementation**: Small, focused classes with clear boundaries
- **Validation**: Code reviews enforce SRP compliance

## Naming Conventions

### Java Naming
```java
// Classes
public class BillProcessor {}           // PascalCase
public class BillActionAnalyzer {}      // PascalCase

// Methods
public void processBill() {}            // camelCase
public Bill getBillById() {}           // camelCase, descriptive

// Variables
private Bill currentBill;              // camelCase
private final String BILL_STATUS;      // UPPER_SNAKE_CASE for constants

// Packages
gov.nysenate.openleg.processor.bill    // lowercase, hierarchical
```

### Database Naming
```sql
-- Tables
bill                                    -- lowercase, singular
bill_action                            -- lowercase, snake_case
federal_member                         -- lowercase, snake_case

-- Columns
bill_id                                -- lowercase, snake_case
created_at                             -- lowercase, snake_case
is_active                              -- lowercase, snake_case, boolean prefix
```

### File Naming
```
BillProcessor.java                    # PascalCase + Type
BillActionAnalyzer.java              # PascalCase + Type
bill-dao.xml                         # lowercase, hyphenated
application.properties               # lowercase, hyphenated
```

## Code Structure

### Class Organization
```java
public class BillProcessor {

    // Constants (public, protected, private)
    public static final String PROCESSOR_NAME = "BillProcessor";

    // Static variables and methods
    private static final Logger logger = LoggerFactory.getLogger(BillProcessor.class);

    // Instance variables
    private final BillDao billDao;
    private final BillActionParser actionParser;

    // Constructor
    public BillProcessor(BillDao billDao, BillActionParser actionParser) {
        this.billDao = billDao;
        this.actionParser = actionParser;
    }

    // Public methods
    public Bill process(Bill bill) {
        // Implementation
    }

    // Private methods
    private void validateBill(Bill bill) {
        // Implementation
    }
}
```

### Method Structure
```java
public Bill processBill(Bill bill) {
    // 1. Input validation
    validateBill(bill);

    // 2. Pre-processing
    Bill processedBill = preprocessBill(bill);

    // 3. Core processing
    processedBill = performCoreProcessing(processedBill);

    // 4. Post-processing
    processedBill = postprocessBill(processedBill);

    // 5. Return result
    return processedBill;
}
```

## Documentation Standards

### JavaDoc Requirements
```java
/**
 * Processes legislative bills from various sources into standardized format.
 *
 * <p>This processor handles the complete lifecycle of bill processing including
 * validation, parsing, enrichment, and persistence. It supports multiple
 * legislative data formats and ensures data consistency across all sources.</p>
 *
 * <p>Thread Safety: This class is thread-safe and can be used concurrently.</p>
 *
 * @author OpenLegislation Team
 * @since 1.0.0
 */
public class BillProcessor {

    /**
     * Processes a single bill through the complete processing pipeline.
     *
     * @param bill the bill to process, must not be null
     * @return the processed bill with enriched data
     * @throws BillProcessingException if processing fails
     * @throws IllegalArgumentException if bill is null
     */
    public Bill process(@NonNull Bill bill) throws BillProcessingException {
        // Implementation
    }
}
```

### Inline Comments
```java
public void processBillActions(Bill bill) {
    // Extract actions from bill text using regex patterns
    List<String> actionTexts = extractActionTexts(bill.getText());

    // Parse each action text into structured Action objects
    for (String actionText : actionTexts) {
        BillAction action = parseAction(actionText);

        // Validate action has required fields
        if (action.getDate() == null) {
            logger.warn("Action missing date: {}", actionText);
            continue; // Skip invalid actions
        }

        bill.addAction(action);
    }
}
```

## Error Handling

### Exception Hierarchy
```
OpenLegislationException (base)
├── BillProcessingException
├── DataIngestionException
├── ValidationException
├── DatabaseException
└── ExternalServiceException
```

### Error Handling Patterns
```java
public Bill processBill(Bill bill) throws BillProcessingException {
    try {
        // Processing logic
        validateBill(bill);
        Bill processed = performProcessing(bill);
        return processed;
    } catch (ValidationException e) {
        logger.error("Bill validation failed for bill: {}", bill.getBillId(), e);
        throw new BillProcessingException("Bill validation failed", e);
    } catch (DatabaseException e) {
        logger.error("Database error processing bill: {}", bill.getBillId(), e);
        throw new BillProcessingException("Database error during processing", e);
    } catch (Exception e) {
        logger.error("Unexpected error processing bill: {}", bill.getBillId(), e);
        throw new BillProcessingException("Unexpected processing error", e);
    }
}
```

## Testing Standards

### Unit Test Structure
```java
@ExtendWith(MockitoExtension.class)
class BillProcessorTest {

    @Mock
    private BillDao billDao;

    @Mock
    private BillActionParser actionParser;

    @InjectMocks
    private BillProcessor billProcessor;

    @Test
    void process_ValidBill_ReturnsProcessedBill() {
        // Given
        Bill inputBill = createTestBill();
        Bill expectedBill = createExpectedProcessedBill();
        when(billDao.save(any(Bill.class))).thenReturn(expectedBill);

        // When
        Bill result = billProcessor.process(inputBill);

        // Then
        assertThat(result).isEqualTo(expectedBill);
        verify(billDao).save(inputBill);
    }
}
```

### Test Naming Convention
```
MethodName_StateUnderTest_ExpectedBehavior
process_ValidBill_ReturnsProcessedBill
process_NullBill_ThrowsIllegalArgumentException
process_InvalidBill_ThrowsValidationException
```

## Performance Standards

### Method Complexity
- **Cyclomatic Complexity**: ≤ 10 per method
- **Lines of Code**: ≤ 50 lines per method
- **Parameters**: ≤ 5 parameters per method

### Database Performance
- **Query Timeout**: 30 seconds maximum
- **Connection Pool**: Properly configured
- **Indexing**: Appropriate indexes for query patterns
- **Batch Operations**: Use batch inserts/updates for bulk operations

## Security Standards

### Input Validation
```java
public void processBillText(@NonNull String billText) {
    // Validate input
    if (billText == null || billText.trim().isEmpty()) {
        throw new IllegalArgumentException("Bill text cannot be null or empty");
    }

    // Sanitize input (remove potentially dangerous content)
    String sanitizedText = sanitizeInput(billText);

    // Limit input size
    if (sanitizedText.length() > MAX_BILL_TEXT_LENGTH) {
        throw new ValidationException("Bill text exceeds maximum length");
    }

    // Process sanitized input
    processSanitizedText(sanitizedText);
}
```

### Secure Coding Practices
- **SQL Injection Prevention**: Use parameterized queries
- **XSS Prevention**: Sanitize user inputs and outputs
- **Authentication**: Proper session management
- **Authorization**: Role-based access control
- **Encryption**: Encrypt sensitive data at rest and in transit

## Code Review Checklist

### General
- [ ] Code follows naming conventions
- [ ] No hardcoded values (use constants or configuration)
- [ ] No TODO comments without tickets
- [ ] No commented-out code
- [ ] Appropriate logging levels used

### Structure
- [ ] Classes have single responsibility
- [ ] Methods are small and focused
- [ ] Dependencies are injected (not hardcoded)
- [ ] No circular dependencies

### Documentation
- [ ] Public APIs have JavaDoc
- [ ] Complex logic has inline comments
- [ ] Class-level documentation exists

### Testing
- [ ] Unit tests exist for business logic
- [ ] Edge cases are covered
- [ ] Test names are descriptive
- [ ] Tests are independent

### Security
- [ ] Input validation implemented
- [ ] No sensitive data logged
- [ ] Secure coding practices followed
- [ ] Dependencies scanned for vulnerabilities

## Tooling

### Code Quality Tools
- **Spotless**: Code formatting
- **PMD**: Code analysis
- **Checkstyle**: Style checking
- **SonarQube**: Comprehensive analysis

### IDE Configuration
- **IntelliJ IDEA**: Project-specific settings
- **Eclipse**: Formatter and cleanup rules
- **VS Code**: Extension recommendations

## Continuous Improvement

### Code Quality Metrics
- **Maintainability Index**: > 70
- **Technical Debt Ratio**: < 5%
- **Duplication**: < 3%
- **Test Coverage**: > 80%

### Regular Reviews
- **Monthly**: Code quality metrics review
- **Quarterly**: Standards compliance audit
- **Annually**: Standards update and revision

This document establishes the baseline for code quality and must be enforced through automated tools and code review processes.