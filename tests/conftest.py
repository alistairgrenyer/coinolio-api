import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, UTC

from app.main import app
from app.db.base_model import Base
from app.db.base import get_db
from app.core.config import get_settings
from app.core.security import create_access_token

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_engine():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    return engine

@pytest.fixture
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    # Override database URL for testing
    test_settings = get_settings()
    test_settings.SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URL
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
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
def test_user(client, test_user_data):
    response = client.post(
        f"{get_settings().API_V1_STR}/auth/register",
        json=test_user_data
    )
    assert response.status_code == 200
    return response.json()

@pytest.fixture
def test_user_token(test_user, test_settings):
    access_token_expires = timedelta(minutes=test_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": test_user["email"]},
        expires_delta=access_token_expires
    )

@pytest.fixture
def authorized_client(client, test_user_token):
    client.headers["Authorization"] = f"Bearer {test_user_token}"
    return client
