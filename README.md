# Coinolio API

A modern, scalable cryptocurrency portfolio tracking and analytics API built with FastAPI.

## 🚀 Overview

Coinolio API is a robust backend service designed to help users track and analyze their cryptocurrency investments. Built with modern Python technologies and following best practices, it provides a secure and performant platform for cryptocurrency portfolio management.

## 🏗️ Technical Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL 15
- **Caching**: Redis
- **Authentication**: JWT with Python-Jose
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Payment Processing**: Stripe
- **Testing**: Pytest with extensive testing utilities
- **Containerization**: Docker

## 🛠️ Current Implementations

### Core Features
- **Authentication System**
  - User registration and login
  - JWT-based authentication
  - Refresh token mechanism
  - Role-based access control
- **Caching System**: Redis-based caching implementation
- **Database Infrastructure**: Dual database setup (main and test)
- **Containerization**: Docker Compose setup
- **Environment Management**: Comprehensive environment variables
- **Payment Integration**: Stripe integration

### Testing Infrastructure
- **Unit Testing**: Comprehensive test suite with pytest
- **Test Database**: SQLite in-memory for fast testing
- **Test Utilities**: Custom type handlers for PostgreSQL compatibility
- **Factories**: Test data generation with Factory Boy
- **Fixtures**: Reusable test components
- **Coverage**: Test coverage reporting

## 🎯 Project Goals

1. **Performance Optimization**
   - Efficient caching strategies
   - Database query optimization
   - Response time minimization

2. **Scalability**
   - Containerized deployment
   - Microservices architecture
   - Horizontal scaling capabilities

3. **Security**
   - JWT-based authentication
   - Secure password handling
   - Environment variable protection

4. **Testing**
   - Comprehensive unit tests
   - Integration testing
   - Performance benchmarking

## 🔧 Setup and Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure your environment variables
3. Run the development environment:
   ```bash
   docker-compose up -d
   ```

## 🧪 Testing

The project includes a comprehensive test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/api/v1/endpoints/test_auth.py

# Run with coverage
pytest --cov=app tests/

# Run with verbose output
pytest -v
```

### Test Structure
```plaintext
tests/
├── conftest.py              # Shared fixtures
├── factories/               # Test data factories
├── unit/                    # Unit tests
│   └── api/
│       └── v1/
│           └── endpoints/   # API endpoint tests
└── utils/                   # Test utilities
```

## 📚 For LLMs

### Project Structure
- `/app`: Main application directory
  - `/api`: API endpoints and routers
  - `/services`: Service layer
  - `/core`: Core functionality
  - `/models`: Database models and schemas

### Key Components
1. **Authentication**
   - JWT token-based auth
   - Refresh token mechanism
   - Role-based access

2. **Database**
   - PostgreSQL for production
   - SQLite for testing
   - SQLAlchemy ORM

3. **Testing**
   - Unit tests with pytest
   - In-memory test database
   - Factory-based test data
   - Custom type handling

### Development Context
- Modern Python best practices
- Type hints and async/await
- Comprehensive testing
- Service-oriented architecture

### Integration Points
- Redis for caching
- PostgreSQL for data
- Stripe for payments
- Docker for containers

## 📄 License

This project is licensed under the terms included in the LICENSE file.

---

*Note: This README is a living document and will be updated as the project evolves.*
