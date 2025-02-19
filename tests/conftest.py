import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, UTC

from app.main import app
from app.db.base_model import Base
from app.db.base import get_db
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash
from app.core.json import json_dumps

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

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

class CustomTestClient(TestClient):
    def post(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['content'] = json_dumps(kwargs.pop('json')).encode('utf-8')
            kwargs['headers'] = {**kwargs.get('headers', {}), 'Content-Type': 'application/json'}
        return super().post(*args, **kwargs)

    def put(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['content'] = json_dumps(kwargs.pop('json')).encode('utf-8')
            kwargs['headers'] = {**kwargs.get('headers', {}), 'Content-Type': 'application/json'}
        return super().put(*args, **kwargs)

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
    from app.models.enums import SubscriptionTier
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
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
    return create_access_token(
        data={"sub": test_user.email},
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
