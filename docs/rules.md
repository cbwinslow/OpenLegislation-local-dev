# Development Rules and Standards

## Code of Conduct

### Core Principles

1. **Collaboration First**: We work together to build the best possible platform
2. **Respect**: Treat all contributors with dignity and respect
3. **Inclusivity**: Welcome contributors from all backgrounds and experience levels
4. **Quality**: Maintain high standards for code, documentation, and user experience
5. **Transparency**: Be open about decisions, changes, and challenges

### Communication Guidelines

- Use constructive and professional language in all communications
- Assume good intent from others
- Focus on what is best for the community
- Show empathy towards other community members
- Be respectful of differing viewpoints and experiences

### Ethical Guidelines
- Ensure data privacy and security
- Maintain transparency in decision-making
- Use resources responsibly
- Comply with legal and regulatory requirements
- Protect intellectual property rights

## Coding Standards

### General Principles

1. **Readability**: Code should be easy to read and understand
2. **Consistency**: Follow established patterns and conventions
3. **Simplicity**: Favor simple solutions over complex ones
4. **Maintainability**: Write code that others can easily modify
5. **Performance**: Consider performance implications without premature optimization

### Frontend Standards (TypeScript/React)

#### File Naming
```
Components:      PascalCase.tsx (BillCard.tsx, SearchForm.tsx)
Utilities:       camelCase.ts (formatDate.ts, apiClient.ts)
Types:           camelCase.types.ts (bill.types.ts, user.types.ts)
Hooks:           camelCase.ts (useBillData.ts, useAuth.ts)
Constants:       UPPER_SNAKE_CASE.ts (API_ENDPOINTS.ts, ERROR_MESSAGES.ts)
```

#### Component Structure
```typescript
// 1. Imports (external libraries first, then internal)
import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button, Card } from '@/components/ui';
import { Bill, BillStatus } from '@/types';
import { billApi } from '@/lib/api';
import { formatDate } from '@/lib/utils';

// 2. Types/Interfaces
interface BillCardProps {
  bill: Bill;
  onSelect?: (billId: string) => void;
  className?: string;
}

// 3. Component definition
export const BillCard: React.FC<BillCardProps> = ({ 
  bill, 
  onSelect, 
  className = '' 
}) => {
  // 4. Hooks (in order: state, effects, callbacks, memoized values)
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  
  useEffect(() => {
    // Side effects
  }, [bill.id]);
  
  const handleSelect = useCallback(() => {
    if (onSelect) {
      onSelect(bill.id);
    } else {
      router.push(`/bills/${bill.id}`);
    }
  }, [bill.id, onSelect, router]);
  
  const statusColor = useMemo(() => {
    return bill.status === BillStatus.PASSED ? 'green' : 'blue';
  }, [bill.status]);
  
  // 5. Render
  return (
    <Card className={`bill-card ${className}`}>
      {/* JSX content */}
    </Card>
  );
};

export default BillCard;
```

#### TypeScript Rules
```typescript
// Use explicit types for function parameters and return values
const searchBills = async (query: string): Promise<Bill[]> => {
  // Implementation
};

// Prefer interfaces over types for object shapes
interface User {
  id: string;
  name: string;
  email: string;
}

// Use union types for enums
type BillStatus = 'introduced' | 'passed' | 'failed' | 'vetoed';

// Use generics for reusable components
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
}

function List<T>({ items, renderItem }: ListProps<T>) {
  return (
    <div>
      {items.map(renderItem)}
    </div>
  );
}
```

### Backend Standards (Python)

#### File Naming
```
Models:          PascalCase.py (Bill.py, User.py, Committee.py)
Views/Handlers:  PascalCase.py (BillViewSet.py, UserHandler.py)
Utilities:       snake_case.py (bill_utils.py, date_helpers.py)
Tests:           test_PascalCase.py (test_Bill.py, test_UserAPI.py)
Management:      snake_case.py (seed_dev_data.py, rebuild_index.py)
```

