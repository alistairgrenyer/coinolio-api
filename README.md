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

3. **Infrastructure** (100%)
   - [x] Database models and schemas
   - [x] Environment configuration
   - [x] Test framework
   - [x] Docker setup
   - [x] Migration system

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
--------------------------------------------------
Core (Auth, Portfolio)        400     20    95%
Models & Config              200      0   100%
External Services            150     90    40%
Performance Features         100     45    55%
--------------------------------------------------
TOTAL                        850    155    76%
```

### Known Issues
1. **High Priority**
   - Sync manager coverage (22%)
   - Rate limiting incomplete
   - Caching optimization needed

2. **Medium Priority**
   - External API integration gaps
   - Subscription system incomplete
   - Performance monitoring needed

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
1. Improve sync manager test coverage (22% → 90%)
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
