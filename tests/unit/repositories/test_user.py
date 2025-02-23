"""Test cases for the user repository"""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.enums import SubscriptionTier
from app.models.user import RefreshToken, User
from app.repositories.user import refresh_token_repository, user_repository
from app.services.auth import auth_service


@pytest.fixture
def test_users(db_session):
    """Create test users with different subscription tiers"""
    users = [
        User(
            email=f"test_{tier.value}@example.com",
            hashed_password=auth_service.get_password_hash("password"),
            subscription_tier=tier,
            is_active=True
        )
        for tier in [SubscriptionTier.FREE, SubscriptionTier.PREMIUM]
    ]
    # Add an inactive user
    users.append(
        User(
            email="inactive@example.com",
            hashed_password=auth_service.get_password_hash("password"),
            subscription_tier=SubscriptionTier.FREE,
            is_active=False
        )
    )
    for user in users:
        db_session.add(user)
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    return users

@pytest.fixture
def test_refresh_tokens(db_session, test_users):
    """Create test refresh tokens"""
    tokens = []
    now = datetime.now(timezone.utc)
    
    # Create active token
    active_token = RefreshToken(
        token="active_token",
        user_id=test_users[0].id,
        expires_at=now + timedelta(days=7),
        is_revoked=False
    )
    tokens.append(active_token)
    
    # Create expired token
    expired_token = RefreshToken(
        token="expired_token",
        user_id=test_users[0].id,
        expires_at=now - timedelta(days=1),
        is_revoked=False
    )
    tokens.append(expired_token)
    
    # Create revoked token
    revoked_token = RefreshToken(
        token="revoked_token",
        user_id=test_users[0].id,
        expires_at=now + timedelta(days=7),
        is_revoked=True
    )
    tokens.append(revoked_token)
    
    for token in tokens:
        db_session.add(token)
    db_session.commit()
    for token in tokens:
        db_session.refresh(token)
    return tokens

class TestUserRepository:
    """Test cases for UserRepository"""

    def test_get_by_email(self, test_users, db_session):
        """Test getting a user by email"""
        user = user_repository.get_by_email(db_session, email=test_users[0].email)
        assert user is not None
        assert user.email == test_users[0].email

    def test_get_by_email_not_found(self, db_session):
        """Test getting a non-existent user by email"""
        user = user_repository.get_by_email(db_session, email="nonexistent@example.com")
        assert user is None

    def test_get_by_id(self, test_users, db_session):
        """Test getting a user by ID"""
        user = user_repository.get_by_id(db_session, id=test_users[0].id)
        assert user is not None
        assert user.id == test_users[0].id

    def test_get_by_id_not_found(self, db_session):
        """Test getting a non-existent user by ID"""
        user = user_repository.get_by_id(db_session, id=999)
        assert user is None

    def test_get_active_users(self, test_users, db_session):
        """Test getting active users"""
        users = user_repository.get_active_users(db_session)
        assert len(users) == 2
        assert all(user.is_active for user in users)

    def test_get_by_subscription_tier(self, test_users, db_session):
        """Test getting users by subscription tier"""
        premium_users = user_repository.get_by_subscription_tier(
            db_session, tier=SubscriptionTier.PREMIUM
        )
        assert len(premium_users) == 1
        assert premium_users[0].subscription_tier == SubscriptionTier.PREMIUM

    def test_get_expired_subscriptions(self, db_session):
        """Test getting users with expired subscriptions"""
        # Create a user with expired subscription
        expired_user = User(
            email="expired@example.com",
            hashed_password=auth_service.get_password_hash("password"),
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        db_session.add(expired_user)
        db_session.commit()

        expired_users = user_repository.get_expired_subscriptions(db_session)
        assert len(expired_users) == 1
        assert expired_users[0].email == "expired@example.com"

class TestRefreshTokenRepository:
    """Test cases for RefreshTokenRepository"""

    def test_get_by_token(self, test_refresh_tokens, db_session):
        """Test getting a refresh token by token string"""
        token = refresh_token_repository.get_by_token(
            db_session, token="active_token"
        )
        assert token is not None
        assert token.token == "active_token"
        assert not token.is_revoked

    def test_get_by_token_not_found(self, db_session):
        """Test getting a non-existent refresh token"""
        token = refresh_token_repository.get_by_token(
            db_session, token="nonexistent_token"
        )
        assert token is None

    def test_get_active_by_user(self, test_refresh_tokens, test_users, db_session):
        """Test getting active refresh tokens for a user"""
        tokens = refresh_token_repository.get_active_by_user(
            db_session, user_id=test_users[0].id
        )
        assert len(tokens) == 1
        assert tokens[0].token == "active_token"

    def test_revoke_all_for_user(self, test_refresh_tokens, test_users, db_session):
        """Test revoking all refresh tokens for a user"""
        refresh_token_repository.revoke_all_for_user(
            db_session, user_id=test_users[0].id
        )
        
        # Check that all tokens are revoked
        tokens = db_session.query(RefreshToken).filter(
            RefreshToken.user_id == test_users[0].id
        ).all()
        assert all(token.is_revoked for token in tokens)