#### Class Structure
```python
# 1. Imports (standard library first, then third-party, then local)
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from django.db import models
from django.core.cache import cache
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import Bill, Sponsor
from .serializers import BillSerializer
from .utils import format_bill_number, validate_bill_data

# 2. Logger setup
logger = logging.getLogger(__name__)

# 3. Class/Function definitions with docstrings
class BillProcessor:
    """
    Process legislative bills from various data sources.
    
    Handles validation, normalization, and storage of bill data
    from federal, state, and local legislative bodies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the bill processor.
        
        Args:
            config: Configuration dictionary for processing options
        """
        self.config = config or {}
        self.cache_timeout = self.config.get('cache_timeout', 3600)
    
    async def process_bill(self, bill_data: Dict[str, Any]) -> Bill:
        """
        Process a single bill from raw data.
        
        Args:
            bill_data: Raw bill data from external source
            
        Returns:
            Bill: Processed and saved bill instance
            
        Raises:
            ValidationError: If bill data is invalid
            ProcessingError: If processing fails
        """
        try:
            # Validate input data
            validated_data = await self._validate_bill_data(bill_data)
            
            # Create bill instance
            bill = await self._create_bill(validated_data)
            
            # Process related data
            await self._process_sponsors(bill, validated_data.get('sponsors', []))
            await self._process_actions(bill, validated_data.get('actions', []))
            
            # Cache bill data
            await self._cache_bill(bill)
            
            logger.info(f"Successfully processed bill: {bill.bill_number}")
            return bill
            
        except ValidationError as e:
            logger.error(f"Validation error for bill {bill_data.get('number')}: {e}")
            raise
        except Exception as e:
            logger.error(f"Processing error for bill {bill_data.get('number')}: {e}")
            raise ProcessingError(f"Failed to process bill: {e}")
```

### Code Quality Standards
- Write clean, readable, and maintainable code
- Follow established coding conventions
- Implement comprehensive error handling
- Add meaningful comments and documentation
- Use consistent naming conventions
- Keep functions and classes small and focused
- Use design patterns appropriately
- Follow SOLID principles

## Testing Standards

### Frontend Testing

#### Unit Tests
```typescript
// Component testing with React Testing Library
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BillCard } from './BillCard';
import { Bill } from '@/types';

const mockBill: Bill = {
  id: '1',
  number: 'HR123',
  title: 'Test Bill',
  status: 'introduced',
  sponsor: { name: 'John Doe', id: '1' },
};

describe('BillCard', () => {
  it('renders bill information correctly', () => {
    render(<BillCard bill={mockBill} />);
    
    expect(screen.getByText('HR123')).toBeInTheDocument();
    expect(screen.getByText('Test Bill')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });
  
  it('calls onSelect when clicked', () => {
    const mockOnSelect = jest.fn();
    render(<BillCard bill={mockBill} onSelect={mockOnSelect} />);
    
    fireEvent.click(screen.getByRole('button'));
    expect(mockOnSelect).toHaveBeenCalledWith('1');
  });
});
```

#### Integration Tests
```typescript
// API integration testing
import { renderHook, act } from '@testing-library/react-hooks';
import { useBillSearch } from './useBillSearch';
import { billApi } from '@/lib/api';

jest.mock('@/lib/api');
const mockBillApi = billApi as jest.Mocked<typeof billApi>;

describe('useBillSearch', () => {
  it('searches bills successfully', async () => {
    const mockBills = [mockBill];
    mockBillApi.searchBills.mockResolvedValue(mockBills);
    
    const { result, waitForNextUpdate } = renderHook(() => useBillSearch());
    
    act(() => {
      result.current.search('test query');
    });
    
    expect(result.current.loading).toBe(true);
    
    await waitForNextUpdate();
    
    expect(result.current.loading).toBe(false);
    expect(result.current.bills).toEqual(mockBills);
  });
});
```

### Backend Testing

#### Unit Tests
```python
# Model testing
from django.test import TestCase
from django.core.exceptions import ValidationError
from ..models import Bill, Sponsor, State

class BillModelTest(TestCase):
    def setUp(self):
        self.state = State.objects.create(
            name='California',
            abbreviation='CA'
        )
        self.sponsor = Sponsor.objects.create(
            name='John Doe',
            email='john.doe@ca.gov'
        )
    
    def test_bill_creation(self):
        """Test successful bill creation."""
        bill = Bill.objects.create(
            bill_number='AB123',
            title='Test Bill',
            state=self.state,
            sponsor=self.sponsor
        )
        
        self.assertEqual(bill.bill_number, 'AB123')
        self.assertEqual(bill.title, 'Test Bill')
```

#### API Testing
```python
# API endpoint testing
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class BillAPITest(APITestCase):
    def test_get_bill_list(self):
        """Test retrieving list of bills."""
        url = reverse('bill-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
```

### Testing Requirements
- Write unit tests for all new functionality
- Maintain > 80% code coverage
- Include integration tests for critical paths
- Perform manual testing for user-facing features
- Document test cases and procedures
- Test error conditions and edge cases
- Use test-driven development (TDD) when appropriate
- Automate testing in CI/CD pipeline

