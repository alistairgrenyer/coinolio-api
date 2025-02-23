from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.enums import SubscriptionTier
from app.models.user import RefreshToken, User, UserCreate, UserResponse
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserResponse]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get a user by email"""
        return db.query(User).filter(User.email == email).first()

    def get_by_id(self, db: Session, *, id: int) -> Optional[User]:
        """Get a user by ID"""
        return db.query(User).filter(User.id == id).first()
    
    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users with pagination"""
        return (
            db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_subscription_tier(
        self, db: Session, *, tier: SubscriptionTier, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Get users by subscription tier"""
        return (
            db.query(User)
            .filter(User.subscription_tier == tier)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_expired_subscriptions(self, db: Session) -> List[User]:
        """Get users with expired subscriptions"""
        now = datetime.now(timezone.utc)
        return (
            db.query(User)
            .filter(User.subscription_expires_at < now)
            .filter(User.subscription_tier != SubscriptionTier.FREE)
            .all()
        )

class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshToken, RefreshToken]):
    def get_by_token(self, db: Session, *, token: str) -> Optional[RefreshToken]:
        """Get a refresh token by token string"""
        return db.query(RefreshToken).filter(RefreshToken.token == token).first()
    
    def get_active_by_user(self, db: Session, *, user_id: int) -> List[RefreshToken]:
        """Get active refresh tokens for a user"""
        now = datetime.now(timezone.utc)
        return (
            db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at > now,
                RefreshToken.is_revoked == False
            )
            .all()
        )
    
    def revoke_all_for_user(self, db: Session, *, user_id: int) -> None:
        """Revoke all refresh tokens for a user"""
        (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .update({"is_revoked": True})
        )
        db.commit()

# Create repository instances
user_repository = UserRepository(User)
refresh_token_repository = RefreshTokenRepository(RefreshToken)
