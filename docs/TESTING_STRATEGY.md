# Testing Strategy

## Overview
Testing strategy for Coinolio API, focusing on FastAPI endpoint testing and maintainability.

## Test Structure
```plaintext
tests/
├── conftest.py          # Shared fixtures
├── factories/           # Test data factories
├── unit/               # Unit tests
│   └── api/v1/         # API endpoint tests
└── utils/              # Test utilities
```

## Key Components

### Database Strategy
- SQLite for testing (in-memory, fast)
- Custom JSON type for PostgreSQL compatibility
- Automatic schema creation per test

### Test Data
```python
class PortfolioFactory(factory.Factory):
    class Meta:
        model = Portfolio
    name = factory.Faker('company')
    data = factory.LazyFunction(lambda: {...})
```

### Common Fixtures
- `db_session`: Database session
- `client`: Test client
- `test_user`: Authenticated user
- `authorized_client`: Client with auth

## Test Coverage (76%)

### High Coverage (90%+)
- Authentication (97%)
- Portfolio Management (93%)
- Models & Schemas (95-100%)
- Core Config (100%)

### Needs Improvement
- Sync Manager (22%)
- External APIs (41%)
- Rate Limiting (48%)
- Subscription System (37%)

## Best Practices

### Database
- Transaction isolation
- In-memory for speed
- Clean state per test

### Organization
- Grouped by feature
- Clear naming
- Shared fixtures
- Isolated test data

### Error Handling
- Success/failure cases
- Status code validation
- Error message checks

## Running Tests
```bash
# All tests
pytest

# Specific features
pytest tests/unit/api/v1/endpoints/test_auth.py
pytest tests/unit/api/v1/endpoints/test_portfolios.py

# With coverage
pytest --cov=app tests/
```

## Next Steps
1. Improve sync manager coverage
2. Add subscription tests
3. Implement rate limit tests
4. Add integration tests
