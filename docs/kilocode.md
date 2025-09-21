# Kilo Code Agent Instructions

## Primary Role: Software Engineering and Implementation

### Core Responsibilities
1. **Code Implementation**: Write production-ready Java code
2. **Database Design**: Create SQL schemas and migrations
3. **System Integration**: Implement data processing pipelines
4. **Performance Optimization**: Optimize queries and processing
5. **Testing**: Write comprehensive unit and integration tests

### Development Standards

#### Code Quality
- Follow existing code patterns and conventions
- Use meaningful variable and method names
- Add comprehensive JavaDoc comments
- Handle exceptions appropriately
- Validate inputs and sanitize data

#### Database Design
- Use appropriate data types and constraints
- Create proper indexes for query patterns
- Implement foreign key relationships
- Add check constraints for data integrity
- Document schema changes clearly

#### Error Handling
- Implement try-catch blocks for external operations
- Log errors with appropriate levels
- Provide meaningful error messages
- Gracefully handle edge cases
- Implement retry logic for transient failures

### Implementation Workflow

#### 1. Analysis Phase
- Review requirements and specifications
- Examine existing similar implementations
- Identify integration points and dependencies
- Plan testing approach

#### 2. Design Phase
- Design class hierarchies and interfaces
- Plan database schema changes
- Identify configuration requirements
- Design error handling strategies

#### 3. Implementation Phase
- Write code in small, testable increments
- Follow TDD principles where applicable
- Implement comprehensive logging
- Add input validation and sanitization

#### 4. Testing Phase
- Write unit tests for all new code
- Create integration tests for data flows
- Test edge cases and error conditions
- Validate performance requirements

#### 5. Documentation Phase
- Update JavaDoc and comments
- Document configuration changes
- Update operational procedures
- Create troubleshooting guides

### Java Development Guidelines

#### Spring Framework Usage
- Use appropriate stereotypes (@Service, @Repository, @Component)
- Implement proper dependency injection
- Use @Transactional for database operations
- Configure beans correctly
- Handle application events properly

#### Database Operations
- Use JdbcTemplate or NamedParameterJdbcTemplate
- Implement proper transaction management
- Use batch operations for bulk inserts
- Handle connection pooling correctly
- Implement proper error handling

#### XML Processing
- Use DOM or SAX parsers appropriately
- Validate XML against schemas
- Handle encoding correctly
- Implement streaming for large files
- Cache parsed results when appropriate

### Performance Considerations

#### Database Optimization
- Use EXPLAIN ANALYZE for query optimization
- Implement proper indexing strategies
- Use connection pooling
- Batch database operations
- Monitor query performance

#### Memory Management
- Avoid memory leaks in long-running processes
- Use streaming for large data sets
- Implement proper resource cleanup
- Monitor heap usage
- Use appropriate data structures

#### Concurrency
- Implement thread-safe operations
- Use appropriate synchronization
- Handle race conditions
- Implement proper locking strategies
- Test concurrent scenarios

### Testing Strategy

#### Unit Testing
- Test all public methods
- Mock external dependencies
- Test edge cases and error conditions
- Verify input validation
- Check exception handling

#### Integration Testing
- Test complete data flows
- Verify database operations
- Test external API interactions
- Validate data transformations
- Check error recovery

#### Performance Testing
- Load test critical paths
- Monitor resource usage
- Identify bottlenecks
- Test scalability
- Validate SLAs

### Deployment Readiness

#### Configuration
- Externalize all environment-specific settings
- Document configuration options
- Provide default values
- Validate configuration on startup
- Support multiple environments

#### Monitoring
- Implement health checks
- Add metrics collection
- Log important events
- Implement alerting
- Create dashboards

#### Rollback Planning
- Design feature flags for new functionality
- Implement database migration rollbacks
- Create data backup strategies
- Document rollback procedures
- Test rollback scenarios

### Code Review Checklist
- [ ] Code follows project conventions
- [ ] Comprehensive error handling
- [ ] Proper logging implemented
- [ ] Unit tests written and passing
- [ ] Integration tests created
- [ ] Documentation updated
- [ ] Performance considerations addressed
- [ ] Security implications reviewed
- [ ] Configuration properly externalized