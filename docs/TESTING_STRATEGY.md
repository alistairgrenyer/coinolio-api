# FastAPI Testing Strategy

## Overview

This document outlines our testing strategy for the Coinolio API, focusing on unit testing FastAPI endpoints while maintaining clean, maintainable tests.

## Testing Philosophy

1. **Unit Tests First**: Focus on testing business logic in isolation
2. **Mock External Dependencies**: Avoid actual HTTP/DB calls during unit tests
3. **Clean Test Structure**: Use fixtures and factories for test data
4. **Coverage Focused**: Aim for high coverage of business logic
5. **End-to-End Separate**: Keep E2E tests (Postman, etc.) separate from unit tests

## Test Structure

```plaintext
tests/
├── conftest.py              # Shared fixtures
├── factories/               # Test data factories
│   ├── user.py
│   └── coin.py
├── unit/                    # Unit tests
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── test_coins.py
│   ├── services/
│   │   └── test_coingecko.py
│   └── core/
│       └── test_deps.py
└── utils/                   # Test utilities
    └── mock_responses.py
```

## Testing Approach

### 1. FastAPI TestClient

- Use FastAPI's `TestClient` for endpoint testing
- No need for actual server - TestClient simulates HTTP requests
- Example:
  ```python
  from fastapi.testclient import TestClient
  from app.main import app

  client = TestClient(app)
  ```

### 2. Mocking Strategy

#### Dependencies to Mock:
1. **Database Sessions**: Use SQLAlchemy's `create_engine` with SQLite
2. **External Services**: Mock CoinGecko API responses
3. **Redis Cache**: Mock cache operations
4. **Authentication**: Mock user context
5. **Rate Limiting**: Mock rate limit checks

#### Example Mock Setup:
```python
@pytest.fixture
def mock_coingecko():
    with patch("app.services.coingecko.CoinGeckoService") as mock:
        yield mock

@pytest.fixture
def mock_cache():
    with patch("app.services.cache.RedisCache") as mock:
        yield mock
```

### 3. Test Data Management

Use FactoryBoy for test data generation:
```python
class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n)
    email = factory.Faker('email')
    subscription_tier = SubscriptionTier.FREE
```

### 4. Testing Endpoints

Test Structure for Endpoints:
1. Happy path
2. Input validation
3. Authentication/Authorization
4. Rate limiting
5. Caching behavior
6. Error handling

Example Test Cases:
```python
async def test_get_coin_prices_success(mock_coingecko, mock_cache):
    # Arrange
    mock_cache.get.return_value = None
    mock_coingecko.get_coins_markets.return_value = {...}
    
    # Act
    response = client.get("/api/v1/coins/prices?ids=bitcoin")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {...}
```

## Key Testing Decisions

1. **No Real Database**
   - Use SQLite in-memory for unit tests
   - Faster execution
   - No need for test database setup

2. **No Real HTTP Calls**
   - Mock external service responses
   - Predictable test behavior
   - Faster execution

3. **No Real Redis**
   - Mock cache operations
   - Focus on caching logic, not Redis implementation

4. **Async Testing**
   - Use `pytest-asyncio` for async endpoint testing
   - Test both sync and async code paths

## Test Coverage Strategy

1. **Unit Test Coverage Targets**
   - Business Logic: 90%+
   - API Endpoints: 85%+
   - Utility Functions: 80%+

2. **What to Test**
   - Input validation
   - Business logic
   - Error handling
   - Cache hit/miss scenarios
   - Authorization rules
   - Rate limiting logic

3. **What Not to Test**
   - Framework internals
   - Third-party libraries
   - Configuration loading
   - Actual HTTP/DB operations

## Action Plan

1. **Setup Phase**
   - [ ] Configure pytest with necessary plugins
   - [ ] Set up test directory structure
   - [ ] Create base fixtures in conftest.py
   - [ ] Set up mock factories

2. **Implementation Phase**
   - [ ] Create mock utilities
   - [ ] Implement database fixtures
   - [ ] Create service mocks
   - [ ] Write first endpoint tests

3. **Coverage Phase**
   - [ ] Set up coverage reporting
   - [ ] Identify coverage gaps
   - [ ] Add missing test cases

4. **Maintenance Phase**
   - [ ] Document testing patterns
   - [ ] Create test templates
   - [ ] Set up CI test automation

## Best Practices

1. **Test Isolation**
   - Each test should be independent
   - Use fresh fixtures for each test
   - Clean up any test data

2. **Naming Conventions**
   - test_[feature]_[scenario]_[expected_result]
   - Example: `test_get_coin_prices_cache_hit_returns_cached_data`

3. **Assertion Best Practices**
   - One logical assertion per test
   - Use descriptive assertion messages
   - Test both positive and negative cases

4. **Mock Usage**
   - Mock at the lowest possible level
   - Use spec=True for type checking
   - Reset mocks between tests

## Next Steps

1. Begin with setting up the test environment and dependencies
2. Create basic fixtures and mock utilities
3. Start with simple endpoint tests
4. Gradually expand test coverage
5. Implement CI/CD integration

Remember: The goal is to have reliable, maintainable tests that give us confidence in our code without being overly complex or brittle.