### Documentation Standards

### Code Documentation
```python
def process_legislative_data(
    data_source: str,
    session_year: int,
    data_format: str = 'json'
) -> ProcessingResult:
    """
    Process legislative data from various sources.
    
    This function handles the ingestion, validation, and storage of legislative
    data from federal, state, and local sources. It supports multiple data formats
    and provides comprehensive error handling and logging.
    
    Args:
        data_source: Identifier for the data source (e.g., 'congress.gov', 'ny.gov')
        session_year: Legislative session year for the data
        data_format: Format of the input data ('json', 'xml', 'csv')
        
    Returns:
        ProcessingResult: Object containing processing statistics and status
        
    Raises:
        DataSourceError: If the data source is unavailable or invalid
        ValidationError: If the data format is invalid or corrupted
        ProcessingError: If processing fails due to system errors
        
    Example:
        >>> result = process_legislative_data('congress.gov', 2023)
        >>> print(f"Processed {result.records_processed} records")
        Processed 15420 records
    """
    pass
```

### API Documentation
```python
# DRF serializer with detailed documentation
class BillSerializer(serializers.ModelSerializer):
    """
    Serializer for legislative bills.
    
    Handles serialization/deserialization of bill data including validation,
    field transformations, and relationship handling.
    """
    
    bill_number = serializers.CharField(
        help_text="Official bill number (e.g., 'HR123', 'AB456')",
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{1,4}\d+$',
                message="Bill number must contain letters followed by numbers"
            )
        ]
    )
    
    title = serializers.CharField(
        help_text="Full title of the bill",
        max_length=1000,
        style={'base_template': 'textarea.html'}
    )
```

### Documentation Requirements
- Document all public APIs and interfaces
- Maintain up-to-date README files
- Create user guides and tutorials
- Document architectural decisions
- Keep changelog current
- Include code examples
- Document configuration options
- Provide troubleshooting guides
- Document deployment procedures
- Include performance benchmarks
- Document security considerations
- Provide API reference documentation

## Git Workflow

### Branch Naming Conventions

```bash
# Feature branches
feature/bill-search-enhancement
feature/user-authentication
feature/api-performance-optimization

# Bugfix branches
bugfix/bill-number-validation
bugfix/memory-leak-in-search
bugfix/css-responsive-issues

# Hotfix branches (for production issues)
hotfix/security-vulnerability-patch
hotfix/critical-data-corruption-fix

# Release branches
release/v1.2.0
release/v2.0.0-beta

# Documentation branches
docs/api-documentation-update
docs/developer-guide-enhancement
```

### Commit Message Standards

```bash
# Format: <type>(<scope>): <description>

# Types
feat:     New feature
fix:      Bug fix
docs:     Documentation changes
style:    Code formatting, missing semicolons, etc.
refactor: Code refactoring without functional changes
test:     Adding or updating tests
chore:    Maintenance tasks, dependency updates
perf:     Performance improvements
security: Security-related changes

# Examples
feat(api): add bill search endpoint with filtering
fix(frontend): resolve memory leak in bill list component
docs(readme): update installation instructions for Python 3.9+
refactor(database): optimize bill query with select_related
test(api): add integration tests for bill endpoints
chore(deps): update React from 18.2.0 to 18.3.0
perf(search): implement caching for search results
security(auth): add rate limiting to login endpoint
```

### Git Workflow Process
- Use feature branches for development
- Write clear, descriptive commit messages
- Keep commits focused and atomic
- Rebase feature branches before merging
- Use pull requests for code review
- Protect main/master branch
- Use semantic versioning for releases

## Code Review Process

### Review Guidelines
- Review code for functionality, not style preferences
- Provide specific, actionable feedback
- Suggest improvements, don't dictate changes
- Approve only when requirements are met
- Use automated tools for style checking
- Be constructive and respectful in feedback
- Focus on learning and improvement

### Pull Request Template
```markdown
## Description
Brief description of changes and their purpose.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance testing completed (if applicable)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Security considerations addressed
- [ ] Performance implications considered

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Additional Notes
Any additional context or considerations.
```

### Review Checklist
- [ ] Code follows project conventions
- [ ] Unit tests included and passing
- [ ] Documentation updated
- [ ] Security considerations addressed
- [ ] Performance implications reviewed
- [ ] Accessibility requirements met
- [ ] Error handling implemented
- [ ] Logging and monitoring added
- [ ] Database migrations included (if needed)
- [ ] API documentation updated (if applicable)

