import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import timedelta
from unittest.mock import patch

from app.main import app
from app.db.base_model import Base
from app.db.base import get_db
from app.core.config import get_settings
from app.models.enums import SubscriptionTier
from app.services.auth import auth_service

from tests.utils.redis import MockRedis
from tests.utils.client import CustomTestClient

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(autouse=True)
def mock_redis_globally(monkeypatch):
    """Mock Redis globally for all tests"""
    mock_redis = MockRedis()
    
    # Mock Redis connection to prevent actual connection attempts
    class MockConnection:
        def __init__(self, *args, **kwargs):
            pass
        
        def connect(self):
            pass
        
        def disconnect(self):
            pass
        
        def send_command(self, *args, **kwargs):
            pass
    
    # Mock Redis connection pool
    class MockConnectionPool:
        def __init__(self, *args, **kwargs):
            pass
        
        def get_connection(self, *args, **kwargs):
            return MockConnection()
        
        def release(self, *args, **kwargs):
            pass
        
        def disconnect(self, *args, **kwargs):
            pass
    
    # Patch all Redis-related functionality
    monkeypatch.setattr("redis.Redis.from_url", lambda *args, **kwargs: mock_redis)
    monkeypatch.setattr("redis.Redis", lambda *args, **kwargs: mock_redis)
    monkeypatch.setattr("redis.connection.Connection", MockConnection)
    monkeypatch.setattr("redis.connection.ConnectionPool", MockConnectionPool)
    monkeypatch.setattr("redis.connection.UnixDomainSocketConnection", MockConnection)
    
    # Also patch the Redis instances in our app
    from app.core.rate_limit import rate_limiter
    from app.services.cache import RedisCache
    
    # Create a new instance of RedisCache with our mock Redis
    mock_cache = RedisCache()
    mock_cache.redis = mock_redis
    
    # Patch the rate limiter and cache instances
    rate_limiter.redis = mock_redis
    with patch("app.api.v1.endpoints.coins.cache", mock_cache):
        yield mock_redis

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Creates a new database session for each test function"""
    connection = db_engine.connect()
    transaction = connection.begin()
    
    # Create a session bound to the connection
    TestingSessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture
    
    # Override database URL for testing
    test_settings = get_settings()
    test_settings.SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URL
    
    app.dependency_overrides[get_db] = override_get_db
    with CustomTestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_settings():
    settings = get_settings()
    settings.SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URL
    settings.REDIS_URL = "redis://localhost:6379/0"  # Not used since we mock RedisCache
    return settings

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from app.models.user import User
    
    user = User(
        email="test@example.com",
        hashed_password=auth_service.get_password_hash("testpassword123"),
        is_active=True,
        subscription_tier=SubscriptionTier.FREE
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_user_token(test_user, test_settings):
    """Create a test token for authentication"""
    return auth_service.create_access_token(
        data={
            "sub": test_user.email,
            "subscription_tier": test_user.subscription_tier,
            "role": test_user.role
        },
        expires_delta=timedelta(minutes=30),
    )

@pytest.fixture
def authorized_client(client, test_user_token):
    """Create an authorized client with test token"""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_user_token}"
    }
    return client

@pytest.fixture
def test_premium_user(db_session):
    """Create a test premium user"""
    from app.models.user import User
    
    user = User(
        email="test@example.com",
        hashed_password=auth_service.get_password_hash("testpassword123"),
        is_active=True,
        subscription_tier=SubscriptionTier.PREMIUM
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_premium_user_token(test_premium_user, test_settings):
    """Create a test token for authentication"""
    return auth_service.create_access_token(
        data={
            "sub": test_premium_user.email,
            "subscription_tier": test_premium_user.subscription_tier,
            "role": test_premium_user.role
        },
        expires_delta=timedelta(minutes=30),
    )

@pytest.fixture
def premium_authorized_client(client, test_premium_user_token):
    """Create an authorized client with test token"""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_premium_user_token}"
    }
    return client