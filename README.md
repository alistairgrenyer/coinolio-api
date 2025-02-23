# Coinolio API

A modern, scalable cryptocurrency portfolio tracking and analytics API built with FastAPI. Designed for robust portfolio management with cloud sync capabilities and premium features.

## 🚀 Technical Stack

- **Framework**: FastAPI + Python 3.12
- **Database**: PostgreSQL 15 + SQLAlchemy ORM
- **Caching**: Redis
- **Authentication**: JWT with Python-Jose
- **Testing**: Pytest + SQLite
- **Deployment**: Docker + Alembic
- **Payments**: Stripe (planned)

## 📁 Project Structure

```
app/
├── api/                    # API endpoints and routes
│   └── v1/
│       ├── auth.py        # Authentication endpoints (97% coverage)
│       ├── portfolios.py  # Portfolio management endpoints (93% coverage)
│       ├── coins.py       # CoinGecko cryptocurrency data endpoints (44% coverage)
│       └── subscriptions.py # Premium features and billing (37% coverage)
│
├── core/                   # Core functionality and configuration
│   ├── config.py          # Environment and app configuration (100% coverage)
│   ├── deps.py            # Dependency injection (74% coverage)
│   └── rate_limit.py      # Rate limiting implementation (48% coverage)
│
├── db/                     # Database configuration and utilities
│   ├── base.py            # SQLAlchemy base setup (69% coverage)
│   ├── base_class.py      # Base model class (89% coverage)
│   ├── base_model.py      # Shared model functionality (100% coverage)
│   └── custom_types.py    # Custom database types (77% coverage)
│
├── models/                 # SQLAlchemy database models
│   ├── portfolio.py       # Portfolio data model (81% coverage)
│   ├── user.py            # User account model (100% coverage)
│   └── enums.py          # Shared enumerations (100% coverage)
│
├── repositories/          # SQLAlchemy repositories
│   ├── base.py            # Base repository class (100% coverage)
│   ├── user.py            # User account repository (100% coverage)
│   └── portfolio.py       # Portfolio data repository (100% coverage)
│
├── schemas/               # Pydantic models for API validation
│   ├── portfolio.py      # Portfolio data validation (100% coverage)
│   └── portfolio_sync.py # Sync data validation and types (64% coverage)
│
├── services/             # Business logic and external services
│   ├── auth.py         # Authentication services (100% coverage)
│   ├── sync_manager.py  # Portfolio sync orchestration (87% coverage)
│   ├── cache.py        # Redis caching implementation (62% coverage)
│   └── coingecko.py    # CoinGecko API integration (41% coverage)
│
└── main.py              # FastAPI application setup (93% coverage)

tests/                   # Test suite
├── unit/               # Unit tests for all components
└── integration/        # Integration tests (planned)

docs/                   # Documentation
├── API_REFERENCE.md    # API endpoint documentation
├── auth_strategy.md    # Authentication implementation details
├── docker_strategy.md  # Docker deployment strategy
├── TESTING_STRATEGY.md # Testing approach and guidelines
├── portfolio_strategy.md # Portfolio management implementation details
└── sync_strategy.md    # Portfolio sync implementation details

## 🛠️ Implementation Status

### ✅ Core Features (90%+ Coverage)

1. **Authentication & Users** (97%)
   - [x] User registration and login
   - [x] JWT authentication with refresh
   - [x] Role-based access control
   - [x] Password security (bcrypt)
   - [x] Comprehensive test coverage

2. **Portfolio Management** (93%)
   - [x] CRUD operations
   - [x] Version history tracking
   - [x] Cloud sync (Premium)
   - [x] Asset validation
   - [x] Subscription tier checks
   - [x] Sync manager implementation (87% coverage)

3. **Infrastructure** (100%)
   - [x] Database models and schemas
   - [x] Environment configuration
   - [x] Test framework
   - [x] Docker setup
   - [x] Migration system
   - [x] CORS configuration for mobile app

### 🚧 In Development

1. **External Services** (41% Complete)
   - [ ] CoinGecko integration
   - [ ] Market data fetching
   - [ ] Price updates
   - [ ] Integration tests
   - ETA: March 2025

2. **Subscription System** (37% Complete)
   - [ ] Payment processing
   - [ ] Tier management
   - [ ] Premium features
   - [ ] Billing tests
   - ETA: April 2025

3. **Performance Features** (55% Complete)
   - [ ] Rate limiting (48%)
   - [ ] Redis caching (62%)
   - [ ] Load optimization
   - [ ] Performance tests
   - ETA: May 2025

### 📋 Upcoming Features

1. **Q2 2025**
   - Portfolio analytics engine
   - Advanced metrics
   - Custom reporting
   - Data visualization

2. **Q3 2025**
   - Mobile API optimization
   - Push notifications
   - Offline sync
   - Real-time updates

3. **Q4 2025**
   - Two-factor auth
   - API key management
   - Security audit system
   - Advanced monitoring

## 🔍 Current Status

### Test Coverage
```plaintext
Component                    Stmts   Miss  Cover
-----------------------------------------------------------
Auth Endpoints                 71      2    97%
Portfolio Endpoints            68      5    93%
Sync Manager                  91     12    87%
Core & Config                122     23    81%
Models & Schemas             287     67    77%
External Services (CoinGecko)  32     19    41%
Subscription System           73     46    37%
Rate Limiting                 25     13    48%
-----------------------------------------------------------
TOTAL                        879    220    75%
```

### Known Issues
1. **High Priority**
   - Rate limiting implementation (48% complete)
   - Redis caching optimization needed (62% coverage)
   - Mobile sync conflict resolution edge cases
   - Core dependencies need updating (Pydantic v2, SQLAlchemy v2 warnings)

2. **Medium Priority**
   - CoinGecko API integration (41% complete)
   - Subscription system implementation (37% complete)
   - Performance monitoring setup needed
   - API documentation updates required

## 🔧 Quick Start

1. Clone and setup:
```bash
git clone https://github.com/yourusername/coinolio-api.git
cd coinolio-api
cp .env.example .env
```

2. Configure environment:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/coinolio
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
```

3. Run with Docker:
```bash
docker-compose up -d
docker-compose exec api alembic upgrade head
```

## 🧪 Testing

```bash
# Full test suite
pytest

# Specific components
pytest tests/unit/api/v1/endpoints/test_auth.py
pytest tests/unit/api/v1/endpoints/test_portfolios.py

# Coverage report
pytest --cov=app tests/
```

## 📚 Documentation
- [API Reference](docs/API_REFERENCE.md)
- [Testing Strategy](docs/TESTING_STRATEGY.md)

## 📈 Development Priorities

### Immediate (1-2 weeks)
1. Complete sync manager test coverage (87% → 90%)
2. Complete basic rate limiting
3. Implement Redis caching foundation

### Short Term (1-2 months)
1. Finish CoinGecko integration
2. Launch subscription system
3. Add portfolio analytics

### Medium Term (3-6 months)
1. Mobile API optimization
2. Advanced security features
3. Performance monitoring

## 📄 License
This project is licensed under the terms included in the LICENSE file.

---
Last updated: 2025-02-18