## Security Standards

### Input Validation
```python
# Backend validation
from django.core.validators import RegexValidator
from rest_framework import serializers

class BillSerializer(serializers.ModelSerializer):
    bill_number = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{1,4}\d+$',
                message='Bill number must be in format like "HR123" or "AB456"'
            )
        ],
        max_length=10
    )
    
    title = serializers.CharField(
        max_length=500,
        min_length=5,
        error_messages={
            'required': 'Bill title is required',
            'min_length': 'Bill title must be at least 5 characters long',
            'max_length': 'Bill title cannot exceed 500 characters'
        }
    )
```

```typescript
// Frontend validation
import { z } from 'zod';

export const billSearchSchema = z.object({
  searchTerm: z
    .string()
    .min(1, 'Search term is required')
    .max(100, 'Search term cannot exceed 100 characters')
    .regex(/^[a-zA-Z0-9\s\-]+$/, 'Search term contains invalid characters'),
  
  state: z
    .string()
    .length(2, 'State must be a 2-letter abbreviation')
    .optional(),
  
  chamber: z
    .enum(['upper', 'lower'], {
      errorMap: () => ({ message: 'Chamber must be either "upper" or "lower"' })
    })
    .optional(),
});

export type BillSearchForm = z.infer<typeof billSearchSchema>;
```

### Authentication & Authorization
```python
# Permission classes
from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    """Custom permission to only allow owners of an object to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.owner == request.user

class IsAdminUserOrReadOnly(BasePermission):
    """Custom permission to only allow admin users to edit."""
    
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        return request.user and request.user.is_staff
```

### Data Protection
- Never commit sensitive data to version control
- Use environment variables for secrets
- Encrypt sensitive data at rest
- Implement proper access controls
- Regular security audits
- Use HTTPS for all communications
- Implement rate limiting
- Log security events
- Regular penetration testing

### Secure Coding
- Validate all input data
- Use parameterized queries
- Implement proper authentication
- Follow OWASP guidelines
- Regular dependency updates
- Use secure headers
- Implement CSRF protection
- Sanitize user input
- Use prepared statements
- Implement proper session management

## Performance Standards

### Application Performance
- API response time < 500ms for 95th percentile
- Page load time < 3 seconds
- Database query time < 100ms for common operations
- Support 1000+ concurrent users
- Mobile page load time < 2 seconds
- Search response time < 200ms

### Frontend Performance
```typescript
// Code splitting
const BillSearch = lazy(() => import('./components/BillSearch'));
const BillDetails = lazy(() => import('./components/BillDetails'));

// Memoization
const BillListItem = memo(({ bill, onSelect }: BillListItemProps) => {
  return (
    <div onClick={() => onSelect(bill.id)}>
      {bill.number}: {bill.title}
    </div>
  );
}, (prevProps, nextProps) => {
  return prevProps.bill.id === nextProps.bill.id && 
         prevProps.onSelect === nextProps.onSelect;
});

// Virtual scrolling for large lists
import { FixedSizeList as List } from 'react-window';

const VirtualBillList = ({ bills }: { bills: Bill[] }) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <BillListItem bill={bills[index]} onSelect={handleSelect} />
    </div>
  );
  
  return (
    <List
      height={600}
      itemCount={bills.length}
      itemSize={80}
    >
      {Row}
    </List>
  );
};
```

### Backend Performance
```python
# Database optimization
from django.db.models import Prefetch, Count, Avg
from django.core.cache import cache

def get_bills_with_optimization(state: str = None):
    """Get bills with optimized database queries."""
    queryset = Bill.objects.select_related(
        'state', 'sponsor', 'current_committee'
    ).prefetch_related(
        Prefetch('actions', queryset=BillAction.objects.order_by('-date')),
        Prefetch('sponsors', queryset=Sponsor.objects.select_related('state'))
    ).annotate(
        action_count=Count('actions'),
        sponsor_count=Count('sponsors'),
        avg_action_date=Avg('actions__date')
    )
    
    if state:
        queryset = queryset.filter(state__abbreviation=state)
    
    return queryset

# Caching strategy
def get_bill_statistics(state: str, force_refresh: bool = False):
    """Get bill statistics with intelligent caching."""
    cache_key = f'bill_stats_{state}_{datetime.now().strftime("%Y%m%d")}'
    
    if force_refresh:
        cache.delete(cache_key)
    
    stats = cache.get(cache_key)
    
    if not stats:
        stats = calculate_expensive_statistics(state)
        cache.set(cache_key, stats, timeout=3600 * 24)  # Cache for 24 hours
    
    return stats
```

