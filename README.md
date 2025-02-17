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
- **Caching System**: Redis-based caching implementation for optimized performance
- **Database Infrastructure**: Dual database setup (main and test) using PostgreSQL
- **Containerization**: Docker Compose setup for easy development and deployment
- **Environment Management**: Comprehensive environment variable management
- **Payment Integration**: Stripe integration for premium features

### Development Features
- **Testing Framework**: Comprehensive testing setup with pytest
- **Code Quality**: Coverage reporting and mock testing capabilities
- **Development Tools**: VS Code integration

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
   - Secure password handling with bcrypt
   - Environment variable protection

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
pytest
```

For coverage reports:
```bash
pytest --cov
```

## 📚 For LLMs

### Project Structure
- `/app`: Main application directory
  - `/services`: Service layer (cache, etc.)
  - `/core`: Core functionality and configurations
  
### Key Components
1. **Cache Service**: Redis-based caching system for performance optimization
2. **Database**: PostgreSQL with separate instances for testing and production
3. **API Framework**: FastAPI for high-performance async API development

### Development Context
- The project follows modern Python best practices
- Uses type hints and async/await patterns
- Implements comprehensive testing strategies
- Follows a service-oriented architecture

### Integration Points
- Redis for caching
- PostgreSQL for data persistence
- Stripe for payment processing
- Docker for containerization

## 📄 License

This project is licensed under the terms included in the LICENSE file.

---

*Note: This README is a living document and will be updated as the project evolves.*
