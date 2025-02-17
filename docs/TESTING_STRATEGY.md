# FastAPI Testing Strategy

## Overview

This document outlines our testing strategy for the Coinolio API, focusing on unit testing FastAPI endpoints while maintaining clean, maintainable tests.

## Implementation Status

### Completed
1. **Test Infrastructure**
   - SQLite in-memory database setup
   - Custom JSON type handling for SQLite compatibility
   - Test fixtures and factories
   - Database session management

2. **Authentication Tests**
   - User registration
   - Login functionality
   - Token refresh mechanism
   - Current user retrieval
   - Error handling scenarios

### Pending
1. **Additional Test Coverage**
   - Portfolio management endpoints
   - Subscription handling
   - Rate limiting
   - External API integration

## Test Structure

```plaintext
tests/
├── conftest.py              # Shared fixtures and DB setup
├── factories/               # Test data factories
│   └── user.py             # User factory implementation
├── unit/                   # Unit tests
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── test_auth.py  # Authentication tests
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
class UserFactory(factory.Factory):
    class Meta:
        model = User
    email = factory.Faker('email')
    hashed_password = factory.LazyFunction(lambda: get_password_hash("testpassword123"))
```

### 3. Fixtures
```python
@pytest.fixture
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4. Authentication Test Cases
1. **Registration**
   - Successful registration
   - Duplicate email handling
2. **Login**
   - Successful login
   - Invalid credentials
3. **Token Management**
   - Access token validation
   - Refresh token workflow
   - Token expiration

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
```

Running with coverage:
```bash
pytest --cov=app tests/
```

## Next Steps

1. **Expand Test Coverage**
   - Implement portfolio endpoint tests
   - Add subscription test cases
   - Test rate limiting functionality

2. **Performance Testing**
   - Add load test scenarios
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