### Code Performance
- Optimize algorithms and data structures
- Minimize database queries
- Use caching appropriately
- Monitor memory usage
- Profile performance bottlenecks
- Use connection pooling
- Implement lazy loading
- Optimize images and assets
- Use CDNs for static content
- Implement database indexing
- Monitor and optimize database queries
- Use background processing for heavy tasks

## Deployment and Operations

### Environment Standards

### Development Environment
```bash
# Required versions
Node.js: >= 18.0.0
Python: >= 3.9.0
PostgreSQL: >= 13.0
Elasticsearch: >= 8.0
Redis: >= 6.0

# Development tools
ESLint: >= 8.0.0
Prettier: >= 2.0.0
Black: >= 22.0.0
Flake8: >= 4.0.0
```

### Environment Variables
```bash
# Database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/openlegislation
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Cache configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# External APIs
CONGRESS_GOV_API_KEY=your_api_key_here
NY_STATE_API_KEY=your_api_key_here

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here

# Feature flags
ENABLE_FEDERAL_DATA=true
ENABLE_AI_FEATURES=true
ENABLE_REAL_TIME_UPDATES=false
```

### Environment Configuration
- Development: Local development environment
- Staging: Pre-production testing environment
- Production: Live system environment
- All environments must be identical in configuration
- Use environment-specific configuration files
- Implement proper secret management
- Use containerization for consistency
- Monitor environment health
- Implement proper logging per environment
- Use feature flags for controlled rollouts

### Deployment Process
- Automated deployment through CI/CD
- Zero-downtime deployments
- Rollback capability
- Environment-specific configurations
- Post-deployment verification

## Data Management

### Data Quality
- Validate data integrity
- Implement data quality checks
- Monitor data accuracy
- Handle data inconsistencies
- Document data lineage

### Backup and Recovery
- Daily automated backups
- Test backup restoration
- Offsite backup storage
- Point-in-time recovery capability
- Disaster recovery plan

## Communication Guidelines

### Internal Communication
- Use appropriate channels for different topics
- Keep discussions focused and productive
- Document decisions and action items
- Follow up on commitments
- Maintain transparency

### External Communication
- Professional and courteous
- Clear and concise
- Accurate information
- Timely responses
- Appropriate level of detail

## Change Management

### Change Process
- Document all changes
- Assess impact of changes
- Test changes thoroughly
- Communicate changes to stakeholders
- Provide training when necessary

### Risk Assessment
- Identify potential risks
- Assess probability and impact
- Develop mitigation strategies
- Monitor risk indicators
- Update risk assessments regularly

## Continuous Improvement

### Learning and Development
- Regular training and skill development
- Knowledge sharing sessions
- Process improvement initiatives
- Technology evaluation
- Industry best practices adoption

### Metrics and Measurement
- Track key performance indicators
- Monitor process effectiveness
- Gather feedback regularly
- Analyze trends and patterns
- Implement improvements based on data

## Compliance and Legal

### Legal Compliance
- Comply with data protection laws
- Respect intellectual property
- Follow open source licensing
- Maintain records as required
- Report incidents appropriately

### Regulatory Compliance
- Government data standards
- Accessibility requirements
- Privacy regulations
- Security standards
- Industry-specific regulations

## Emergency Procedures

### Incident Response
- Identify incident types
- Establish response procedures
- Define roles and responsibilities
- Communication protocols
- Recovery procedures

### Business Continuity
- Identify critical functions
- Develop continuity plans
- Test continuity procedures
- Maintain redundant systems
- Regular plan updates

## Quality Assurance

### Quality Standards
- Meet all requirements
- Follow established processes
- Maintain quality metrics
- Continuous quality improvement
- Customer satisfaction focus

### Audit and Review
- Regular code audits
- Process reviews
- Quality assessments
- Compliance audits
- Improvement recommendations

## Resource Management

### Time Management
- Estimate tasks accurately
- Track time spent
- Meet deadlines
- Prioritize effectively
- Manage workload

### Resource Allocation
- Plan resource needs
- Monitor resource usage
- Optimize resource utilization
- Budget management
- Cost control

## Conclusion

These rules and guidelines provide the foundation for successful project execution. All team members are expected to follow these guidelines and contribute to their continuous improvement. Regular review and updates ensure they remain relevant and effective.