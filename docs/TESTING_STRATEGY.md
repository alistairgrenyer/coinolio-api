# FastAPI Testing Strategy

## Overview

This document outlines our testing strategy for the Coinolio API, focusing on comprehensive testing of FastAPI endpoints while maintaining clean, maintainable tests.

## Implementation Status

### Completed
1. **Authentication Tests**
   - User registration
   - Login functionality
   - Token refresh mechanism
   - Current user retrieval
   - Error handling scenarios

2. **Portfolio Tests**
   - Portfolio CRUD operations
   - Version history tracking
   - Cloud sync functionality
   - Subscription tier checks
   - Error handling scenarios

3. **Test Infrastructure**
   - SQLite in-memory database setup
   - Custom JSON type handling for SQLite compatibility
   - Test fixtures and factories
   - Database session management

### Pending
1. **Additional Test Coverage**
   - Subscription management endpoints
   - Rate limiting functionality
   - External API integrations (CoinGecko)
   - Caching layer tests
   - Background task tests

## Test Structure

```plaintext
tests/
├── conftest.py              # Shared fixtures and DB setup
├── factories/               # Test data factories
│   ├── user.py             # User factory
│   └── portfolio.py        # Portfolio factory
├── unit/                   # Unit tests
│   └── api/
│       └── v1/
│           └── endpoints/
│               ├── test_auth.py       # Auth tests
│               └── test_portfolios.py # Portfolio tests
└── utils/                  # Test utilities
    └── db.py              # SQLite compatibility layer
```

## Key Components

### 1. Database Strategy
- Using SQLite for testing instead of PostgreSQL
- Custom JSON type handling for PostgreSQL JSONB compatibility
- In-memory database for fast test execution
- Automatic schema creation for each test

### 2. Test Data Management
```python
class PortfolioFactory(factory.Factory):
    class Meta:
        model = Portfolio
        exclude = ('_sa_instance_state',)

    name = factory.Faker('company')
    description = factory.Faker('catch_phrase')
    is_cloud_synced = False
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    # ... more fields
```

### 3. Fixtures
```python
@pytest.fixture
def test_user(client, test_user_data):
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json=test_user_data
    )
    return response.json()
```

### 4. Test Cases
1. **Authentication**
   - Registration success/failure
   - Login validation
   - Token refresh flow
   - User data retrieval

2. **Portfolio Management**
   - Portfolio creation/update
   - Version tracking
   - Cloud sync (Premium feature)
   - Subscription tier validation

## Best Practices Implemented

1. **Database Handling**
   - Use transactions for test isolation
   - Clean up after each test
   - Use in-memory database for speed

2. **Test Organization**
   - Group related tests in classes
   - Clear test naming conventions
   - Shared fixtures in conftest.py

3. **Data Management**
   - Factory Boy for test data generation
   - Faker for realistic test data
   - Isolated test data per test

4. **Error Handling**
   - Test both success and failure cases
   - Validate error messages
   - Check HTTP status codes

## SQLite vs PostgreSQL Considerations

### Handling PostgreSQL-Specific Types
```python
class SqliteJson(TypeDecorator):
    """Enables JSON storage by encoding and decoding on the fly."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None
```

### Production vs Test Environment
- Production: PostgreSQL with JSONB support
- Testing: SQLite with JSON string storage
- Automatic type selection based on environment

## Test Execution

Running specific test files:
```bash
pytest tests/unit/api/v1/endpoints/test_auth.py -v
pytest tests/unit/api/v1/endpoints/test_portfolios.py -v
```

Running with coverage:
```bash
pytest --cov=app tests/
```

## Next Steps

1. **Additional Test Coverage**
   - Subscription management tests
   - Rate limiting tests
   - External API mocking
   - Cache integration tests

2. **Performance Testing**
   - Load test scenarios
   - Benchmark critical endpoints
   - Test caching effectiveness

3. **Integration Testing**
   - External API mocking
   - Database performance
   - Cache integration

4. **CI/CD Integration**
   - Add GitHub Actions workflow
   - Automated test execution
   - Coverage reporting

## Lessons Learned

1. **SQLite for Testing**
   - Pros: Fast, in-memory, no setup required
   - Cons: Limited PostgreSQL feature support
   - Solution: Custom type decorators

2. **Form Data vs JSON**
   - FastAPI form handling specifics
   - Token refresh requirements
   - Request content-type importance

3. **Test Organization**
   - Importance of clear structure
   - Fixture reusability
   - Test isolation

## Maintenance Guidelines

1. **Adding New Tests**
   - Follow existing patterns
   - Use appropriate fixtures
   - Include both success and failure cases

2. **Database Considerations**
   - Use transactions for isolation
   - Clean up test data
   - Handle PostgreSQL-specific features

3. **Code Quality**
   - Maintain test documentation
   - Use descriptive test names
   - Keep tests focused and atomic
