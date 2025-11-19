# Development Guide

## Development Environment Setup

### Prerequisites

- **Node.js**: 18.x or higher
- **Python**: 3.9 or higher
- **PostgreSQL**: 13.x or higher
- **Elasticsearch**: 8.x or higher
- **Redis**: 6.x or higher
- **Docker**: 20.x or higher
- **Git**: 2.30 or higher

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/openlegislation/OpenLegislation.git
cd OpenLegislation

# Install frontend dependencies
cd frontend
npm install
cd ..

# Install backend dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Setup database
createdb openlegislation
python manage.py migrate

# Start development services
docker-compose up -d elasticsearch redis postgres
```

## Project Structure

```
OpenLegislation/
├── frontend/                 # Next.js frontend application
│   ├── app/                 # App Router pages and layouts
│   ├── components/          # Reusable React components
│   ├── lib/                 # Utility functions and configurations
│   └── styles/              # Global styles and Tailwind CSS
├── src/                     # Backend Python application
│   ├── main/               # Main application entry point
│   ├── api/                # API endpoints and handlers
│   ├── db/                 # Database models and connections
│   ├── pipeline/           # Data processing pipelines
│   └── compliance/         # Compliance checking modules
├── tools/                   # Data ingestion and processing tools
├── docs/                    # Documentation
├── tests/                   # Test suites
└── deploy/                  # Deployment configurations
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... develop your feature ...

# Run tests
npm test                    # Frontend tests
python manage.py test       # Backend tests

# Run linting
npm run lint               # Frontend linting
flake8 src/                # Backend linting

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### 2. Code Review Process

- All code changes require pull request review
- Automated tests must pass
- Code coverage must not decrease
- Security scans must pass
- Documentation must be updated

### 3. Testing Strategy

#### Frontend Testing
```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Coverage report
npm run test:coverage
```

#### Backend Testing
```bash
# Unit tests
python manage.py test

# Integration tests
python manage.py test --integration

# API tests
python manage.py test --api

# Coverage report
coverage run --source='.' manage.py test
coverage report
```

## Coding Standards

### Frontend (TypeScript/React)

```typescript
// Component naming: PascalCase
export const BillSearchComponent: React.FC<BillSearchProps> = ({ 
  onSearch,
  filters 
}) => {
  // Hook usage at top level
  const [searchTerm, setSearchTerm] = useState<string>('');
  const { data, loading, error } = useBillSearch(searchTerm);
  
  // Event handlers
  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    onSearch?.(term);
  }, [onSearch]);
  
  return (
    <div className="bill-search">
      {/* JSX content */}
    </div>
  );
};
```

### Backend (Python)

```python
# Class naming: PascalCase
class BillProcessor:
    """Process legislative bills from various sources."""
    
    def __init__(self, config: ProcessorConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def process_bill(self, bill_data: Dict[str, Any]) -> Bill:
        """Process a single bill with validation."""
        try:
            # Validate input data
            validated_data = self._validate_bill_data(bill_data)
            
            # Create bill instance
            bill = Bill(**validated_data)
            
            # Save to database
            await bill.asave()
            
            return bill
            
        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Processing error: {e}")
            raise ProcessingError(f"Failed to process bill: {e}")
```

## Database Development

### Migrations

```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Database Seeding

```bash
# Seed development data
python manage.py seed_dev_data

# Seed test data
python manage.py seed_test_data

# Reset database
python manage.py reset_db
```

## API Development

### REST API Standards

```python
# API endpoint structure
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bill_list(request):
    """
    List all bills with optional filtering.
    
    Query Parameters:
        - state: Filter by state (optional)
        - chamber: Filter by chamber (optional)
        - session: Filter by session year (optional)
    """
    try:
        queryset = Bill.objects.all()
        
        # Apply filters
        state = request.query_params.get('state')
        if state:
            queryset = queryset.filter(state__abbreviation=state)
        
        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        # Serialization
        serializer = BillSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### GraphQL API

