import pytest
from typing import Generator, Dict
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import jwt
from unittest.mock import MagicMock

from app.main import app
from app.core.config import get_settings
from app.models.user import User
from app.models.enums import UserRole, SubscriptionTier
from app.models.portfolio import Portfolio, PortfolioVersion
from app.db.base import get_db

settings = get_settings()

def get_mock_db():
    """Return a mocked database session"""
    mock_db = MagicMock()
    yield mock_db

@pytest.fixture(scope="function")
def client() -> Generator:
    """Test client with mocked database"""
    app.dependency_overrides[get_db] = get_mock_db
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_db():
    """Return a mocked database session"""
    return MagicMock()

@pytest.fixture
def normal_user() -> User:
    """Create a mock normal user"""
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_password",
        role=UserRole.USER,
        subscription_tier=SubscriptionTier.FREE
    )

@pytest.fixture
def premium_user() -> User:
    """Create a mock premium user"""
    return User(
        id=2,
        email="premium@example.com",
        hashed_password="hashed_password",
        role=UserRole.USER,
        subscription_tier=SubscriptionTier.PREMIUM,
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123"
    )

@pytest.fixture
def admin_user() -> User:
    """Create a mock admin user"""
    return User(
        id=3,
        email="admin@example.com",
        hashed_password="hashed_password",
        role=UserRole.ADMIN,
        subscription_tier=SubscriptionTier.PREMIUM
    )

def create_test_token(user: User) -> str:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@pytest.fixture
def normal_user_token(normal_user: User) -> str:
    return create_test_token(normal_user)

@pytest.fixture
def premium_user_token(premium_user: User) -> str:
    return create_test_token(premium_user)

@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_test_token(admin_user)

@pytest.fixture
def sample_portfolio_data() -> dict:
    """Sample portfolio data for testing"""
    return {
        "assets": {
            "bitcoin": {
                "amount": "1.5",
                "cost_basis": "45000.00",
                "notes": "Test BTC position",
                "last_modified": datetime.utcnow().isoformat(),
                "transactions": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": "buy",
                        "amount": "1.5",
                        "price_usd": "45000.00",
                        "notes": "Initial purchase"
                    }
                ]
            },
            "ethereum": {
                "amount": "10.0",
                "cost_basis": "3000.00",
                "notes": "Test ETH position",
                "last_modified": datetime.utcnow().isoformat(),
                "transactions": []
            }
        },
        "settings": {
            "preferred_currency": "usd",
            "notification_preferences": {},
            "display_preferences": {}
        },
        "metadata": {
            "last_modified_device": "test_device",
            "app_version": "1.0.0",
            "platform": "test"
        },
        "schema_version": "1.0.0"
    }

@pytest.fixture
def test_portfolio(normal_user: User, sample_portfolio_data: dict) -> Portfolio:
    """Create a mock test portfolio"""
    portfolio = Portfolio(
        id=1,
        name="Test Portfolio",
        description="Test description",
        user_id=normal_user.id,
        data=sample_portfolio_data,
        version=1,
        total_value_usd=100000.0,
        asset_count=2,
        is_cloud_synced=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    portfolio.user = normal_user
    normal_user.portfolios = [portfolio]
    return portfolio

@pytest.fixture
def premium_portfolio(premium_user: User, sample_portfolio_data: dict) -> Portfolio:
    """Create a mock premium portfolio"""
    portfolio = Portfolio(
        id=2,
        name="Premium Portfolio",
        description="Premium portfolio description",
        user_id=premium_user.id,
        data=sample_portfolio_data,
        version=1,
        total_value_usd=500000.0,
        asset_count=2,
        is_cloud_synced=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    portfolio.user = premium_user
    premium_user.portfolios = [portfolio]
    return portfolio

@pytest.fixture
def portfolio_version(test_portfolio: Portfolio) -> PortfolioVersion:
    """Create a mock portfolio version"""
    version = PortfolioVersion(
        id=1,
        portfolio_id=test_portfolio.id,
        version=1,
        data=test_portfolio.data,
        total_value_usd=test_portfolio.total_value_usd,
        asset_count=test_portfolio.asset_count,
        change_summary={"added": [], "removed": [], "modified": []},
        created_at=datetime.utcnow()
    )
    version.portfolio = test_portfolio
    test_portfolio.versions = [version]
    return version