```python
# GraphQL schema definition
class BillType(DjangoObjectType):
    class Meta:
        model = Bill
        fields = '__all__'
    
    def resolve_sponsor(self, info):
        """Resolve sponsor with caching."""
        return cache.get_or_set(
            f'bill_sponsor_{self.id}',
            lambda: self.sponsor,
            timeout=3600
        )

class Query(graphene.ObjectType):
    bills = graphene.List(BillType, state=graphene.String())
    
    def resolve_bills(self, info, state=None):
        queryset = Bill.objects.all()
        if state:
            queryset = queryset.filter(state__abbreviation=state)
        return queryset
```

## Performance Optimization

### Frontend Optimization

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
});

// Virtual scrolling for large lists
const VirtualBillList = ({ bills }: { bills: Bill[] }) => {
  return (
    <FixedSizeList
      height={600}
      itemCount={bills.length}
      itemSize={80}
      itemData={bills}
    >
      {BillListItem}
    </FixedSizeList>
  );
};
```

### Backend Optimization

```python
# Database query optimization
def get_bills_with_sponsors(state: str = None):
    """Get bills with optimized queries."""
    queryset = Bill.objects.select_related('sponsor', 'state')
    
    if state:
        queryset = queryset.filter(state__abbreviation=state)
    
    return queryset.annotate(
        action_count=Count('actions'),
        vote_count=Count('votes')
    )

# Caching strategy
from django.core.cache import cache

def get_bill_stats(state: str):
    """Get bill statistics with caching."""
    cache_key = f'bill_stats_{state}'
    stats = cache.get(cache_key)
    
    if not stats:
        stats = calculate_bill_stats(state)
        cache.set(cache_key, stats, timeout=3600)
    
    return stats
```

## Security Best Practices

### Input Validation

```python
# Backend validation
from django.core.validators import RegexValidator
from rest_framework import serializers

class BillSerializer(serializers.ModelSerializer):
    bill_number = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r'^[A-Z]+\d+$',
                message='Bill number must be in format like "HR123"'
            )
        ]
    )
    
    class Meta:
        model = Bill
        fields = ['bill_number', 'title', 'content']
```

```typescript
// Frontend validation
import { z } from 'zod';

const billSearchSchema = z.object({
  searchTerm: z.string().min(1, 'Search term is required'),
  state: z.string().optional(),
  chamber: z.enum(['upper', 'lower']).optional(),
});

type BillSearchForm = z.infer<typeof billSearchSchema>;
```

### Authentication & Authorization

```python
# JWT Authentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

class BillViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Filter based on user permissions
        user = self.request.user
        if user.is_staff:
            return Bill.objects.all()
        return Bill.filter_by_user_access(user)
```

## Monitoring and Debugging

### Logging Configuration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/openlegislation.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'openlegislation': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Performance Monitoring

```python
# Middleware for request timing
import time
from django.utils.deprecation import MiddlewareMixin

class TimingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        duration = time.time() - request.start_time
        logger.info(f"Request to {request.path} took {duration:.2f}s")
        return response
```

## Deployment

### Development Deployment

```bash
# Using Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# Manual setup
python manage.py runserver 0.0.0.0:8000
cd frontend && npm run dev
```

### Production Deployment

```bash
# Build frontend
cd frontend
npm run build
npm run start

# Backend with Gunicorn
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   docker-compose ps postgres
   
   # Check connection
   python manage.py dbshell
   ```

2. **Elasticsearch Issues**
   ```bash
   # Check cluster health
   curl -X GET "localhost:9200/_cluster/health"
   
   # Rebuild index
   python manage.py rebuild_index
   ```

3. **Frontend Build Errors**
   ```bash
   # Clear node modules
   rm -rf node_modules package-lock.json
   npm install
   
   # Check TypeScript errors
   npm run type-check
   ```

### Debug Mode

```python
# Enable debug mode
DEBUG = True

# Django debug toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

## Contributing Guidelines

### Before Submitting

1. **Code Quality**: Ensure all linting checks pass
2. **Tests**: Maintain or improve test coverage
3. **Documentation**: Update relevant documentation
4. **Performance**: Consider performance implications
5. **Security**: Follow security best practices

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

This development guide provides comprehensive standards and workflows for contributing to the OpenLegislation platform, ensuring consistency, quality, and maintainability across the entire codebase.